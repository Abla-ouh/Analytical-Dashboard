import os
from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph,START,END
from langgraph.graph.message import add_messages

class State(TypedDict):
  # Messages have the type "list". The `add_messages` function
    # in the annotation defines how this state key should be updated
    # (in this case, it appends messages to the list, rather than overwriting them)
  messages:Annotated[list,add_messages]

def chatbot(state:State):
  return {"messages":llm.invoke(state['messages'])}

if __name__ == "__main__":

    load_dotenv()

    llm_name = "qwen2.5:0.5b"
    llm = ChatOllama(model=llm_name)

    graph_builder=StateGraph(State)

    graph_builder.add_node("chatbot",chatbot)

    graph_builder.add_edge(START,"chatbot")

    graph_builder.add_edge("chatbot",END)

    graph=graph_builder.compile()

    while True:
        user_input=input("User: ")
        if user_input.lower() in ["quit","q"]:
            print("Good Bye")
            break
        for event in graph.stream({'messages':("user",user_input)}):
            print(event.values())
            for value in event.values():
                print(value['messages'])
                print("Assistant:",value["messages"].content)