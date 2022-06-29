.PHONY: install
install:
	pipenv install --dev

.PHONY: run
run:
	pipenv run flask run

.PHONY: debug
debug:
	FLASK_ENV=development pipenv run flask run

all: install run
