
py-dep:
	@pip install -r requirements.txt --target ./.py-dep

bundle:
	@cd .py-dep && zip -r ../deployment-pkg.zip .
	@zip -g deployment-pkg.zip edgar.py sec4.py

