# from google.oauth2 import service_account
from google.auth import default as google_auth_default
from googleapiclient.discovery import build
import time

import json
from pprint import pprint as print


class GCPComputeManager:
    REQUIRED_APIS = ["compute.googleapis.com"]

    def __init__(self, project_id: str, zone: str, service_account_file: str = None):
        self.project_id = project_id
        self.zone = zone

        # TODO: Implement service account auth
        # credentials = service_account.Credentials.from_service_account_file(
        #     service_account_file,
        #     scopes=["https://www.googleapis.com/auth/cloud-platform"],
        # )
        credentials, _ = google_auth_default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        self.compute = build("compute", "v1", credentials=credentials)
        self.serviceusage = build("serviceusage", "v1", credentials=credentials)

    def create_instance(
        self,
        instance_name: str,
        machine_type: str = None,
        disk_size: int = None,
        instance_user: str = None,
        zone: str = None,
        use_custom_image: bool = False,
        custom_image_name: str = None,
        image_project: str = "ubuntu-os-cloud",
        image_family: str = "ubuntu-2204-lts",
    ):
        target_zone = zone or self.zone

        if use_custom_image:
            # Full custom image resource path (assumed to be in your project)
            source_image = (
                f"projects/{self.project_id}/global/images/{custom_image_name}"
            )
        else:
            # Public image from family
            source_image = (
                f"projects/{image_project}/global/images/family/{image_family}"
            )

        with open("scripts/startup_ansible.sh") as f:
            startup_script_template = f.read()

        startup_script = startup_script_template.format(instance_user=instance_user)

        config = {
            "name": instance_name,
            "machineType": f"zones/{target_zone}/machineTypes/{machine_type}",
            "disks": [
                {
                    "boot": True,
                    "autoDelete": True,
                    "initializeParams": {
                        "sourceImage": source_image,
                        "diskSizeGb": disk_size,
                        "diskType": f"zones/{target_zone}/diskTypes/pd-balanced",
                    },
                }
            ],
            "networkInterfaces": [
                {
                    "network": "global/networks/default",
                    "accessConfigs": [
                        {
                            "type": "ONE_TO_ONE_NAT",
                            "name": "External NAT",
                            "networkTier": "STANDARD",
                        }
                    ],
                }
            ],
            "metadata": {"items": [{"key": "startup-script", "value": startup_script}]},
        }

        return (
            self.compute.instances()
            .insert(project=self.project_id, zone=target_zone, body=config)
            .execute()
        )

    def start_instance(self, instance_name: str, zone: str = None):
        target_zone = zone or self.zone
        return (
            self.compute.instances()
            .start(project=self.project_id, zone=target_zone, instance=instance_name)
            .execute()
        )

    def stop_instance(self, instance_name: str, zone: str = None):
        target_zone = zone or self.zone
        return (
            self.compute.instances()
            .stop(project=self.project_id, zone=target_zone, instance=instance_name)
            .execute()
        )

    def delete_instance(self, instance_name: str, zone: str = None):
        target_zone = zone or self.zone

        return (
            self.compute.instances()
            .delete(project=self.project_id, zone=target_zone, instance=instance_name)
            .execute()
        )

    def create_image_from_instance(
        self,
        instance_name: str,
        image_name: str,
        zone: str = None,
        family: str = None,
    ):
        target_zone = zone or self.zone

        instance = (
            self.compute.instances()
            .get(project=self.project_id, zone=target_zone, instance=instance_name)
            .execute()
        )
        print(instance)
        boot_disk = next(
            d["source"].split("/")[-1] for d in instance["disks"] if d["boot"]
        )

        # TODO: add timestamp to image name
        image_body = {
            "name": image_name,
            "sourceDisk": f"projects/{self.project_id}/zones/{target_zone}/disks/{boot_disk}",
        }

        if family:
            image_body["family"] = family

        return (
            self.compute.images()
            .insert(project=self.project_id, body=image_body)
            .execute()
        )

    def delete_image(self, image_name: str):
        return (
            self.compute.images()
            .delete(project=self.project_id, image=image_name)
            .execute()
        )

    def list_instances(self):
        result = (
            self.compute.instances()
            .list(project=self.project_id, zone=self.zone)
            .execute()
        )

        return result.get("items", [])

    def list_images(self, family: str = None):
        result = self.compute.images().list(project=self.project_id).execute()
        images = result.get("items", [])

        if family:
            images = [img for img in images if img.get("family") == family]

        return images

    def get_latest_image_from_family(self, family: str):
        return (
            self.compute.images()
            .getFromFamily(project=self.project_id, family=family)
            .execute()
        )

    def check_required_apis(self):
        enabled_services = []
        request = self.serviceusage.services().list(
            parent=f"projects/{self.project_id}",
            filter="state:ENABLED",
        )

        while request is not None:
            response = request.execute()
            for service in response.get("services", []):
                enabled_services.append(service["config"]["name"])
            request = self.serviceusage.services().list_next(
                previous_request=request, previous_response=response
            )

        missing = [api for api in self.REQUIRED_APIS if api not in enabled_services]
        return {
            "enabled": [api for api in self.REQUIRED_APIS if api in enabled_services],
            "missing": missing,
        }

    def wait_for_operation(
        self,
        operation_name: str,
        scope: str = "zone",
        zone: str = None,
        timeout: int = 300,
        poll_interval: int = 5,
    ):
        """
        Polls a Compute Engine operation until it completes.
        Supports both 'zone' and 'global' operations.

        Args:
            operation_name (str): The name of the operation to poll.
            scope (str): 'zone' (default) or 'global'.
            zone (str): Required if scope == 'zone'.
            timeout (int): Timeout in seconds.
            poll_interval (int): Poll interval in seconds.

        Returns:
            dict: {'success': True/False, 'operation': ..., 'error': ... (if any)}
        """
        start_time = time.time()

        while True:
            if scope == "zone":
                target_zone = zone or self.zone

                request = self.compute.zoneOperations().get(
                    project=self.project_id,
                    zone=target_zone,
                    operation=operation_name,
                )
            elif scope == "global":
                request = self.compute.globalOperations().get(
                    project=self.project_id,
                    operation=operation_name,
                )
            else:
                raise ValueError(
                    "Unsupported operation scope: must be 'zone' or 'global'."
                )

            result = request.execute()
            # print(result.get("status"))
            print(result)
            if result.get("status") == "DONE":
                if "error" in result:
                    return {
                        "success": False,
                        "error": result["error"],
                        "operation": result,
                    }
                return {
                    "success": True,
                    "operation": result,
                }
            if time.time() - start_time > timeout:
                raise TimeoutError(
                    f"Operation {operation_name} timed out after {timeout} seconds"
                )

            time.sleep(poll_interval)


if __name__ == "__main__":
    zone = "europe-north1-a"
    instance_name = "vmlc-test"

    manager = GCPComputeManager(
        project_id="wagon-de",
        zone=zone,
    )

    ### Create Instance

    # op = manager.create_instance(
    #     instance_name=instance_name,
    #     machine_type="e2-standard-4",
    #     disk_size=80,
    #     instance_user="lscr",
    #     # zone=zone,
    #     use_custom_image=False,
    #     custom_image_name=None,
    #     image_project="ubuntu-os-cloud",
    #     image_family="ubuntu-2204-lts",
    # )

    ### Stop Instance

    # op = manager.stop_instance(
    #     instance_name=instance_name,
    #     zone=zone,
    # )

    ### Start Instance

    # op = manager.start_instance(
    #     instance_name=instance_name,
    #     zone=zone,
    # )

    ### Delete Instance

    op = manager.delete_instance(
        instance_name=instance_name,
    )

    result = manager.wait_for_operation(op["name"], scope="zone", zone=zone)

    ### List Instances

    # result = manager.list_instances()

    # with open("instance-list-output.json", "w") as f:
    #     json.dump(result, f)

    # print(result)

    ### Create Image from Instance

    # op = manager.create_image_from_instance(
    #     instance_name=instance_name,
    #     image_name=f"{instance_name}-image",
    #     family=f"{instance_name}-image",
    #     zone=zone,
    # )

    # result = manager.wait_for_operation(op["name"], scope="global", zone=zone)

    ### List Images

    # result = manager.list_images(family=f"{instance_name}-image")

    # print(result)

    ### Get latest image from family

    # result = manager.get_latest_image_from_family(family=f"{instance_name}-image")

    # print(result)

    ### Delete image

    # op = manager.delete_image("vmlc-test-image")

    # result = manager.wait_for_operation(op["name"], scope="global", zone=zone)
