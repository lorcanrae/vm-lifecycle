import click

# from vm_lifecycle.config_manager import ConfigManager
# from vm_lifecycle.compute_manager import GCPComputeManager
from vm_lifecycle.utils import poll_with_spinner, init_gcp_context


@click.command(name="stop")
@click.option("-k", "--keep", is_flag=True, help="Do not delete the instance.")
@click.option(
    "-b",
    "--basic",
    is_flag=True,
    help="Only shut down the VM instance. No images will will be created, no instances will be destroyed",
)
def stop_vm_instance(keep, basic):
    """Stop VM instance, create image of instance, delete instance"""
    config_manager, compute_manager, active_zone = init_gcp_context()
    if not config_manager:
        return

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

        spinner_text = f"Stopping instance: '{config_manager.active_profile['instance_name']}' in zone: '{active_zone}'"
        done_text = f"✅ Instance: '{config_manager.active_profile["instance_name"]}' in zone: '{active_zone}' stopped"

        poll_with_spinner(
            compute_manager=compute_manager,
            op_name=op["name"],
            text=spinner_text,
            done_text=done_text,
            scope="zone",
            zone=active_zone,
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

    if not basic:
        # Create an image from the stopped instance
        op = compute_manager.create_image_from_instance(
            instance_name=config_manager.active_profile["instance_name"],
            image_name=config_manager.active_profile["image_base_name"],
            family=config_manager.active_profile["image_base_name"],
            zone=active_zone,
        )

        spinner_text = f"Creating image from instance: '{config_manager.active_profile['instance_name']}'"

        image_name = op["targetLink"].split("/")[-1]
        done_text = f"✅ Image: '{image_name}' created from instance: '{config_manager.active_profile['instance_name']}'"
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
        if dangling_images:
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
    if not keep and not basic:
        op = compute_manager.delete_instance(
            instance_name=config_manager.active_profile["instance_name"],
            zone=active_zone,
        )

        spinner_text = f"Destroying VM instance: {config_manager.active_profile['instance_name']} in zone: '{config_manager.active_profile['zone']}'"
        done_text = f"🗑️  VM instance: '{config_manager.active_profile['instance_name']}' in zone: '{active_zone}' destroyed."

        poll_with_spinner(
            compute_manager=compute_manager,
            op_name=op["name"],
            text=spinner_text,
            done_text=done_text,
            scope="zone",
            zone=active_zone,
        )
