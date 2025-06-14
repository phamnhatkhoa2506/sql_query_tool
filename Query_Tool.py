import streamlit as st
from loguru import logger
from dotenv import load_dotenv

import sys
sys.path.append(r"E:\Python\sql_query_tool")

from models.llms import load_llm
from db.port import DEFAULT_PORT
from db.connection import connect_to_db
from agent.action import (
    write_query, 
    execute_query, 
    generate_answer, 
    graph,
    config
)

def setup_page() -> None:
    st.set_page_config(
        page_title="SQL Query Chat",
        page_icon="🖊",
        layout="centered"
    )

    st.session_state["is_memory_saving"] = False


def setup_sidebar() -> None:
    with st.sidebar:
        model_selectbox = st.selectbox(
            "Choose model",
            ["gemini-2.0-flash", "gpt-3.5-turbo", "gpt-4o"]
        )
        st.session_state.model_name = model_selectbox

        temp_slider = st.slider(
            "Choose temperature",
            0.0, 1.0
        )
        st.session_state.temp = temp_slider

        max_tokens_input = st.number_input(
            "Enter max tokens",
            100, 1000
        )
        st.session_state.max_tokens = max_tokens_input

        st.button("Save Change", on_click=handle_load_model)

        if "model_status_msg" in st.session_state:
            st.write(st.session_state.model_status_msg)
    

def setup_main() -> None:
    left_col, right_col = st.columns(2)

    # Left column
    with left_col:
        dbms = st.selectbox("DBMS", ["MySQL", "PostgresSQL", "SQLite"])
        st.session_state["dbms"] = dbms

        port = st.text_input(
            "Port", 
            placeholder="Enter your port",
            value=DEFAULT_PORT[st.session_state["dbms"]]
        )
        st.session_state["port"] = port

        db_name = st.text_input("Database", placeholder="Enter your database")
        st.session_state["db_name"] = db_name

    # Right column
    with right_col:
        host = st.text_input("Host", placeholder="Enter your host")
        st.session_state["host"] = host

        user = st.text_input("User", placeholder="Enter your user")
        st.session_state["user"] = user

        password = st.text_input("Password", placeholder="Enter your password", type="password")
        st.session_state["password"] = password

    # Button to handle connect db
    st.button("Connect", icon="🎁", on_click=handle_connect_db)

    # Notification about database connection 
    if "db_connect_status_msg" in st.session_state:
        st.write(st.session_state.db_connect_status_msg)

    st.divider()

    # Saving mode
    st.session_state["is_memory_saving"] = st.toggle("Saving")
 
    # Prompt
    st.session_state["user_prompt"] = st.chat_input(placeholder="Enter your prompt", on_submit=handle_user_prompt)
    st.button("Ask", icon="🤖", on_click=handle_user_prompt)

    # SQL Query answer text areas
    st.text_area(
        "SQL query", 
        key="1",
        value=st.session_state["sql_query"] if "sql_query" in st.session_state else ""
    )
    
    # Confirm execute modal
    if st.session_state.get("confirm_execute_modal", False):
        confirm_execute()

    # Bot answer text areas
    st.text_area(
        "Bot answer", 
        key="2",
        value=st.session_state["bot_ans"] if "bot_ans" in st.session_state else ""
    )


def handle_connect_db() -> None:
    if "llm" not in st.session_state:
        error_model_loading()
        st.session_state["model_status_msg"] = "Model hasn't loaded yet"
        st.session_state["db_connect_status_msg"] = "Model hasn't loaded yet"
        return 
    
    try: 
        db = connect_to_db(
            st.session_state["dbms"],
            st.session_state["db_name"],
            st.session_state["host"],
            st.session_state["port"],
            st.session_state["user"],
            st.session_state["password"],
        )
        st.session_state["db"] = db

        st.balloons()
        logger.success("Connect to database succesfully")
        st.session_state["db_connect_status_msg"] = "Connected Successfully"
    except Exception as e:
        logger.error("Connect to database failed " + str(e))
        st.session_state["db_connect_status_msg"] = "Connected Failed. Retry!: " + str(e)


def handle_load_model() -> None:
    try: 
        llm = load_llm(
            st.session_state["model_name"],
            st.session_state["temp"],
            st.session_state["max_tokens"]
        )

        st.session_state["llm"] = llm
        st.session_state["model_status_msg"] = f"✅ Load model {st.session_state.model_name} successfully!"

        st.snow()
        logger.success(f"Load model {st.session_state.model_name} succesfully!")
    except Exception as e:
        st.session_state["model_status_msg"] = "❌ Submit model failed. Retry!"
        logger.error("Submit model failed. Retry! " + str(e))

        error_modal("Submit model failed. Retry! " + str(e))


def handle_user_prompt() -> None:
    if "llm" not in st.session_state:
        error_model_loading()
        return
    if "db" not in st.session_state:
        error_db_connection()
        return

    if not st.session_state["is_memory_saving"]:
        query = write_query(
            {"question": st.session_state["user_prompt"]}
        )["query"]
        st.session_state["sql_query"] = query

        result = execute_query(
            {"query": query}
        )["result"]

        answer = generate_answer(
            {
                "question": st.session_state["user_prompt"],
                "query": query,
                "result": result
            }
        )["answer"]
        st.session_state["bot_ans"] = answer
    else:
        for step in graph.stream(
            {"question": st.session_state["user_prompt"]},
            config,
            stream_mode="updates",
        ):
            if 'write_query' in step:
                st.session_state["sql_query"] = step['write_query']['query']

        st.session_state["confirm_execute_modal"] = True


def handle_confirm_execute():
    for step in graph.stream(None, config, stream_mode="updates"):
        if 'generate_answer' in step:
            st.session_state["bot_ans"] = step['generate_answer']['answer']
 
    st.session_state["confirm_execute_modal"] = False 


def handle_cancel_execute():
    st.session_state["confirm_execute_modal"] = False 


@st.dialog("Confirm execute")
def confirm_execute() -> None:
    st.write("Continue to execute query?")

    left_col, right_col = st.columns(2)
    with left_col:
        if st.button("Yes", on_click=handle_confirm_execute):
            st.rerun()
    
    with right_col:
        if st.button("No", on_click=handle_cancel_execute):
            st.rerun()
    

@st.dialog('No database')
def error_db_connection() -> None:
    st.write("You have to connect to a databse")


@st.dialog('No model')
def error_model_loading() -> None:
    st.write("You have to save change a model")

@st.dialog('Error')
def error_modal(msg: str) -> None:
    st.write(msg)


def main() -> None:
    # Load environment variables
    load_dotenv()
    
    # Setup page
    setup_page()

    # Setup sidebar
    setup_sidebar()

    # Setup main part
    setup_main()

    
if __name__ == '__main__':
    main()
