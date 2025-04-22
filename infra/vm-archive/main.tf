resource "null_resource" "stop_vm" {
  triggers = {
    always_run = timestamp()
  }
  provisioner "local-exec" {
    command = "gcloud compute instances stop ${var.instance_name} --zone=${var.zone} --quiet"
  }
}

resource "google_compute_image" "vm_snapshot" {
  name        = "${var.image_base_name}-${formatdate("YYYYMMDD-HHmmss", timestamp())}"
  family      = var.image_base_name
  source_disk = "zones/${var.zone}/disks/${var.instance_name}"
  depends_on  = [null_resource.stop_vm]
}

resource "null_resource" "delete_vm" {
  triggers = {
    always_run = timestamp()
  }
  depends_on = [google_compute_image.vm_snapshot]

  provisioner "local-exec" {
    command = "gcloud compute instances delete ${var.instance_name} --zone=${var.zone} --quiet || true"
  }
}
