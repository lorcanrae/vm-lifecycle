import subprocess
import click
from vm_lifecycle.utils import (
    pre_run_checks,
    remove_tfstate_files,
    describe_vm_status_code,
    load_config,
)
from vm_lifecycle.params import ROOT_DIR, DEFAULT_CONFIG_PATH


@click.command(name="archive")
def archive_vm():
    """Turn of an existing VM, create an image from it, and delete the instance"""
    checks = pre_run_checks(workspace="vm-archive")
    config = load_config(DEFAULT_CONFIG_PATH)
    status = describe_vm_status_code(
        config["zone"], config["project_id"], config["instance_name"]
    )
    if "ERROR" in status.stderr:
        click.echo(f"No VM named: [{config['instance_name']}] to archive. Aborting.")
        return

    remove_tfstate_files(ROOT_DIR / "infra/vm-archive", echo=False)
    if not checks:
        return
    click.echo("Archiving VM...")
    subprocess.run(
        ["make", "apply", "workspace=vm-archive"],
        check=True,
        cwd=ROOT_DIR,
    )
