.PHONY: env clean run check-env remove-env recreate-env analyze analyze-model compare-models

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
	PYTHONPATH=$(shell pwd) python src/check_env.py

run: check-env
	PYTHONPATH=$(shell pwd) python src/main.py

run-limit: check-env
	PYTHONPATH=$(shell pwd) python src/main.py --limit $(limit)

resume: check-env
	PYTHONPATH=$(shell pwd) python src/main.py --resume

analyze:
	PYTHONPATH=$(shell pwd) python src/analyze_results.py

analyze-model:
	PYTHONPATH=$(shell pwd) python src/analyze_results.py --model $(model)

compare-models:
	PYTHONPATH=$(shell pwd) python src/analyze_results.py --compare