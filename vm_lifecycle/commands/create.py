import subprocess
import click
from vm_lifecycle.utils import pre_run_checks
from vm_lifecycle.params import ROOT_DIR


@click.command(name="create")
def create_vm():
    """Create GCP VM using Terraform"""
    pre_run_checks(workspace="vm-create")
    click.echo("Creating VM...")
    subprocess.run(["make", "apply", "workspace=vm-create"], check=True, cwd=ROOT_DIR)
