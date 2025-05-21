.PHONY: env clean run check-env remove-env recreate-env

env:
	conda env create -f environment.yml

update-env:
	conda env update -f environment.yml

remove-env:
	conda env remove -n agir-eu

recreate-env: remove-env env
	@echo "Environment recreated. Please run: conda activate agir-eu"

clean:
	rm -rf ./__pycache__
	rm -rf ./venv

check-env:
	PYTHONPATH=$(shell pwd) src/python check_env.py

run: check-env
	PYTHONPATH=$(shell pwd) src/python main.py

run-limit: check-env
	PYTHONPATH=$(shell pwd) src/python main.py --limit $(limit)

resume: check-env
	PYTHONPATH=$(shell pwd) src/python main.py --resume --limit $(limit)