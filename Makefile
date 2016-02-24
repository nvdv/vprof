all: lint test deps_install install clean

.PHONY: test
test:
	python -m unittest discover -b vprof "*_test.py"
	npm run test

e2e_test:
	python -m unittest discover -b vprof "*_e2e.py"

install:
	npm run build
	pip install .

deps_install:
	npm install
	pip install -r requirements.txt
	pip install -r dev_requirements.txt

lint:
	npm run lint
	pylint --reports=n --rcfile=pylint.rc vprof/*.py

clean:
	rm -rf vprof/frontend/vprof_min.js
