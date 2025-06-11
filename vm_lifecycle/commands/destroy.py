import click

from vm_lifecycle.utils import poll_with_spinner, init_gcp_context


@click.command(name="destroy")
@click.option("-v", "--vm", help="Destroy all VM Instances")
@click.option("-i", "--image", help="Destroy all VM Images")
@click.option("-a", "--all", help="Destroy all GCP Assets")
def destroy_vm_instance(vm, image, all):
    config_manager, compute_manager, active_zone = init_gcp_context()
    if not config_manager:
        return

    # Check Instance exists
    existing_instances = compute_manager.list_instances()

    if not existing_instances:
        click.echo(
            f"❗ No GCP Compute Engine instances found in zone: '{config_manager.active_profile['zone']}'."
        )
        return
    for instance in existing_instances:
        if instance["name"] == config_manager.active_profile["instance_name"]:
            if click.confirm(
                f"❓ Destroy instance: '{config_manager.active_profile['instance_name']}' in zone: '{active_zone}'?",
                default=False,
            ):
                op = compute_manager.delete_instance(
                    instance_name=config_manager.active_profile["instance_name"],
                    zone=active_zone,
                )
            else:
                click.echo("❌ Aborted.")
                return

    spinner_text = (
        f"Destroying VM instance: {config_manager.active_profile['instance_name']}"
    )
    done_text = f"🗑️  VM instance: '{config_manager.active_profile['instance_name']}' in zone: '{active_zone}' destroyed."
    poll_with_spinner(
        compute_manager=compute_manager,
        op_name=op["name"],
        text=spinner_text,
        done_text=done_text,
        scope="zone",
        zone=active_zone,
    )
