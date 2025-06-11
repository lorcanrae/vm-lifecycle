# GCP VM Lifecycle

A CLI tool to manage the lifecycle of a Google Cloud Platform Compute Engine resource that is used as a remote *personal* instance, with a focus on cost minimisation by storing the VM as an [image](https://cloud.google.com/compute/docs/images) when not in use. Manage more than one personal VM with different profiles.

This tool is not intended to manage production resources that are created with CI or CD actions.

The CLI wrapper is written in Python, using [click](https://click.palletsprojects.com/en/stable/), and is primarily an abstraction over the GCP Compute Engine API.

# Usage

Recommended to install with [pipx](https://github.com/pypa/pipx) or uv.

## Pre-requisites

1. Have Python 3.12 or higher installed (might work on lower, unsure)
2. Have `gcloud` installed and authenticated with **Application Default Credentials**
3. *Should* work on both Windows and Unix-like operating systems. Only tested on Unix-like.

## Initialisation

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

## General Usage

Create a VM with:

```bash
vmlc create [OPTIONS]
    -i, --image     Name of a custom VM Image to use, default: Ubuntu 22.04 LTS
    -z, --zone      GCP Zone override, will update profile zone and region on successful operation
```

Stop a VM, create an image of the VM, prune dangling images, delete the instance:

```bash
vmlc stop [OPTIONS]
    -b, --basic     Stop the VM, no image is created, no instance is deleted
    -k, --keep      Stop the VM, image is created, no instance is deleted
```

Start a VM from an image or stopped instance.

```bash
vmlc start [OPTIONS]
    -z, --zone      GCP Zone override, will update profile 'zone' and 'region' on successful operation
```

Destroy current VM:

```bash
vmlc destroy [OPTIONS]
    -v, --vm        Destroy all VM Instances
    -i, --image     Destroy all Images
    -a, --all       Destroy all VM Instances and Images
```

Get the status of all VM instances for your project. A wrapper for `gcloud compute instances list --project=<your_project>`

```bash
vmlc status
```

Connect to an instance:

```bash
# Defaults to /home/<username>/code/
vmlc connect

# Or connect to a specific path - requires full absolute path
vmlc connect --path=/home/my/specific/path
```

## Disclaimer

Cloud Services costs money. I am in no way responsible for any costs attributed to users of this tool.
