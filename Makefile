
.PHONY=unittests integration_tests

unittests:
	pytest

integration_tests:
	docker compose up --build
