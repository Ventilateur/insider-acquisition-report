.PHONY: all

_check_env:
ifndef AWS_ACCESS_KEY_ID
	$(error AWS_ACCESS_KEY_ID is undefined)
endif
ifndef AWS_SECRET_ACCESS_KEY
	$(error AWS_SECRET_ACCESS_KEY is undefined)
endif
ifndef AWS_DEFAULT_REGION
	$(error AWS_DEFAULT_REGION is undefined)
endif
ifndef AWS_TF_S3_BUCKET
	$(error AWS_TF_S3_BUCKET is undefined)
endif


%/init: _check_env
	@cd aws/$* && terraform init -backend-config="bucket=$(AWS_TF_S3_BUCKET)"

%/validate: _check_env
	@cd aws/$* && terraform validate

%/plan: _check_env
	@$(MAKE) $*/lambda-bundle
	@cd aws/$* && terraform plan

%/apply: _check_env
	@$(MAKE) $*/lambda-bundle
	@cd aws/$* && terraform apply -auto-approve

%/infra-info: _check_env
	@cd aws/infra && terraform output > ../$*/terraform.tfvars

tf-fmt:
	@terraform fmt -recursive aws

py-dep:
	@pip install --upgrade -r requirements.txt --target ./.py-dep

infra/lambda-bundle:
	@zip -r aws/infra/infra-pkg.zip infra

sec4/lambda-bundle:
	@rm -f aws/sec4/sec4-pkg.zip
	@cd .py-dep && zip -r ../aws/sec4/sec4-pkg.zip .
	@zip -gr aws/sec4/sec4-pkg.zip sec4
