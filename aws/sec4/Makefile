init:
	terraform init -backend-config="bucket=terraform-states-vhphan"

plan:
	terraform plan -var-file=../infra/out/terraform.tfvars

apply:
	terraform apply -auto-approve -var-file=../infra/out/terraform.tfvars