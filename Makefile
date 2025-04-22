# Terraform binary
TF ?= terraform

# Workspace name (can override with workspace=vm-create)
workspace ?= vm-create
dir := infra/$(workspace)

# List of available workspaces
workspaces := vm-create vm-archive vm-restore

# Terraform commands
init:
	@cd $(dir) && $(TF) init

apply:
	cd $(dir) && $(TF) init && $(TF) apply -auto-approve -var-file=terraform.tfvars

destroy:
	cd $(dir) && $(TF) init && $(TF) destroy -var-file=terraform.tfvars

plan:
	cd $(dir) && $(TF) init && $(TF) plan -var-file=terraform.tfvars

show:
	cd $(dir) && $(TF) show

output:
	cd $(dir) && $(TF) output

refresh:
	cd $(dir) && $(TF) refresh -var-file=terraform.tfvars

validate:
	cd $(dir) && $(TF) validate

workspace-list:
	@echo "Available workspaces: $(workspaces)"

init-all:
	@echo "Initializing all Terraform workspaces..."
	@$(MAKE) init workspace=vm-create
	@$(MAKE) init workspace=vm-archive
	@$(MAKE) init workspace=vm-restore

.PHONY: init apply destroy plan show output refresh validate workspace-list init-all
