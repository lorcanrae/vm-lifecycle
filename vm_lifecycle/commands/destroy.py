import subprocess
import click
from vm_lifecycle.utils import get_root_dir, remove_tfstate_files
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime


@click.command(name="destroy")
@click.option(
    "--dry-run", is_flag=True, help="Preview with Terraform plan instead of destroy"
)
@click.option(
    "--log-file", type=click.Path(), default="destroy.log", help="Log output to file"
)
def destroy_all(dry_run, log_file):
    """Destroy all GCP resources managed by vmlc Terraform workspaces"""
    root = get_root_dir(__file__)
    mode = "plan" if dry_run else "destroy"
    workspaces = ["vm-create", "vm-archive", "vm-restore"]

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    log_file = log_file or f"destroy-{timestamp}.log"

    click.echo(f"⚠️ Running `terraform {mode}` in all workspaces...")

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
            cwd=root,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        log_entry += result.stdout

        if not dry_run:
            remove_tfstate_files(root / f"infra/{ws}")

        return log_entry

    with ThreadPoolExecutor() as executor:
        results = executor.map(destroy_workspace, workspaces)

    with open(log_file, "a") as log:
        for entry in results:
            log.write(entry + "\n")

    click.echo(
        f"✅ All Terraform workspaces processed in '{mode}' mode. Log saved to {log_file}"
    )
