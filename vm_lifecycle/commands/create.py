import click
from vm_lifecycle.config_manager import ConfigManager
from vm_lifecycle.compute_manager import GCPComputeManager
from vm_lifecycle.utils import poll_with_spinner


@click.command(name="create")
@click.option("-i", "--image", help="Name of a custom VM Image to use")
@click.option("-s", "--startup-script", help="Name of a custom startup script")
@click.option("-z", "--zone", help="GCP Zone override")
def create_vm_instance(image, startup_script, zone):
    # Load Profile
    config_manager = ConfigManager()

    profile_check = config_manager.pre_run_profile_check()
    if not profile_check:
        click.echo("Error with active profile. Ensure a profile has been created.")
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

    # Check existing instances with this profile already exist
    existing_instances = compute_manager.list_instances()

    if existing_instances:
        for instance in existing_instances:
            if instance["name"] == config_manager.active_profile["instance_name"]:
                click.echo(
                    f"❗ GCP Compute Engine instance with name: '{config_manager.active_profile['instance_name']}' in zone '{config_manager.active_profile['zone']}' already exists. Start or connect to the instance"
                )
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

    poll_with_spinner(
        compute_manager=compute_manager,
        op_name=op["name"],
        text=spinner_text,
        done_text=done_text,
        scope="zone",
    )
