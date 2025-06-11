import click
from googleapiclient.errors import HttpError

# from vm_lifecycle.config_manager import ConfigManager
# from vm_lifecycle.compute_manager import GCPComputeManager
from vm_lifecycle.utils import poll_with_spinner, init_gcp_context


@click.command(name="start")
@click.option(
    "-z", "--zone", help="GCP Zone override. Updates 'zone' for current profile."
)
def start_vm_instance(zone):
    config_manager, compute_manager, active_zone = init_gcp_context(zone_override=zone)
    if not config_manager:
        return

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

    # Start instance if exists and not different zone
    if instance_exists and active_zone == config_manager.active_profile["zone"]:
        spinner_text = f"Instance: '{config_manager.active_profile["instance_name"]}' exists. Starting..."
        op = compute_manager.start_instance(
            instance_name=config_manager.active_profile["instance_name"],
            zone=config_manager.active_profile["zone"],
        )

    # Create image from existing stopped instance, create new VM from image in new zone
    elif instance_exists and active_zone != config_manager.active_profile["zone"]:
        pass

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

    result = poll_with_spinner(
        compute_manager=compute_manager,
        op_name=op["name"],
        text=spinner_text,
        done_text=done_text,
        scope="zone",
        zone=active_zone,
    )

    if config_manager.update_active_zone_region(result["success"], zone=active_zone):
        click.echo(
            f"✅ Updated zone in profile: '{config_manager.active}' to '{active_zone}'"
        )
