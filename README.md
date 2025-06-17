# GCP VM Lifecycle

A CLI tool to manage the lifecycle of a Google Cloud Platform Compute Engine resource that is used as a remote *personal* instance, with a focus on cost minimisation by storing the VM as an [image](https://cloud.google.com/compute/docs/images) when not in use. Manage more than one personal VM with different profiles.

This tool is not intended to manage production resources that are created with CI or CD actions.

The CLI wrapper is written in Python, using [click](https://click.palletsprojects.com/en/stable/).

## Requirements

1. Have Python 3.12 or higher installed.
2. Have `gcloud` installed and authenticated with **Application Default Credentials** - typically with `gcloud auth application-default login`
3. Unix-like operating system. It *might* work on Windows. Only tested on Unix-like.

## Installation

Recommended to install with [pipx](https://github.com/pypa/pipx).

```bash
pipx install git+https://github.com/lorcanrae/vm-lifecycle.git
```

The tool uses profiles for each different VM you want to manage. Create a profile with `vmlc profile create` to locally store:
- GCP Project ID
- GCP Zone and Region
- Instance Configuration:
    - Instance Name
    - Instance User Name (recommended to match local username)
    - Disk Size
    - Hardware config (CPU, RAM)

No secrets are stored in plain text. Every command used will use the active profile.

Tool uses `gcloud compute config-ssh` to generate the SSH connection to a running instance. There is no support for manually created SSH keys.

## Usage

### Profile Management

Create a profile:

```bash
vmlc profile create
```

And follow the prompts.

Other commands:

```bash
# Show all profiles and active profile
vmlc profile show

# Set an active profile interactively or by name
vmlc profile set [PROFILE_NAME]

# Delete a profile by name or delete all profiles
vmlc profile delete [OPTIONS] [PROFILE_NAME]
    -a, --all       Delete all profiles
```

### General Usage

Create a VM with:

```bash
vmlc create [OPTIONS]
    -i, --image     Name of a custom VM Image to use (default: Ubuntu 22.04 LTS)
    -z, --zone      GCP Zone override, updates profile zone and region on successful operation
```

Start a VM from a stopped instance or image related to the current profile.

```bash
vmlc start [OPTIONS]
    -z, --zone      GCP Zone override, updates profile zone and region on successful operation
```

Stop a VM, create an image of the VM, prune dangling images, delete the instance:

```bash
vmlc stop [OPTIONS]
    -b, --basic     Stop the VM, no image is created, no instance is deleted
    -k, --keep      Stop the VM, image is created, no instance is deleted
```

If you use VS Code, connect to an instance:

```bash
# Defaults to /home/<instance_user>/
vmlc connect [OPTIONS]
    -p, --path      Target connection path (requires absolute path)
```

The general flow is:
➡️ Create a **profile**
➡️ **create** an instance, set it up to your preference
➡️ Use **start** and **stop** as required
➡️ Use **connect** to connect to an instance.

If a GCP Zone has exhausted compute resources, start an instance from a stopped instance or image in a different zone with:

```bash
vmlc start -z <different_gcp_zone>
```

### Extended Usage

Get the status of all VM instances for a GCP project. A wrapper for `gcloud compute instances list --project=<your_project>`

```bash
vmlc status [OPTIONS]
    -i, --images    List all images for the project
```

Destroy VM based on active profile:

```bash
vmlc destroy [OPTIONS]
    -v, --vm        Interactively destroy VM Instances (singular, all)
    -i, --images    Interactively destroy Images (singular, all)
```

## Disclaimer

Cloud Services costs money. I am in no way responsible for any costs attributed to users of this software.
