import click
from vm_lifecycle.commands.create import create_vm
from vm_lifecycle.commands.archive import archive_vm
from vm_lifecycle.commands.restore import restore_vm_from_image
from vm_lifecycle.commands.destroy import destroy_all
from vm_lifecycle.commands.config import init
from vm_lifecycle.commands.connect import vscode_connect


@click.group()
def cli():
    """CLI tool to manage GCP VM lifecycle"""
    pass


cli.add_command(create_vm)
cli.add_command(archive_vm)
cli.add_command(restore_vm_from_image)
cli.add_command(init)
cli.add_command(destroy_all)
cli.add_command(vscode_connect)

if __name__ == "__main__":
    cli()
