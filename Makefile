.PHONY: env clean run check-env remove-env recreate-env

env:
	conda env create -f environment.yml

update-env:
	conda env update -f environment.yml

remove-env:
	conda env remove -n agir-eu

recreate-env: remove-env env
	@echo "环境已重新创建，请运行: conda activate agir-eu"

clean:
	rm -rf ./__pycache__
	rm -rf ./venv

check-env:
	python check_env.py

run: check-env
	python main.py

run-limit: check-env
	python main.py --limit $(limit)

resume: check-env
	python main.py --resume --limit $(limit)