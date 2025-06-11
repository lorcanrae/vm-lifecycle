#!/usr/bin/env bash
set -e

# Ensure the user exists
if ! id "{instance_user}" &>/dev/null; then
    useradd -m -s /bin/bash {instance_user}
    echo "{instance_user} ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers
fi

# Ensure Ansible is installed
if ! command -v ansible &> /dev/null; then
    apt update -y
    apt install -y software-properties-common
    add-apt-repository --yes --update ppa:ansible/ansible
    apt install -y ansible
fi

echo "Ansible installed successfully!"
