import re
import azure.functions as func
import datetime
import json
import logging
import os
from openai import AzureOpenAI


from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from llama_index.vector_stores.azureaisearch import AzureAISearchVectorStore
from llama_index.vector_stores.azureaisearch import IndexManagement
from llama_index.core.settings import Settings
from llama_index.readers.azstorage_blob import AzStorageBlobReader
from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
from llama_index_service import LlamaIndexService

app = func.FunctionApp()

@app.function_name(name="AskQuestion")
@app.route(route="AskQuestion", auth_level=func.AuthLevel.ANONYMOUS)
@app.cosmos_db_input(arg_name="inputDocuments", 
                     database_name="aoaidb",
                     container_name="facts",
                     connection="MyAccount_COSMOSDB")
def AskQuestion(inputDocuments: func.DocumentList, req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    # Get the question from the request parameters
    raw_question = req.params.get('question')

    # Check if the question is provided
    if not raw_question:
        return func.HttpResponse(
            "Please pass a question on the query string",
            status_code=400
        )

    # Remove all HTML tags from the question
    clean_question = re.sub('<.*?>', '', raw_question)

    if inputDocuments:
        # TODO - Create an AI search client to connect to the resource
        search_endpoint = os.environ["AISearchEndpoint"]
        search_key = os.environ["AISearchAPIKey"]
        search_index = os.environ["AISearchIndexName"]
        search_client = SearchClient(endpoint=search_endpoint, index_name=search_index, credential=AzureKeyCredential(search_key))
        client = AzureOpenAI(
            azure_endpoint = os.getenv("AOAI_ENDPOINT"), 
            api_key=os.getenv("AOAI_KEY"),  
            api_version="2024-02-15-preview"
        )

        #Join all the facts into a single string
        facts = "These are the local experts." + "\n".join([doc.data['fact'] for doc in inputDocuments])                        
           
        # TODO - Create a text embedding of the question from the OpenAI Model.  
        question_embedding = client.create_text_embedding(clean_question)

        # TODO - Create a vectorized query to sent to AI Search

        # TODO - Search the AI search index for the top 5 results

        # TODO - Join all the facts from the AI search results into a single string

        # TODO - Add the AI search results to the facts

        message_text = [{"role":"system","content": facts}, 
                        {"role":"user","content": clean_question + 
                         ". Be as helpful as possible in connecting the above local experts in the response. State the response as a gramatically correct and complete summary."}]

        completion = client.chat.completions.create(
            messages = message_text,
            model = os.environ.get("MODEL", "gpt35"),
            temperature = float(os.environ.get("TEMPERATURE", "0.7")), 
            max_tokens = int(os.environ.get("MAX_TOKENS", "800")),
            top_p = float(os.environ.get("TOP_P", "0.95")),
            frequency_penalty = float(os.environ.get("FREQUENCY_PENALTY", "0")),
            presence_penalty = float(os.environ.get("PRESENCE_PENALTY", "0")),
            stop = os.environ.get("STOP", "None")
        )

    return func.HttpResponse(
        completion.choices[0].message.content,
        status_code=200
        )



# TODO - CHALLENGE 2 - After AI Search is connected, add a trigger to the function to process the blob and chunk the file
@app.blob_trigger(arg_name="indexBlob", path="dsl-content",
                               connection="function_storage_connection") 
def ChunkFileTrigger(indexBlob: func.InputStream):
    
    llama_index_service: LlamaIndexService = LlamaIndexService()
    blob_name: str = indexBlob.name.split("/")[-1]    
    aoai_model_name: str = os.environ["OpenAIModelName"]
    aoai_api_key: str = os.environ["OpenAIAPIKey"]
    aoai_endpoint: str = os.environ["OpenAIEndpoint"]
    aoai_api_version: str = os.environ["OpenAIAPIVersion"]
    embed_model = __create_embedding_model__()
    vector_store = __create_vector_store__()
    blob_loader = __create_blob_loader__(blob_name)
    
    llama_index_service.index_documents(
        aoai_model_name,
        aoai_api_key,
        aoai_endpoint,
        aoai_api_version,
        vector_store,
        embed_model,
        blob_loader
    )

# Create the Azure AI Search Index
def __create_search_index__() -> SearchIndexClient: 
    # TODO - Create the Azure AI Search Index
    return None

# Create the Azure AI Search Vector Store
def __create_vector_store__() -> AzureAISearchVectorStore:
    # TODO - Create the Azure AI Search Vector Store
    return None

# Create the Azure OpenAI Embedding Model
def __create_embedding_model__() -> AzureOpenAIEmbedding:
    # TODO - Create the Azure OpenAI Embedding Model
    return None

# Create the Azure Blob Loader
def __create_blob_loader__(blob_name: str) -> AzStorageBlobReader:
    container_name: str = os.environ["StorageAccountContainerName"]
    account_url: str = os.environ["StorageAccountUrl"]
    connection_string: str = os.environ["StorageAccountConnectionString"]
    
    return AzStorageBlobReader(
        container_name=container_name,
        blob=blob_name,
        account_url=account_url,
        connection_string=connection_string,
    )