# GCP VM Lifecycle

A CLI tool to manage the lifecycle of a Google Cloud Platform Compute Engine resource that is used as a remote *personal* instance, with a focus on cost reduction. This is not intended to manage production resources that are created in CI/CD.

There are three terraform modules:
1. **Create** - create a GCP Compute Engine instance with Ubuntu 22.04, creating a user that matches the CLI host, and install Ansible.
2. **Archive** - turn off the Compute Engine instance, create a time-stamped GCP Image, and destroy the Compute Engine instance.
3. **Restore** - create a GCP Compute Engine instance from the most recent timestamped image, delete any historical images.

The CLI wrapper written in Python, using [click](https://click.palletsprojects.com/en/stable/).

This is not the most ideal application of Terraform, it would probably be easier to do everything with `gcloud` calls. I was just playing around to see how far I could get.

# Usage

Recommended to install with [pipx](https://github.com/pypa/pipx).

## Pre-requisites

1. A unix-like operating system
2. Have Python 3.12 or higher installed (might work on lower, unsure)
3. Have `gcloud` installed and authenticated
4. Have terraform installed

## Initialisation

Initialize the CLI to set GCP config and initialize the terraform workspaces with:

```bash
vmlc init

# Just GCP Config
vmlc init config

# Just terraform workspaces
vmlc init tf
```

## General Usage

Create a VM with:

```bash
vmlc create
```

Archive (create an image and destroy the instance) with:

```bash
vmlc archive
```

Restore (create a VM instance from the most recent image) with:

```bash
vmlc restore
```

Use VS Code to connect to an instance (requires SSH - Config VS Code extension):

```bash
# Defaults to /home/<username>/code/
vmlc connect

# Or connect to a specific path - requires full absolute path
vmlc connect --path=/home/my/specific/path
```

Destroy all GCP assets (VM and images):

```bash
vmlc destroy

# Maintain terraform state
vmlc destroy --keep-state

# Do a dry run
vmlc destroy --dry-run
```
