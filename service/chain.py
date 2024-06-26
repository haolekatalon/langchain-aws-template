from langchain.memory import DynamoDBChatMessageHistory
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain.prompts import (
    ChatPromptTemplate, 
    MessagesPlaceholder, 
)
from langchain_core.runnables import (
    RunnableLambda,
    RunnableParallel,
)
from langchain_core.runnables.history import RunnableWithMessageHistory

import utils
import config
import os
from uuid import uuid4
from operator import itemgetter

def run(api_key: str, session_id: str, prompt: str):
    """This is the main function that executes the prediction chain.
    Updating this code will change the predictions of the service.

    Args:
        api_key: api key for the LLM service, OpenAI used here
        session_id: session id key to store the history
        prompt: prompt question entered by the user

    Returns:
        The prediction from LLM
    """
    
    # create a session_id for new conversation
    if not session_id:
        session_id = str(uuid4())

    SECRETS = utils.get_secrets()
    OPENAI_API_KEY = SECRETS["openai-api-key"]
    PINECONE_INDEX = SECRETS["pinecone-index"]
    PINECONE_API_KEY = SECRETS["pinecone-api-key"]
    PINECONE_ENVIRONMENT = SECRETS["pinecone-environment"]
    # for methods that use env vars
    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
    os.environ["PINCEONE_INDEX"] = PINECONE_INDEX
    os.environ["PINECONE_API_KEY"] = PINECONE_API_KEY
    os.environ["PINECONE_ENVIRONMENT"] = PINECONE_ENVIRONMENT

    # vectorstore
    vectorstore = PineconeVectorStore.from_existing_index(
        PINECONE_INDEX, 
        OpenAIEmbeddings(),
    )
    retriever = vectorstore.as_retriever()
    
    # RAG answer synthesis prompt
    template = """Answer the question based only on the following context, return links, if there's any:
    <context>
    {context}
    </context>"""
    ANSWER_PROMPT = ChatPromptTemplate.from_messages(
        [
            ("system", template),
            MessagesPlaceholder(variable_name="history"),
            ("user", "{question}"),
        ]
    )

    _search_query = RunnableLambda(itemgetter("question"))

    _inputs = RunnableParallel(
        {
            "question": lambda x: x["question"],
            "context": _search_query | retriever,
            "history": lambda x: x["history"]
        }
    )

    llm = ChatOpenAI(temperature=0, openai_api_key=OPENAI_API_KEY)

    chain = _inputs | ANSWER_PROMPT | llm | StrOutputParser()

    # wrap the chain with message history
    chain_with_history = RunnableWithMessageHistory(
        chain,
        lambda session_id: DynamoDBChatMessageHistory(
            table_name=config.config.DYNAMODB_TABLE_NAME,
            session_id=session_id
            ),
        input_messages_key="question",
        history_messages_key="history",
    )
    
    response = chain_with_history.invoke({'question': prompt}, {'configurable': {'session_id': session_id}})
    
    return response, session_id

