import subprocess
import click
from vmlc.utils import get_root_dir, pre_run_checks


@click.command(name="archive")
def archive_vm():
    """Turn of an existing VM, create an image from it, and delete the instance"""
    pre_run_checks(workspace="vm-archive")
    click.echo("Archiving VM...")
    root = get_root_dir(__file__)
    subprocess.run(
        ["make", "apply", "workspace=vm-archive"],
        check=True,
        cwd=root,
    )


if __name__ == "__main__":
    print(get_root_dir(__file__))
