
.PHONY=dockershell_rebuild dockershell unittests integration_tests compile_protobuf

dockershell_rebuild:
	./scripts/dockershell.sh -r

dockershell:
	./scripts/dockershell.sh

unittests:
	pytest

integration_tests:
	docker compose up --build

integration_tests_debug:
	LOG_LEVEL=DEBUG docker compose up --build

compile_protobuf:
	protoc --python_out=. src/exporter_ecoadapt/generated/power_elec6_message.proto
