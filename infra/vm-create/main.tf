resource "google_compute_instance" "my-instance" {
  name         = var.instance_name
  machine_type = var.machine_type
  zone         = var.zone

  boot_disk {
    initialize_params {
      image = "ubuntu-2204-jammy-v20250305"
      size  = var.disk_size
      type  = "pd-balanced"
    }
  }

  network_interface {
    network = "default"
    access_config {
      network_tier = "STANDARD"
    }
  }

  metadata_startup_script = <<-EOT
#!/usr/bin/env bash
set -e

# Ensure the user exists
if ! id "${var.instance_user}" &>/dev/null; then
    useradd -m -s /bin/bash ${var.instance_user}
    echo "${var.instance_user} ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers
fi

# Ensure Ansible is installed
if ! command -v ansible &> /dev/null; then
    apt update -y
    apt install -y software-properties-common
    add-apt-repository --yes --update ppa:ansible/ansible
    apt install -y ansible
fi

# Output Ansible version
sudo -u ${var.instance_user} ansible --version

echo "Ansible installed successfully!"
EOT
}
