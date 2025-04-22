variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
}

variable "zone" {
  description = "GCP Zone"
  type        = string
}

variable "instance_name" {
  description = "VM Name"
  type        = string
}

variable "instance_user" {
  description = "VM User, match to local username"
  type        = string
}

variable "machine_type" {
  description = "GCP VM Machine type"
  type        = string
}

variable "image_base_name" {
  default = "my-custom-vm"
}
