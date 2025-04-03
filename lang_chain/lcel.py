# pip install requirements
# pip install langchain==0.1.0 python-dotenv==1.0.0 ollama

import os
from operator import itemgetter
from typing import Dict, List, Optional, Union

from dotenv import load_dotenv
from langchain_community.llms import Ollama
from langchain.prompts import ChatPromptTemplate
from langchain.schema import AIMessage, HumanMessage, StrOutputParser, SystemMessage
from langchain.schema.runnable import Runnable, RunnablePassthrough
from langchain.schema.runnable.config import RunnableConfig

# Load environment variables (though Ollama doesn't need API keys)
load_dotenv()

# Initialize Ollama - using llama2 as default, but you can change to any model you've pulled
# Make sure you've run `ollama pull llama2` or your preferred model first
model = Ollama(model="gemma3:1b")

# Basic chain
prompt = ChatPromptTemplate.from_template(
    "Tell me a short joke about {topic}"
)
output_parser = StrOutputParser()

chain = prompt | model | output_parser

result = chain.invoke({"topic": "Star Wars"})
print("Basic joke chain result:", result, "\n")

# More complex chain with system message
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a helpful AI assistant. You answer briefly and in a funny way."),
        ("human", "Tell me a joke about {topic}"),
    ]
)

chain = prompt | model | output_parser

result = chain.invoke({"topic": "Star Wars"})
print("System message chain result:", result, "\n")

# Dictionary input with RunnablePassthrough
chain = (
    {"topic": RunnablePassthrough()}
    | prompt
    | model
    | output_parser
)

result = chain.invoke("beets")
print("RunnablePassthrough chain result:", result, "\n")

# Multiple inputs
template = """Tell me a joke about {topic}.
Make it in the style of {style}.
"""
prompt = ChatPromptTemplate.from_template(template)

chain = prompt | model | output_parser

result = chain.invoke({"topic": "Star Wars", "style": "Master Yoda"})
print("Multiple inputs chain result:", result, "\n")

# Using itemgetter for multiple inputs
chain = (
    {"topic": itemgetter("topic"), "style": itemgetter("style")}
    | prompt
    | model
    | output_parser
)

result = chain.invoke({"topic": "Star Wars", "style": "Master Yoda", "other": "ignored"})
print("Itemgetter chain result:", result, "\n")

# Using RunnablePassthrough for multiple inputs
chain = (
    RunnablePassthrough.assign(style=lambda x: "a " + x["style"])
    | prompt
    | model
    | output_parser
)

result = chain.invoke({"topic": "Star Wars", "style": "Master Yoda"})
print("RunnablePassthrough.assign chain result:", result, "\n")

# Branching and merging
planner = (
    ChatPromptTemplate.from_template("Generate an argument about: {input}")
    | model
    | StrOutputParser()
    | {"base_response": RunnablePassthrough()}
)

arguments_for = (
    ChatPromptTemplate.from_template(
        "List the pros or positive aspects of: {base_response}"
    )
    | model
    | StrOutputParser()
)

arguments_against = (
    ChatPromptTemplate.from_template(
        "List the cons or negative aspects of: {base_response}"
    )
    | model
    | StrOutputParser()
)

final_responder = (
    ChatPromptTemplate.from_messages(
        [
            ("ai", "{original_response}"),
            ("human", "What are the pros?\n{results_for}\n\nWhat are the cons?\n{results_against}"),
            ("system", "Generate a final response given the critique"),
        ]
    )
    | model
    | StrOutputParser()
)

chain = (
    planner
    | {
        "results_for": arguments_for,
        "results_against": arguments_against,
        "original_response": itemgetter("base_response"),
    }
    | final_responder
)

result = chain.invoke({"input": "scrum meetings"})
print("Branching and merging chain result:", result, "\n")

# Custom functions
def length_function(text):
    return len(text)

def _multiple_length_function(text1, text2):
    return len(text1) * len(text2)

def multiple_length_function(_dict):
    return _multiple_length_function(_dict["text1"], _dict["text2"])

prompt = ChatPromptTemplate.from_template("what is {a} + {b}")

chain1 = prompt | model

# chain = {
#     "a": itemgetter("foo") | length_function,
#     "b": {"text1": itemgetter("foo"), "text2": itemgetter("bar")} | multiple_length_function,
# } | prompt | model | output_parser
#
# result = chain.invoke({"foo": "bars", "bar": "gahs"})
# print("Custom functions chain result:", result, "\n")

# LCEL with chat models
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a helpful assistant. Answer all questions to the best of your ability."),
        ("human", "Explain the plot of {movie} in a short way"),
    ]
)

chain = prompt | model | output_parser

result = chain.invoke({"movie": "Return of Jedi"})
print("Chat model chain result:", result, "\n")

# Interface
def parse_or_fix(text: str, config: Optional[RunnableConfig] = None):
    fixing_chain = (
        ChatPromptTemplate.from_template(
            "Fix the following text:\n\n```text\n{input}\n```\nError: {error}"
            " Don't narrate, just respond with the fixed data."
        )
        | model
        | StrOutputParser()
    )
    for _ in range(3):
        try:
            return int(text)
        except ValueError as e:
            text = fixing_chain.invoke({"input": text, "error": e}, config)
    return "Failed to parse"

result = parse_or_fix("45")
print("Parse or fix (valid input):", result)

result = parse_or_fix("forty five")
print("Parse or fix (invalid input):", result)