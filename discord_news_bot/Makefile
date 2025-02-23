# Load environment variables from .env if it exists
ifneq (,$(wildcard .env))
    include .env
    export
endif

# Default event file
EVENT ?= test_data/event.json  # Default event file

# Use Python 3.11 explicitly
PYTHON = python

# AWS CDK executable
CDK = cdk

.PHONY: install lint format test synth deploy all

install:
	@echo "Installing dependencies..."
	$(PYTHON) -m pip install -r requirements.txt
	$(PYTHON) -m pip install -r src/lambda/requirements.txt

lint:
	@echo "Running flake8 linting..."
	flake8 .

format:
	@echo "Running black formatter..."
	black .

test:
	@echo "Running pytest..."
	pytest

synth:
	@echo "Synthesizing CDK stack..."
	cd src/cdk && $(CDK) synth

invoke:
	@echo "Invoking DiscordNewsBot Lambda locally..."
	sam local invoke "DiscordNewsBotLambda" -e $(EVENT) --env-vars .env

deploy:
	@echo "Deploying CDK stack..."
	cd src/cdk && $(CDK) deploy --require-approval never --profile $(AWS_PROFILE) --region $(AWS_REGION)

all: install lint format test synth deploy
