import click
import subprocess
import sys

from vm_lifecycle.gcp_helpers import init_gcp_context


@click.command(name="status")
@click.option(
    "-i", "--images", is_flag=True, help="Retrieve list of images for active project."
)
def gcp_vm_instance_status(images):
    """List GCP Compute Engine instance resources"""

    config_manager, compute_manager, active_zone = init_gcp_context()
    if not config_manager:
        sys.exit(1)

    if not images:
        subprocess.run(
            [
                "gcloud",
                "compute",
                "instances",
                "list",
                f"--project={config_manager.active_profile['project_id']}",
            ]
        )

    if images:
        found_images = compute_manager.list_images()

        if found_images:
            click.echo(
                f"💿 Found {len(found_images)} image{'s' if len(found_images) > 1 else ''}:"
            )
            for image in found_images:
                click.echo(f"\t{image['name']}")
            sys.exit(0)
        else:
            sys.exit(1)
