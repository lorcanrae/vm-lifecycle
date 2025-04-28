data "google_compute_instance" "vm_instance" {
  name    = var.instance_name
  zone    = var.zone
  project = var.project_id
}

resource "null_resource" "stop_vm" {
  triggers = {
    always_run = timestamp()
  }
  provisioner "local-exec" {
    command = "gcloud compute instances stop ${var.instance_name} --zone=${var.zone} --quiet || true"
  }
}

resource "google_compute_image" "vm_image" {
  name        = "${var.image_base_name}-${formatdate("YYYYMMDD-HHmmss", timestamp())}"
  source_disk = data.google_compute_instance.vm_instance.boot_disk[0].source
  project     = var.project_id
  family      = var.image_base_name
  depends_on  = [null_resource.stop_vm]
  lifecycle {
    prevent_destroy = false
  }
}

resource "null_resource" "delete_vm" {
  triggers = {
    always_run = timestamp()
  }
  depends_on = [google_compute_image.vm_image]

  provisioner "local-exec" {
    command = "gcloud compute instances delete ${var.instance_name} --zone=${var.zone} --quiet || true"
  }
}

resource "null_resource" "delete_old_images" {
  depends_on = [google_compute_image.vm_image]

  provisioner "local-exec" {
    command = "${path.module}/scripts/delete_old_images.sh ${var.image_base_name}"
  }
}
