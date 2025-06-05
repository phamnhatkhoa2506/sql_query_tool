import streamlit as st
from agent.react_agent import get_agent_executor

def setup_page() -> None:
    st.set_page_config(
        page_title="Agent",
        page_icon="🤖",
        layout="centered"
    )


def handle_bot_reply(question: str) -> None:
    messages = []
    for step in st.session_state["agent_executor"].stream(
        {"messages": [{"role": "user", "content": question}]},
        stream_mode="values",
    ):
        step["messages"][-1].pretty_print()
        messages.append(step["messages"][-1])

    with st.chat_message(name="ai"):
        st.write(messages[-1].content)
    st.session_state["messages"].append({"role": "ai", "content": messages[-1].content})


def main() -> None:
    # Setup page
    setup_page()

    # Init message history
    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    if "db" in st.session_state:
        st.session_state["agent_executor"] = get_agent_executor()

    # Display chat history
    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # Display input
    user_message = st.chat_input("Enter your question")
    if user_message:
       
        # Show user question
        with st.chat_message("user"):
            st.write(user_message)

        # Store message
        st.session_state["messages"].append({"role": "user", "content": user_message})

        if "db" in st.session_state:
            handle_bot_reply(user_message)
        else:
            with st.chat_message(name="ai"):
                msg = "You need to connect to a database"
                st.write(msg)
                st.session_state["messages"].append({"role": "ai", "content": msg})

if __name__ == '__main__':
    main()
