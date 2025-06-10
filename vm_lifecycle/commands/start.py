import click
from googleapiclient.errors import HttpError

from vm_lifecycle.config_manager import ConfigManager
from vm_lifecycle.compute_manager import GCPComputeManager
from vm_lifecycle.utils import poll_with_spinner


@click.command(name="start")
@click.option("-z", "--zone", help="GCP Zone override")
def start_vm_instance(zone):
    # Load Profile
    config_manager = ConfigManager()

    profile_check = config_manager.pre_run_profile_check()
    if not profile_check:
        click.echo("❗ Error with active profile. Ensure a profile has been created.")
        return

    active_zone = zone or config_manager.active_profile["zone"]

    compute_manager = GCPComputeManager(
        config_manager.active_profile["project_id"],
        active_zone,
    )

    # GCP API Check
    if not config_manager.active_profile["api_cache"]:
        apis = compute_manager.check_required_apis()
        if apis["missing"]:
            click.echo("❗ The following GCP API's have not been enabled:")
            for api in apis["missing"]:
                click.echo(f"\t{api}")
            return
        config_manager.config[config_manager.active]["api_cache"] = True
        config_manager.save_config()

    # Check if instance exists
    existing_instances = compute_manager.list_instances()
    instance_exists = False
    if existing_instances:
        for instance in existing_instances:
            if (
                instance["name"] == config_manager.active_profile["instance_name"]
                and instance["status"] == "RUNNING"
            ):
                click.echo(
                    f"❗ Instance: '{config_manager.active_profile["instance_name"]}' is already running."
                )
                return
            elif (
                instance["name"] == config_manager.active_profile["instance_name"]
                and instance["status"] == "TERMINATED"
            ):
                instance_exists = True

    # Get latest image
    if not instance_exists:
        try:
            latest_image = compute_manager.get_latest_image_from_family(
                family=config_manager.active_profile["image_base_name"]
            )
        except HttpError as e:
            click.echo(f"❗ Error: {e}")
            return

    # Start instance if exists
    if instance_exists:
        spinner_text = f"Instance: '{config_manager.active_profile["instance_name"]}' exists. Starting..."
        click.echo("Instance exists: starting...")
        op = compute_manager.start_instance(
            instance_name=config_manager.active_profile["instance_name"],
            zone=config_manager.active_profile["zone"],
        )

    # Create instance from image
    if not instance_exists and latest_image:
        spinner_text = f"Creating instance from image: '{latest_image['name']}'"
        op = compute_manager.create_instance(
            instance_name=config_manager.active_profile["instance_name"],
            machine_type=config_manager.active_profile["machine_type"],
            disk_size=config_manager.active_profile["disk_size"],
            instance_user=config_manager.active_profile["instance_user"],
            zone=active_zone,
            custom_image_name=latest_image["name"],
        )

    done_text = f"✅ Instance: '{config_manager.active_profile['instance_name']}' created in zone: '{active_zone}'"

    poll_with_spinner(
        compute_manager=compute_manager,
        op_name=op["name"],
        text=spinner_text,
        done_text=done_text,
        scope="zone",
    )
