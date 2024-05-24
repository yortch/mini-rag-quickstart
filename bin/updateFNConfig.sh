#!/bin/sh

export AOAI_KEY="<replace>"
export AOAI_ENDPOINT="https://jb-aoai-teams.openai.azure.com/"
export MyAccount_COSMOSDB="AccountEndpoint=<replace>"
export MODEL="gpt35"



az functionapp config appsettings set --name $AOAI_APP --resource-group $RG \
  --settings "AOAI_KEY=$AOAI_KEY" "AOAI_ENDPOINT=$AOAI_ENDPOINT" "MyAccount_COSMOSDB=$MyAccount_COSMOSDB" "MODEL=$MODEL"


