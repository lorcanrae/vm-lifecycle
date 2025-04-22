import subprocess
import click
from vm_lifecycle.utils import pre_run_checks
from vm_lifecycle.params import ROOT_DIR


@click.command(name="restore")
def restore_vm_from_image():
    """Restore a VM from the latest image and delete old images"""
    pre_run_checks(workspace="vm-restore")
    click.echo("Restoring VM...")
    subprocess.run(
        ["make", "apply", "workspace=vm-restore"],
        check=True,
        cwd=ROOT_DIR,
    )
