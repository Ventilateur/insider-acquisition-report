
py-dep:
	@pip install --upgrade -r requirements.txt --target ./.py-dep

infra/lambda-bundle:
	@zip aws/infra/infra-pkg.zip infra/lambda.py

sec4/infra-info:
	@cd aws/infra && terraform output > ../sec4/terraform.tfvars

sec4/lambda-bundle:
	@rm -f aws/sec4/sec4-pkg.zip
	@cd .py-dep && zip -r ../aws/sec4/sec4-pkg.zip .
	@zip -gr aws/sec4/sec4-pkg.zip sec4
