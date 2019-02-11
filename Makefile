#
# Copyright 2018 the original author or authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

ifeq ($(TAG),)
TAG := latest
endif

ifeq ($(TARGET_TAG),)
TARGET_TAG := latest
endif

ifneq ($(http_proxy)$(https_proxy),)
# Include proxies from the environment
DOCKER_PROXY_ARGS = \
       --build-arg http_proxy=$(http_proxy) \
       --build-arg https_proxy=$(https_proxy) \
       --build-arg ftp_proxy=$(ftp_proxy) \
       --build-arg no_proxy=$(no_proxy) \
       --build-arg HTTP_PROXY=$(HTTP_PROXY) \
       --build-arg HTTPS_PROXY=$(HTTPS_PROXY) \
       --build-arg FTP_PROXY=$(FTP_PROXY) \
       --build-arg NO_PROXY=$(NO_PROXY)
endif

DOCKER_BUILD_ARGS = \
        --build-arg TAG=$(TAG) \
        --build-arg REGISTRY=$(REGISTRY) \
        --build-arg REPOSITORY=$(REPOSITORY) \
        $(DOCKER_PROXY_ARGS) $(DOCKER_CACHE_ARG) \
         --rm --force-rm \
        $(DOCKER_BUILD_EXTRA_ARGS)

DOCKER_IMAGE_LIST = \
	pyvoltha-base \
        pyvoltha

VENVDIR := venv-$(shell uname -s | tr '[:upper:]' '[:lower:]')

VENV_BIN ?= virtualenv
VENV_OPTS ?=

.PHONY: $(DIRS) $(DIRS_CLEAN) $(DIRS_FLAKE8) flake8 protos venv rebuild-venv clean distclean build test docker_base_img docker_image

# This should to be the first and default target in this Makefile
help:
	@echo "Usage: make [<target>]"
	@echo "where available targets are:"
	@echo
	@echo "build                : Build the protos"
	@echo "dist                 : Build the protos and create the python package"
	@echo "docker_base_img      : Build a base docker image with a modern version of pip and requirements.txt installed"
	@echo "docker_image         : Build a docker image with pyvoltha installed"
	@echo "test                 : Run all unit test"
	@echo "clean                : Remove files created by the build and tests"
	@echo "distclean            : Remove venv directory"
	@echo "help                 : Print this help"
	@echo "protos               : Compile all grpc/protobuf files"
	@echo "rebuild-venv         : Rebuild local Python virtualenv from scratch"
	@echo "venv                 : Build local Python virtualenv if did not exist yet"
	@echo

## New directories can be added here
#DIRS:=

## If one directory depends on another directory that
## dependency can be expressed here
##
## For example, if the Tibit directory depended on the eoam
## directory being built first, then that can be expressed here.
##  driver/tibit: eoam

# Parallel Build
$(DIRS):
	@echo "    MK $@"
	$(Q)$(MAKE) -C $@

# Parallel Clean
DIRS_CLEAN = $(addsuffix .clean,$(DIRS))
$(DIRS_CLEAN):
	@echo "    CLEAN $(basename $@)"
	$(Q)$(MAKE) -C $(basename $@) clean

# Parallel Flake8
DIRS_FLAKE8 = $(addsuffix .flake8,$(DIRS))
$(DIRS_FLAKE8):
	@echo "    FLAKE8 $(basename $@)"
	-$(Q)$(MAKE) -C $(basename $@) flake8

build: protos

protos:
	make -C pyvoltha/protos

dist: venv protos
	@ echo "Creating PyPi artifacts"
	python setup.py sdist

upload: dist
	@ echo "Uploading PyPi artifacts"
	twine upload --repository-url https://test.pypi.org/legacy/ dist/*
	twine upload dist/*

docker_base_img:
	docker build $(DOCKER_BUILD_ARGS) -t ${REGISTRY}${REPOSITORY}pyvoltha-base:${TAG} -f docker/Dockerfile.base .

docker_image: docker_base_img dist
	docker build $(DOCKER_BUILD_ARGS) -t ${REGISTRY}${REPOSITORY}pyvoltha:${TAG} -f docker/Dockerfile.pyvoltha .

install-protoc:
	make -C pyvoltha/protos install-protoc

test: venv protos
	@ echo "Executing all unit tests"
	@ . ${VENVDIR}/bin/activate && tox
#	@ . ${VENVDIR}/bin/activate && make -C test utest

COVERAGE_OPTS=--with-xcoverage --with-xunit --cover-package=voltha,common,ofagent --cover-html\
              --cover-html-dir=tmp/cover

utest-with-coverage: venv protos
	@ echo "Executing all unit tests and producing coverage results"
	@ . ${VENVDIR}/bin/activate && nosetests $(COVERAGE_OPTS) pyvoltha/tests/utests

clean:
	find . -name '*.pyc' | xargs rm -f
	find . -name 'coverage.xml' | xargs rm -f
	find . -name 'nosetests.xml' | xargs rm -f
	make -C pyvoltha/protos clean
	rm -rf PyVoltha.egg-info
	rm -rf dist

distclean: clean
	rm -rf ${VENVDIR}

purge-venv:
	rm -fr ${VENVDIR}

rebuild-venv: purge-venv venv

venv: ${VENVDIR}/.built

${VENVDIR}/.built:
	@ $(VENV_BIN) ${VENV_OPTS} ${VENVDIR}
	@ $(VENV_BIN) ${VENV_OPTS} --relocatable ${VENVDIR}
	@ . ${VENVDIR}/bin/activate && \
	    pip install --upgrade pip; \
	    if ! pip install -r requirements.txt; \
	    then \
	        echo "On MAC OS X, if the installation failed with an error \n'<openssl/opensslv.h>': file not found,"; \
	        echo "see the BUILD.md file for a workaround"; \
	    else \
	        uname -s > ${VENVDIR}/.built; \
	    fi
	@ $(VENV_BIN) ${VENV_OPTS} --relocatable ${VENVDIR}


flake8: $(DIRS_FLAKE8)

# end file
