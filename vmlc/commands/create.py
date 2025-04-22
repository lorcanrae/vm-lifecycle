import subprocess
import click
from vmlc.utils import get_root_dir, pre_run_checks


@click.command(name="create")
def create_vm():
    """Create GCP VM using Terraform"""
    pre_run_checks(workspace="vm-create")
    click.echo("Creating VM...")
    root = get_root_dir(__file__)
    subprocess.run(["make", "apply", "workspace=vm-create"], check=True, cwd=root)
