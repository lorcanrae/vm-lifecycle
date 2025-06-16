import click
import subprocess
import sys

from vm_lifecycle.gcp_helpers import init_gcp_context
from vm_lifecycle.utils import create_vm_ssh_connection


@click.command(name="connect")
@click.option("-p", "--path", type=click.Path(), help="Path to Open VS Code on VM")
def vscode_connect(path):
    config_manager, compute_manager, target_zone = init_gcp_context()
    if not config_manager:
        sys.exit(1)

    try:
        instance_status = compute_manager.get_instance_status(
            config_manager.active_profile["instance_name"],
            zone=target_zone,
        )
    except ValueError as e:
        if "not found in zone" in str(e):
            instance_status = "UNKNOWN"

    if instance_status == "UNKNOWN":
        click.echo(
            f"❗ Instance: '{config_manager.active_profile['instance_name']}' not found in zone: '{target_zone}'"
        )
        sys.exit(1)
    elif instance_status == "TERMINATED":
        click.echo(
            f"❗ Instance: '{config_manager.active_profile['instance_name']}' found, but not running. Run 'vmlc start' to turn on VM"
        )
        sys.exit(1)

    # Create SSH Connection
    create_vm_ssh_connection(
        project_id=config_manager.active_profile["project_id"],
        instance_name=config_manager.active_profile["instance_name"],
        zone=target_zone,
    )

    # Connect to instance
    instance_name = f"{config_manager.active_profile['instance_name']}.{target_zone}.{config_manager.active_profile['project_id']}"
    if path:
        conn_path = path
    else:
        conn_path = f"/home/{config_manager.active_profile['instance_user']}"

    subprocess.run(
        [
            "code",
            "--folder-uri",
            f"vscode-remote://ssh-remote+{instance_name}{conn_path}",
        ]
    )
