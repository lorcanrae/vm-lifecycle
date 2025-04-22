import click
import subprocess
from vm_lifecycle.utils import (
    load_config,
    describe_vm,
    check_running,
    pre_run_checks,
    create_vscode_ssh,
)
from vm_lifecycle.params import TF_WORKSPACES


@click.command(name="connect")
@click.option(
    "--path", type=click.Path(), default="/home/", help="Path to Open VS Code on VM"
)
def vscode_connect(path):
    "Connect to VM in VS Code inside ~/code/<username>"
    for workspace in TF_WORKSPACES:
        check = pre_run_checks(workspace)

    if not check:
        return

    # Build connection alias with gcloud
    config = load_config()

    create_vscode_ssh()

    # Make sure the VM is on
    if not check_running(
        describe_vm(config["zone"], config["project_id"], config["instance_name"])
    ):
        print(
            "VM is stopped. Run 'vmlc create' or 'vmlc restore' before trying to connect"
        )
    else:
        vscode_path = path if path else f"/home/{config['instance_user']}/code/"

        subprocess.run(
            [
                "code",
                "--folder-uri",
                f"vscode-remote://ssh-remote+{config['instance_name']}.{config['zone']}.{config['project_id']}{vscode_path}",
            ]
        )
