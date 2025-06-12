import click
import subprocess
import sys

from vm_lifecycle.gcp_helpers import init_gcp_context


@click.command(name="status")
def gcp_vm_instance_status():
    """List GCP Compute Engine instance resources"""

    config_manager, compute_manager, active_zone = init_gcp_context()
    if not config_manager:
        sys.exit(1)

    subprocess.run(
        [
            "gcloud",
            "compute",
            "instances",
            "list",
            f"--project={config_manager.active_profile['project_id']}",
        ]
    )
