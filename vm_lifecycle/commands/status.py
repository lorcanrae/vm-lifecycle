import click
import subprocess

from vm_lifecycle.utils import init_gcp_context


@click.command(name="status")
def gcp_vm_instance_status():
    """List GCP Compute Engine instance resources"""

    config_manager, compute_manager, active_zone = init_gcp_context()
    if not config_manager:
        return

    subprocess.run(
        [
            "gcloud",
            "compute",
            "instances",
            "list",
            f"--project={config_manager.active_profile['project_id']}",
        ]
    )
