import click

from vm_lifecycle.config_manager import ConfigManager
from vm_lifecycle.compute_manager import GCPComputeManager
from vm_lifecycle.utils import poll_with_spinner


@click.command(name="stop")
@click.option("-k", "--keep", is_flag=True, help="Do not delete the instance.")
def stop_vm_instance(keep):
    # Load Profile
    config_manager = ConfigManager()

    profile_check = config_manager.pre_run_profile_check()
    if not profile_check:
        click.echo("Error with active profile. Ensure a profile has been created.")
        return

    active_zone = config_manager.active_profile["zone"]

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
    instance_running = False

    if existing_instances:
        for instance in existing_instances:
            if (
                instance["name"] == config_manager.active_profile["instance_name"]
                and instance["status"] == "RUNNING"
            ):
                instance_exists = True
                instance_running = True
                break
            elif (
                instance["name"] == config_manager.active_profile["instance_name"]
                and instance["status"] == "TERMINATED"
            ):
                instance_exists = True
                instance_running = False
                break

    # Stop the instance if it's running
    if instance_exists and instance_running:
        # Shutdown instance
        op = compute_manager.stop_instance(
            instance_name=config_manager.active_profile["instance_name"]
        )

        spinner_text = (
            f"Stopping instance: '{config_manager.active_profile['instance_name']}'"
        )
        done_text = (
            f"✅ Instance: '{config_manager.active_profile["instance_name"]}' stopped"
        )

        # TODO: add spinner
        poll_with_spinner(
            compute_manager=compute_manager,
            op_name=op["name"],
            text=spinner_text,
            done_text=done_text,
            scope="zone",
        )

    elif not instance_running and not instance_exists:
        click.echo(
            f"❗ No instance named: '{config_manager.active_profile['instance_name']}' found"
        )
    elif instance_exists and not instance_running:
        pass
    elif not instance_exists and instance_running:
        # Unreachable
        pass

    # Create an image from the stopped instance
    op = compute_manager.create_image_from_instance(
        instance_name=config_manager.active_profile["instance_name"],
        image_name=config_manager.active_profile["image_base_name"],
        family=config_manager.active_profile["image_base_name"],
        zone=active_zone,
    )

    spinner_text = f"Creating image from instance: '{config_manager.active_profile['instance_name']}'"
    done_text = "✅ Image created!"
    poll_with_spinner(
        compute_manager=compute_manager,
        op_name=op["name"],
        text=spinner_text,
        done_text=done_text,
        scope="global",
    )

    # Delete dangling images
    dangling_images = compute_manager.get_dangling_images(
        family=config_manager.active_profile["image_base_name"]
    )
    click.echo(
        f"🗑️  Destroying {len(dangling_images)} dangling image{'s' if len(dangling_images) > 1 else ''}:"
    )
    for image in dangling_images:
        op = compute_manager.delete_image(image)

        spinner_text = f"Destroying image: '{image}'"
        done_text = f"🗑️  Image: '{image}' destroyed"

        poll_with_spinner(
            compute_manager=compute_manager,
            op_name=op["name"],
            text=spinner_text,
            done_text=done_text,
            scope="global",
        )

    # Delete Compute Engine Instance
    if not keep:
        op = compute_manager.delete_instance(
            instance_name=config_manager.active_profile["instance_name"],
            zone=active_zone,
        )

        spinner_text = (
            f"Destroying instance: '{config_manager.active_profile['instance_name']}'"
        )
        done_text = f"🗑️  Instance: '{config_manager.active_profile['instance_name']}' destroyed."

        poll_with_spinner(
            compute_manager=compute_manager,
            op_name=op["name"],
            text=spinner_text,
            done_text=done_text,
            scope="zone",
        )
