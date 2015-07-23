runtests:
	python -m vprof.tests

install:
	pip install .

devdeps_install:
	npm install

lint:
	npm run lint