data "google_compute_image" "latest_image" {
  project     = var.project_id
  family      = var.image_base_name
  most_recent = true
}

resource "google_compute_instance" "vm_from_image" {
  name         = var.instance_name
  machine_type = var.machine_type
  zone         = var.zone

  boot_disk {
    initialize_params {
      image = data.google_compute_image.latest_image.self_link
    }
  }

  network_interface {
    network = "default"
    access_config {
      network_tier = "STANDARD"
    }
  }
}
