import click
from vmlc.commands.create import create_vm
from vmlc.commands.archive import archive_vm
from vmlc.commands.restore import restore_vm_from_image
from vmlc.commands.config import init


@click.group()
def cli():
    """CLI tool to manage GCP VM lifecycle"""
    pass


cli.add_command(create_vm)
cli.add_command(archive_vm)
cli.add_command(restore_vm_from_image)
cli.add_command(init)


if __name__ == "__main__":
    cli()
