# This file is used to abstract away commands we often need to run.
# For example, we can run `make build-push-deploy` to build our Docker image,
# push it to the registry, and deploy it to Azure Container Apps, all in one command.

include .env

IMAGE_NAME := ${CONTAINER_REGISTRY}.azurecr.io/llmops-app-${USER_NAME}

.PHONY: help
help:
	@echo "Available commands:"
	@echo "  run-local: Run the app locally"
	@echo "  docker-build: Build the Docker image"
	@echo "  docker-push: Push the Docker image to the registry"
	@echo "  docker-run: Run the Docker image locally"
	@echo "  container-app-deploy:  Deploy the Azure Container App"
	@echo "  build-push-deploy: Build, push, and deploy the Container App"

.PHONY: run-local
run-local:
	streamlit run src/llmops_training/news_reader/app/app.py

.PHONY: docker-build
docker-build:
	docker build --platform linux/amd64 -t $(IMAGE_NAME) .

.PHONY: docker-push
docker-push:
	az acr login --name ${CONTAINER_REGISTRY}
	docker push $(IMAGE_NAME)

.PHONY: docker-run
docker-run:
	docker run --env-file .env --rm -p 8081:8081 $(IMAGE_NAME)

# All container apps must be deployed in an Azure Container Apps environment. 
# For now, we have created this resource for you. 
.PHONY: deploy-app-environment
deploy-app-environment:
	az containerapp env create --name ${APP_ENVIRONMENT} --resource-group ${RESOURCE_GROUP} \
	--location westeurope \
	--logs-workspace-id ${LOG_ANALYTICS_WORKSPACE_ID} \
  	--logs-workspace-key ${LOG_ANALYTICS_WORKSPACE_KEY}

.PHONY: container-app-deploy
container-app-deploy:
	az containerapp up \
		--name llmops-app-${USER_NAME} \
		--resource-group ${RESOURCE_GROUP} \
		--location westeurope \
		--image ${IMAGE_NAME} \
		--target-port 8081 \
		--ingress external \
		--registry-username ${CONTAINER_REGISTRY_USERNAME} \
		--registry-password ${CONTAINER_REGISTRY_PASSWORD} \
		--env-vars \
		"APPLICATIONINSIGHTS_CONNECTION_STRING=${APPLICATIONINSIGHTS_CONNECTION_STRING}" \
		"AZURE_OPENAI_ENDPOINT=${AZURE_OPENAI_ENDPOINT}" \
		"AZURE_OPENAI_API_KEY=${AZURE_OPENAI_API_KEY}" \
		"AZURE_OPENAI_API_VERSION=${AZURE_OPENAI_API_VERSION}" \
		"AZURE_OPENAPI_DEPLOYMENT_NAME=o3-mini"

.PHONY: build-push-deploy
build-push-deploy: docker-build docker-push container-app-deploy
