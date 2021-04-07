
py-dep:
	@pip install --upgrade -r requirements.txt --target ./.py-dep

bundle:
	@rm -f deployment-pkg.zip
	@cd .py-dep && zip -r ../deployment-pkg.zip .
	@zip -gr deployment-pkg.zip scrape -x "*.pyc*"
