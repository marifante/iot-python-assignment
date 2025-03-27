#!/bin/bash

###############################################################################
## Function
log() {
	echo "$(date +"%Y-%m-%dT%H:%M:%S.%03N") - $*"
}

###############################################################################
## Parameters
DOCKER_IMAGE_EXECUTED_LOCALLY='exporter_ecoadapt:local'
DOCKERFILE='Dockerfile.exporter_ecoadapt'
REBUILD_IMAGE=false

## Fixed variables
SCRIPT_PATH=$(readlink -f "$0")
SCRIPT_DIR=$(dirname "$SCRIPT_PATH")

###############################################################################
## Process
while getopts "ron:" opt; do
	case ${opt} in
	r)
		REBUILD_IMAGE=true
		;;
	n)
		DOCKER_IMAGE_EXECUTED_LOCALLY="${OPTARG}:local"
		DOCKERFILE="Dockerfile.${OPTARG}"
		;;
	\?)
		echo "Invalid option: -$OPTARG"
		exit 1
		;;
	:)
		echo "The option -$OPTARG requires an argument."
		exit 1
		;;
	esac
done

RUN_CMD="docker run --rm -it -v $(pwd):/host_repo -w /host_repo ${DOCKER_IMAGE_EXECUTED_LOCALLY} /bin/bash"

if [ "${REBUILD_IMAGE}" = "true" ]; then
	log "erasing ${DOCKER_IMAGE_EXECUTED_LOCALLY}..."
	docker rmi -f ${DOCKER_IMAGE_EXECUTED_LOCALLY}
fi

if [[ "$(docker images -q ${DOCKER_IMAGE_EXECUTED_LOCALLY} 2>/dev/null)" == "" ]]; then
	log "${DOCKER_IMAGE_EXECUTED_LOCALLY} do no exists! building it..."
	uid="$(id -u)"
	gid="$(id -g)"
	log "Creating docker image (user, UID=${uid} and GID=${gid})"
	docker build -f ${SCRIPT_DIR}/../docker/${DOCKERFILE} \
		--build-arg USER_UID=${uid} --build-arg USER_GID=${gid} \
		-t ${DOCKER_IMAGE_EXECUTED_LOCALLY} . &&
		${RUN_CMD}
else
	log "yeah! ${DOCKER_IMAGE_EXECUTED_LOCALLY} exists!!"
	${RUN_CMD}
fi
