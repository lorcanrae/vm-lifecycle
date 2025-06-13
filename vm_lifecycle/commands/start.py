import click
from googleapiclient.errors import HttpError
import sys

from vm_lifecycle.gcp_helpers import poll_with_spinner, init_gcp_context


@click.command(name="start")
@click.option(
    "-z", "--zone", help="GCP Zone override. Updates 'zone' for current profile."
)
def start_vm_instance(zone):
    """Start a GCP VM instance from profile"""
    config_manager, compute_manager, active_zone = init_gcp_context(zone_override=zone)

    if not config_manager:
        return

    # Check if instance exists
    existing_instances = compute_manager.list_instances(
        zone=config_manager.active_profile["zone"]
    )
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

    # Start instance if exists and not different zone
    if instance_exists and active_zone == config_manager.active_profile["zone"]:
        spinner_text = f"Instance: '{config_manager.active_profile["instance_name"]}' exists. Starting Instance."
        op = compute_manager.start_instance(
            instance_name=config_manager.active_profile["instance_name"],
            zone=config_manager.active_profile["zone"],
        )
    # Create image from existing stopped instance, create new VM from image in new zone
    elif instance_exists and active_zone != config_manager.active_profile["zone"]:
        # Create image from stopped instance
        op = compute_manager.create_image_from_instance(
            instance_name=config_manager.active_profile["instance_name"],
            image_name=config_manager.active_profile["image_base_name"],
            family=config_manager.active_profile["image_base_name"],
            zone=config_manager.active_profile["zone"],
        )
        spinner_text = f"Creating image from instance: '{config_manager.active_profile['instance_name']}'"
        # image_name = op["targetLink"].split("/")[-1]
        # done_text = f"✅ Image: '{image_name}' created from instance: '{config_manager.active_profile['instance_name']}'"
        result = poll_with_spinner(
            compute_manager=compute_manager,
            op_name=op["name"],
            text=spinner_text,
            done_text=None,
            scope="global",
        )

        if not result["success"]:
            click.echo(f"❌ Failed to create image: {result['error']['message']}")
            sys.exit(1)

        target_link = result.get("operation", {}).get("targetLink")
        if not target_link:
            click.echo("❌ Image creation did not return a targetLink.")
            sys.exit(1)

        image_name = target_link.split("/")[-1]
        done_text = f"✅ Image: '{image_name}' created from instance: '{config_manager.active_profile['instance_name']}'"
        click.echo(done_text)

        # Destroy redundant instance
        op = compute_manager.delete_instance(
            instance_name=config_manager.active_profile["instance_name"],
            zone=config_manager.active_profile["zone"],
        )

        spinner_text = f"Destroying VM instance: {config_manager.active_profile['instance_name']} in zone: '{config_manager.active_profile['zone']}'"
        done_text = f"🗑️  VM instance: '{config_manager.active_profile['instance_name']}' in zone: '{active_zone}' destroyed."

        poll_with_spinner(
            compute_manager=compute_manager,
            op_name=op["name"],
            text=spinner_text,
            done_text=done_text,
            scope="zone",
            zone=config_manager.active_profile["zone"],
        )

        # Set flag to create from image
        instance_exists = False

    # Get latest image
    if not instance_exists:
        try:
            latest_image = compute_manager.get_latest_image_from_family(
                family=config_manager.active_profile["image_base_name"]
            )
            if not latest_image:
                click.echo(
                    f"❌ No image found for family: '{config_manager.active_profile['image_base_name']}'"
                )
                sys.exit(1)
        except HttpError as e:
            click.echo(f"❗ Error: {e}")
            sys.exit(1)

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

    if not result["success"]:
        click.echo(f"❌ Failed to start instance: {result['error']['message']}")
        sys.exit(1)

    if config_manager.update_active_zone_region(result["success"], zone=active_zone):
        click.echo(
            f"✅ Updated zone in profile: '{config_manager.active}' to '{active_zone}'"
        )
