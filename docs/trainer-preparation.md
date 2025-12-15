# Traininer preparation instructions 🧑‍🏫

Are you a participant of the training? Then you can skip this part and hop over to the next notebook.

In order to get all infra in place for the training, you need to provision the following in Azure.
Make sure you create a new Azure Resource Group for the training at hand, in which you can provision these resources.
Infra can be provisioned manually. Remove the Resource Group afterwards.

... complete the steps below or use the [`llmops-training`](https://github.com/godatadriven/gdd_sso/blob/main/azure_ad/projects/llmops_training_azure.yaml) resource group that was created already with [ggd_sso](https://github.com/godatadriven/gdd_sso). Don't forget to add parcipants in the `.yaml` file to grant them access to the Azure resource group.

- [ ] Create Azure Resource Group (e.g., `llmops-training-rg`)
- [ ] Create Azure OpenAI Service instance
- [ ] Deploy required models (e.g., `o3-mini`, `gpt-5`, ~text-embedding-ada-002~)
- [ ] Create Azure Container Registry
  - [ ] Run `az acr update -n $CONTAINER_REGISTRY --admin-enabled true`
- [ ] Create Azure Application Insights instance
- [ ] Create Azure Key Vault
- [ ] Create Azure Machine Learning Workspace
- [ ] ~Create Azure Container App (with Azure Container App Environment)~ (participants do this during the training)
  - [ ] Enable Identity > System Assigned Identity (see [Stack Overflow](https://stackoverflow.com/questions/76610215/unable-to-update-image-of-containerapp-with-az-up-command))
- [ ] Create Service Principal with roles:
  - Contributor (on Resource Group)
  - AcrPush (on Container Registry)
  - Container Apps Contributor
- [ ] Add the following to GitHub Actions repository secrets:
  - `AZURE_CREDENTIALS` - Service principal credentials in JSON format
  - `REGISTRY_USERNAME` - Container Registry username (service principal client ID)
  - `REGISTRY_PASSWORD` - Container Registry password (service principal secret)
  - `SUBSCRIPTION_ID` - Azure Subscription ID
- [ ] Add participants via `gdd_sso` (e.g. [https://github.com/godatadriven/gdd_sso/blob/87818a8aa3de09fd639581422ebaaa95818f13f8/azure_ad/projects/llmops_training_azure.yaml](https://github.com/godatadriven/gdd_sso/blob/87818a8aa3de09fd639581422ebaaa95818f13f8/azure_ad/projects/llmops_training_azure.yaml))
  - ~Contributor (on Resource Group)~
  - AzureML Data Scientist (go to Azure ML resource in Azure > IAM > AzureML Data Scientist > Add participant emails)
    - or simply:
      ```
      az role assignment create --assignee <user-email-or-object-id> \  
      --role "AzureML Data Scientist" \  
      --scope /subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.MachineLearningServices/workspaces/$WORKSPACE_NAME
      ```
  - Azure OpenAI Service User
  - Azure Container Registry contributor
    - like above, or simply:

      ```
      az role assignment create --assignee <user-email-or-object-id> --role "Container Registry Repository Contributor" --scope /subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.MachineLearningServices/workspaces/$WORKSPACE_NAME
      ```
  - Also add AcrPush role if above doesn't work for a participant.
  - Container Apps Contributor
    - add via CLI or ClickOps
- [ ] Increase Azure OpenAI quota if necessary during training
  - Check Token Per Minute (TPM) limits for deployed models

> [!NOTE]
> Data comes from a [Hugging Face dataset](https://huggingface.co/datasets/RealTimeData/bbc_news_alltime). It is loaded dynamically in the code itself. No need to prep anything!
