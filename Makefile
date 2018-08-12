.PHONY: clean
clean:
	rm -rf venv

.PHONY: dev
dev:
	venv/bin/python -m dobson.main

venv: vendor/venv-update requirements.txt requirements-dev.txt
	vendor/venv-update venv= -ppython3 venv install= -r requirements.txt -r requirements-dev.txt

.PHONY: update-requirements
update-requirements: venv
	venv/bin/upgrade-requirements
