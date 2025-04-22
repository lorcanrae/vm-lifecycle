import click
import subprocess
from vm_lifecycle.utils import load_config

# TODO: all of this


def describe_vm(zone: str, project: str) -> str:
    """Get the description of the VM"""
    response = str(
        subprocess.check_output(
            [
                "gcloud",
                "compute",
                "instances",
                "describe",
                f"--zone={zone}",
                "--project={project}",
            ]
        )
    )
    return response


def check_running(status) -> bool:
    return "RUNNING" in status


@click.command()
def connect():
    "Connect to VM in VS Code inside ~/code/<username>"
    config = load_config(__file__)
    if not check_running(describe_vm(config["zone"], config["project_id"])):
        print("VM is stopped. Run 'vmlc start' before trying to connect")
    else:
        subprocess.run(
            [
                "code",
                "--folder-uri",
                f"vscode-remote://ssh-remote+{config['instance_name']}.{config['zone']}.{config['project_id']}/home/{config['instance_user']}/code/",
            ]
        )
