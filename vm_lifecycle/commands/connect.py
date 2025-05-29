import click
import subprocess
from vm_lifecycle.utils import (
    load_config,
    describe_vm,
    pre_run_checks,
    create_vscode_ssh,
    check_vm_status,
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
    gcp_instance_name = (
        f"{config['instance_name']}.{config['zone']}.{config['project_id']}"
    )
    status = check_vm_status(
        describe_vm(config["zone"], config["project_id"], config["instance_name"])
    )

    if status == "ERROR":
        print(
            "No VM found. Run 'vmlc create' or 'vmlc restore' before trying to connect"
        )
        return
    elif status == "OFF":
        print("Turning VM on.")
        subprocess.run(
            [
                "gcloud",
                "compute",
                "instances",
                "start",
                f"--zone={config['zone']}",
                f"--project={config['project_id']}",
                config["instance_name"],
            ]
        )

    create_vscode_ssh()

    # Make sure the VM is on
    if path == "/home/":
        vscode_path = f"/home/{config['instance_user']}/code/lorcanrae"
    else:
        vscode_path = path

    subprocess.run(
        [
            "code",
            "--folder-uri",
            f"vscode-remote://ssh-remote+{gcp_instance_name}{vscode_path}",
        ]
    )
