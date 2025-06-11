import click

from vm_lifecycle.utils import poll_with_spinner, init_gcp_context


@click.command(name="create")
@click.option("-i", "--image", help="Name of a custom VM Image to use")
@click.option("-s", "--startup-script", help="Name of a custom startup script")
@click.option("-z", "--zone", help="GCP Zone override")
def create_vm_instance(image, startup_script, zone):
    config_manager, compute_manager, active_zone = init_gcp_context(zone_override=zone)
    if not config_manager:
        return

    # Check existing instances with this profile already exist
    existing_instances = compute_manager.list_instances()

    if existing_instances:
        for instance in existing_instances:
            if instance["name"] == config_manager.active_profile["instance_name"]:
                click.echo(
                    f"❗ GCP Compute Engine instance with name: '{config_manager.active_profile['instance_name']}' in zone '{active_zone}' already exists. Start or connect to the instance"
                )
                return

    # Check if image corresponding to this profile exists
    images = compute_manager.list_images(
        family=config_manager.active_profile["image_base_name"]
    )
    num_images = len(images)

    if images:
        if not click.prompt(
            f"❓ {num_images} image{'s' if num_images > 1 else ''} for instance: '{config_manager.active_profile['instance_name']}'. Are you sure you want to create a new instance?",
            default=False,
        ):
            click.echo("❌ Aborted.")
            return

    # Create instance
    op = compute_manager.create_instance(
        instance_name=config_manager.active_profile["instance_name"],
        machine_type=config_manager.active_profile["machine_type"],
        disk_size=config_manager.active_profile["disk_size"],
        instance_user=config_manager.active_profile["instance_user"],
        zone=active_zone,
        custom_image_name=None,
        image_project="ubuntu-os-cloud" if not image else None,
        image_family="ubuntu-2204-lts" if not image else None,
        startup_script_type=startup_script or None,
    )

    # Works
    # TODO: Add logic if creation fails
    # Opts: zone_out_of_resources, quota

    spinner_text = f"Creating instance: '{config_manager.active_profile['instance_name']}' in zone: '{active_zone}'"
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
