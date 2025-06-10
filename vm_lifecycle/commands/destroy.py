import click
from vm_lifecycle.config_manager import ConfigManager
from vm_lifecycle.compute_manager import GCPComputeManager


@click.command(name="destroy")
def destroy_vm():
    # Load profile
    config_manager = ConfigManager()

    # Profile check
    profile_check = config_manager.pre_run_profile_check()
    if not profile_check:
        click.echo("Error with active profile. Ensure a profile has been created.")
        return

    # GCP API check
    compute_manager = GCPComputeManager(
        config_manager.active_profile["project_id"],
        config_manager.active_profile["zone"],
    )

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
                f"🗑️  Delete instance: {config_manager.active_profile['instance_name']}?",
                default=False,
            ):
                op = compute_manager.delete_instance(
                    instance_name=config_manager.active_profile["instance_name"],
                    zone=config_manager.active_profile["zone"],
                )
                # click.echo(
                #     f"✅ Instance: '{config_manager.active_profile['instance_name']}' in zone: '{config_manager.active_profile['instance_name']}'."
                # )
            else:
                click.echo("❌ Aborted.")
                return

    # TODO: add spinner
    for update in compute_manager.wait_for_operation(
        op["name"], scope="zone", zone=config_manager.active_profile["zone"]
    ):
        if update == "RUNNING":
            print("Still running...")
        else:
            if update["success"]:
                print("Operation completed successfully.")
            else:
                print("Operation failed with error: ", update["error"])
