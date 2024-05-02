import asyncio
import os
from typing import Any, List

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import RawVectorQuery
from dotenv import load_dotenv

import semantic_kernel as sk
from plugins.QueryDb import queryDb as plugin
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.planning import SequentialPlanner
from src.aoai.azure_openai import AzureOpenAIManager
from src.prompts import get_intent_prompt
from utils.ml_logging import get_logger


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(ROOT_DIR+'/.env', override=True)

service_endpoint = os.getenv("AZURE_AI_SEARCH_SERVICE_ENDPOINT")
key = os.getenv("AZURE_SEARCH_ADMIN_KEY")
credential = AzureKeyCredential(key)
index_name = "query-dev-index"
logger = get_logger()

search_client = SearchClient(service_endpoint, index_name, credential=credential)
search_query = SearchClient(service_endpoint, index_name, credential=credential)
az_client = AzureOpenAIManager()

def get_user_query() -> str:
    """Prompt the user for a query and return it."""
    return input("\nPlease enter your question: ")

async def create_plan(planner: SequentialPlanner, input: str) -> Any:
    """Create a plan using the provided planner and input."""
    return await planner.create_plan(goal=input)

async def invoke_plan(sequential_plan: Any) -> Any:
    """Invoke the provided sequential plan."""
    return await sequential_plan.invoke()

async def run_texttosql(nlp_input: str) -> Any:
    """Run the text to SQL conversion process."""
    kernel = sk.Kernel()
    deployment, api_key, endpoint = sk.azure_openai_settings_from_dot_env()
    azure_text_service = AzureChatCompletion(deployment_name=deployment, endpoint=endpoint, api_key=api_key)
    kernel.add_text_completion_service("azure_text_completion", azure_text_service)
    plugins_directory = "plugins"
    kernel.import_semantic_plugin_from_directory(plugins_directory, "nlpToSqlPlugin")
    kernel.import_plugin(plugin.QueryDbPlugin(os.getenv("CONNECTION_STRING")), plugin_name="QueryDbPlugin")
    planner = SequentialPlanner(kernel)
    ask = f"Create a SQL query according to the following request: {nlp_input} and query the database to get the result."
    plan = await create_plan(planner, ask)
    result = await invoke_plan(plan)
    logger.info(f'\nUser ASK: {nlp_input}\nResponse: {result}\n')
    for index, step in enumerate(plan._steps):
        logger.info(f"Step: {index}\nDescription: {step.description}\nFunction: {step.plugin_name + '.' + step._function.name}")
        if len(step._outputs) > 0:
            output = result[step._outputs[0]].replace('\n', '\n  ')
            logger.info(f"Output:\n{output}")
    return result.result

def main():
    """Main function to handle user queries and intents."""
    while True:
        conversation_history: List[str] = []
        user_query = get_user_query()
        if user_query.lower() in ["exit", "quit"]:
            logger.info("Exiting the program. Goodbye!")
            break
        prompt_intent = get_intent_prompt(conversation_history, user_query)
        intent = az_client.generate_chat_response(
            conversation_history=conversation_history,
            query=prompt_intent,
            system_message_content="You are an AI assistant designed to detect the intent from the user's query.",
            max_tokens=50,
        )
        if intent == 'how_to':
            handle_how_to_intent()
        elif intent == 'database':
            asyncio.run(run_texttosql(user_query))
        elif intent == 'how_to_database':
            logger.info("Handling 'how_to_database' intent...")
        else:
            logger.info("Intent not found. Please try again.")

def handle_how_to_intent():
    """Handle 'how_to' intent."""
    search_query = "Identify players who played more than 100 games, have an OPS (On-base Plus Slugging) higher than .900, and have less than 10 errors in a season."
    search_vector = az_client.generate_embedding(input_text=search_query)
    r = search_client.search(
        search_query,
        top=5,
        vector_queries=[RawVectorQuery(vector=search_vector, k=50, fields="table_vector")],
        query_type="semantic",
        semantic_configuration_name="query-index-semantic-config",
        query_language="en-us",
    )
    for doc in r:
        content = doc["table_content"].replace("\n", " ")[:1000]
        table_name = doc["table_name"]
        score = doc["@search.score"]
        reranker_score = doc["@search.reranker_score"]
        logger.info(f"Table Name: {table_name}\nScore: {score}\nReranker Score: {reranker_score}\nContent: {content}\n{'-' * 50}")

if __name__ == "__main__":
    main()