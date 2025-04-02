# langchain_ollama_modern.py
from langchain.memory import ConversationBufferMemory
from langchain_community.llms.ollama import Ollama
from langchain_core.prompts import PromptTemplate
from langchain_core.memory import BaseMemory
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_community.utilities import WikipediaAPIWrapper

# Initialize Ollama - make sure you've downloaded your preferred model first
# Example: run `ollama pull llama2` in your terminal before executing this script
llm = Ollama(model="llama3.2:1b", temperature=0.7)  # Can use mistral, llama2, or others

# Initialize Wikipedia wrapper
wiki = WikipediaAPIWrapper()

# Memory for conversation history
memory = ConversationBufferMemory()

# Create prompt templates
topic_prompt = PromptTemplate.from_template(
    "Give me a brief overview of {topic}?"
)

wiki_prompt = PromptTemplate.from_template(
    "Provide additional details about {topic} based on this research: {wiki_research}"
)

quiz_prompt = PromptTemplate.from_template(
    """Based on our discussion about {topic} and this history: {chat_history}, 
    create a 3-question quiz to test understanding."""
)

# Create chains using the new Runnable protocol
topic_chain = (
        {"topic": RunnablePassthrough()}
        | topic_prompt
        | llm
        | StrOutputParser()
)

wiki_chain = (
        {"topic": RunnablePassthrough(), "wiki_research": RunnablePassthrough()}
        | wiki_prompt
        | llm
        | StrOutputParser()
)

quiz_chain = (
        {"topic": RunnablePassthrough(), "chat_history": RunnablePassthrough()}
        | quiz_prompt
        | llm
        | StrOutputParser()
)


def run_demo(topic):
    # Run Wikipedia research
    wiki_research = wiki.run(topic)

    # Get initial topic overview
    topic_overview = topic_chain.invoke(topic)

    # Get wiki-enhanced details
    wiki_details = wiki_chain.invoke({"topic": topic, "wiki_research": wiki_research})

    # Get chat history from memory
    chat_history = memory.load_memory_variables({})["history"]

    # Generate quiz
    quiz = quiz_chain.invoke({"topic": topic, "chat_history": chat_history})

    # Save to memory
    memory.save_context({"input": topic}, {"output": f"{topic_overview}\n{wiki_details}"})

    # Print results
    print("\n=== TOPIC OVERVIEW ===")
    print(topic_overview)

    print("\n=== WIKI ENHANCED DETAILS ===")
    print(wiki_details)

    print("\n=== GENERATED QUIZ ===")
    print(quiz)

    print("\n=== WIKIPEDIA RESEARCH ===")
    print(wiki_research)


if __name__ == "__main__":
    # Check if Ollama is running
    try:
        # Test connection to Ollama
        llm.invoke("test")
    except Exception as e:
        print("Error connecting to Ollama. Please ensure:")
        print("1. Ollama is installed (https://ollama.ai/)")
        print("2. You've downloaded a model (e.g., `ollama pull llama2`)")
        print("3. The Ollama server is running")
        exit(1)

    user_topic = input("Enter a topic you'd like to learn about: ")
    run_demo(user_topic)