# GCP VM Lifecycle

A CLI tool to manage the lifecycle of a Google Cloud Platform Compute Engine resource that is used as a remote *personal* instance, with a focus on cost reduction. This is not intended to manage production resources that are created in CI/CD.

The core is three terraform modules:
1. Create - create a GCP Compute Engine instance with Ubuntu 22.04, creating a user that matches the CLI host, and install Ansible.
2. Archive - turn off the Compute Engine instance, create a time-stamped GCP Image, and destroy the Compute Engine instance.
3. Restore - create a GCP Compute Engine instance from the most recent timestamped image, delete any historical images.

The CLI wrapper written in Python, using Click.

# Usage

Recommended to install with pipx

```bash
pipx install
```

## Pre-requisites

1. Use a unix-like operating system.
2. Have Python 3.12 or higher installed.
3. Be authenticated with `gcloud`. This tool is intended to manage a *personal* GCP VM instance. The assumption is that you have run `gcloud auth login`. There is no support for service accounts and service account keys in the CLI directly.
4. Have terraform installed.

## Initialisation

Initialize the CLI to set GCP config and initialize the terraform workspaces with:

```bash
vmlc init
```

If you want to initialize just the GCP config:

```bash
vmlc init config
```

Or initialize the terraform workspaces:

```bash
vmlc init tf
```



# TODO

1. Create a connect command
2. Tests
