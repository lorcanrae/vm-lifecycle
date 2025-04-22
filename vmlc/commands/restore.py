import subprocess
import click
from vmlc.utils import get_root_dir, pre_run_checks


@click.command(name="restore")
def restore_vm_from_image():
    """Restore a VM from the latest image and delete old images"""
    pre_run_checks(workspace="vm-restore")
    click.echo("Restoring VM...")
    root = get_root_dir(__file__)
    subprocess.run(
        ["make", "apply", "workspace=vm-restore"],
        check=True,
        cwd=root,
    )
