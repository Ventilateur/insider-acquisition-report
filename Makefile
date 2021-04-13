
py-dep:
	@pip install --upgrade -r requirements.txt --target ./.py-dep

bundle:
	@rm -f infra/deployment-pkg.zip
	@cd .py-dep && zip -r ../infra/deployment-pkg.zip .
	@zip -gr infra/deployment-pkg.zip scrape -x "*.pyc*"

infra/lambda-bundle:
	@zip aws/infra/infra-pkg.zip infra/lambda.py
