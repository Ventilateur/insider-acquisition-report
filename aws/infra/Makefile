lambda-bundle:
	@zip infra-pkg.zip lambda.py

init:
	terraform init -backend-config="bucket=terraform-states-vhphan"

plan:
	terraform plan

apply:
	terraform apply -auto-approve

output:
	mkdir -p out && terraform output > out/terraform.tfvars
