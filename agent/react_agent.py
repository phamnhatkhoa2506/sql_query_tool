import re
import ast
import streamlit as st
from langgraph.prebuilt import create_react_agent
from langchain.agents.agent_toolkits import create_retriever_tool
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_core.messages import HumanMessage
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_google_genai import GoogleGenerativeAIEmbeddings


def query_as_list(db: any, query: str):
    res = db.run(query)
    res = [el for sub in ast.literal_eval(res) for el in sub if el]
    res = [re.sub(r"\b\d+\b", "", string).strip() for string in res]
    return list(set(res))


def get_agent_executor() -> any:
    toolkit = SQLDatabaseToolkit(
        db=st.session_state["db"], 
        llm=st.session_state["llm"]
    )

    tools = toolkit.get_tools()

    system_message = """
    You are an agent designed to interact with a SQL database.
    Given an input question, create a syntactically correct {dialect} query to run,
    then look at the results of the query and return the answer. Unless the user
    specifies a specific number of examples they wish to obtain, always limit your
    query to at most {top_k} results.

    You can order the results by a relevant column to return the most interesting
    examples in the database. Never query for all the columns from a specific table,
    only ask for the relevant columns given the question.

    You MUST double check your query before executing it. If you get an error while
    executing a query, rewrite the query and try again.

    DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the
    database.

    To start you should ALWAYS look at the tables in the database to see what you
    can query. Do NOT skip this step.

    Then you should query the schema of the most relevant tables.
    """.format(
        dialect=st.session_state["db"].dialect,
        top_k=5,
    )

    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

    vector_store = InMemoryVectorStore(embeddings)

    # _ = vector_store.add_texts(authors + fullnames)
    retriever = vector_store.as_retriever(search_kwargs={"k": 5})
    description = (
        "Use to look up values to filter on. Input is an approximate spelling "
        "of the proper noun, output is valid proper nouns. Use the noun most "
        "similar to the search."
    )
    retriever_tool = create_retriever_tool(
        retriever,
        name="search_proper_nouns",
        description=description,
    )

    suffix = (
        "If you need to filter on a proper noun like a Name, you must ALWAYS first look up "
        "the filter value using the 'search_proper_nouns' tool! Do not try to "
        "guess at the proper name - use this function to find similar ones."
    )
    system = f"{system_message}\n\n{suffix}"

    tools.append(retriever_tool)

    agent_executor = create_react_agent(st.session_state["llm"], tools, prompt=system)

    return agent_executor