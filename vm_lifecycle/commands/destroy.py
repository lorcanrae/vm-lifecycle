import subprocess
import click
from vm_lifecycle.utils import remove_tfstate_files
from vm_lifecycle.params import TF_WORKSPACES, ROOT_DIR
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime


@click.command(name="destroy")
@click.option(
    "--dry-run", is_flag=True, help="Preview with Terraform plan instead of destroy"
)
@click.option(
    "--keep-state", is_flag=True, help="Keep 'terraform.state' files after destroy"
)
def destroy_all(dry_run, keep_state):
    """Destroy all GCP resources managed by vmlc Terraform workspaces"""
    mode = "plan" if dry_run else "destroy"
    workspaces = TF_WORKSPACES

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    log_file = f"destroy-{timestamp}.log"

    click.echo(f"⚠️ Running 'terraform {mode}' in all workspaces...")

    if not dry_run and not click.confirm(
        "Are you sure you want to destroy all resources?", default=False
    ):
        click.echo("Aborted.")
        return

    def destroy_workspace(ws: str):
        log_entry = f"\n=== {mode.upper()} {ws} ===\n"
        click.echo(f"🧨 {mode.title()} workspace: {ws}")
        result = subprocess.run(
            ["make", mode, f"workspace={ws}"],
            cwd=ROOT_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        log_entry += result.stdout

        if not dry_run and not keep_state:
            remove_tfstate_files(ROOT_DIR / f"infra/{ws}")

        return log_entry

    with ThreadPoolExecutor() as executor:
        results = executor.map(destroy_workspace, workspaces)

    with open(log_file, "a") as log:
        for entry in results:
            log.write(entry + "\n")

    click.echo(
        f"✅ All Terraform workspaces processed in '{mode}' mode. Log saved to {log_file}"
    )
