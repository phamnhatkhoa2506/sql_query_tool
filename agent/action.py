import streamlit as st
from typing import Dict
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.tools.sql_database.tool import QuerySQLDatabaseTool
from schemas.state import State
from schemas.query_output import QueryOutput


system_message = """
Given an input question, create a syntactically correct {dialect} query to
run to help find the answer. Unless the user specifies in his question a
specific number of examples they wish to obtain, always limit your query to
at most {top_k} results. You can order the results by a relevant column to
return the most interesting examples in the database.

Never query for all the columns from a specific table, only ask for a the
few relevant columns given the question.

Pay attention to use only the column names that you can see in the schema
description. Be careful to not query for columns that do not exist. Also,
pay attention to which column is in which table.

Only use the following tables:
{table_info}
"""

user_prompt = "Question: {input}"

query_prompt_template = ChatPromptTemplate(
    [("system", system_message), ("user", user_prompt)]
)


def write_query(state: State) -> Dict[str, str]:
    """
        Generate SQL query to fetch information.
    """

    prompt = query_prompt_template.invoke(
        {
            "dialect": st.session_state["db"].dialect,
            "top_k": 10,
            "table_info": st.session_state["db"].get_table_info(),
            "input": state["question"],
        }
    )

    structured_llm = st.session_state["llm"].with_structured_output(QueryOutput)
    result = structured_llm.invoke(prompt)

    return {"query": result["query"]}


def execute_query(state: State):
    """
        Execute SQL query.
    """

    execute_query_tool = QuerySQLDatabaseTool(db=st.session_state["db"])
    return {"result": execute_query_tool.invoke(state["query"])}


def generate_answer(state: State):
    """
        Answer question using retrieved information as context.
    """
    prompt = (
        "Given the following user question, corresponding SQL query, "
        "and SQL result, answer the user question.\n\n"
        f'Question: {state["question"]}\n'
        f'SQL Query: {state["query"]}\n'
        f'SQL Result: {state["result"]}'
    )
    response = st.session_state["llm"].invoke(prompt)
    
    return {"answer": response.content}