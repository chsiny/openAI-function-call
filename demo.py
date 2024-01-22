import json
import openai
import requests
import os
import desygner
from tenacity import retry, wait_random_exponential, stop_after_attempt
from termcolor import colored
from dotenv import load_dotenv

load_dotenv()

gpt_model = os.environ.get("GPT_MODEL")
api_key=os.environ.get("OPENAI_API_KEY")

@retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
def chat_completion_request(messages, tools=None, tool_choice=None, model=gpt_model):
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + api_key,
    }
    json_data = {"model": model, "messages": messages}
    if tools is not None:
        json_data.update({"tools": tools})
    if tool_choice is not None:
        json_data.update({"tool_choice": tool_choice})
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=json_data,
        )
        return response
    except Exception as e:
        print("Unable to generate ChatCompletion response")
        print(f"Exception: {e}")
        return e

def pretty_print_conversation(messages: str) -> None:
    """
    pretty print the message logs
    """

    role_to_color = {
        "system": "red",
        "user": "green",
        "assistant": "blue",
        "tool": "magenta",
    }
    
    for message in messages:
        if message["role"] == "system":
            print(colored(f"system: {message['content']}\n", role_to_color[message["role"]]))
        elif message["role"] == "user":
            print(colored(f"user: {message['content']}\n", role_to_color[message["role"]]))
        elif message["role"] == "assistant" and message.get("function_call"):
            print(colored(f"assistant: {message['function_call']}\n", role_to_color[message["role"]]))
        elif message["role"] == "assistant" and not message.get("function_call"):
            print(colored(f"assistant: {message['content']}\n", role_to_color[message["role"]]))
        elif message["role"] == "tool":
            print(colored(f"function ({message['name']}): {message['content']}\n", role_to_color[message["role"]]))

# list of functions
tools = [
    {
        "type": "function",
        "function" : {
            "name": "hello",
            "description": "say hi",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The text passed for saying hello"
                    }
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_invoices",
            "description": "Get Invoices",
            "parameters": {
                "type": "object",
                "properties": {
                    "company": {
                        "type": "string",
                        "description": "The company name, e.g. desygner",
                    }
                },
                "required": ["company"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_designs",
            "description": "Get design names of the company",
            "parameters": {
                "type": "object",
                "properties": {
                    "company": {
                        "type": "string",
                        "description": "The company name, e.g. Desygner",
                    }
                },
                "required": ["company"]
            },
        }
    },
]

def hello(text: str) -> str:
    """
    A simple test function to say hello with passed text
    """
    hello = "Hello, " + text

    return hello

def call_chatgpt_with_functions(messages: list(dict[str: str])) -> list(dict[str: str]):
    """
    ask chatgpt to call functions
    """

    # messages.append({"role": "system", "content": "Don't make assumptions about what values to plug into functions. Ask for clarification if a user request is ambiguous."})
    # messages.append({"role": "system", "content": "Perform function request for the user"})
    # messages.append({"role": "user", "content": "Hello, I would like to call the hello function passing the string 'It's me'"})

    # call chatgpt with config message and prompt
    chat_response = chat_completion_request(
        messages, tools=tools
    )

    wants_to_use_function = chat_response.json()["choices"][0]["finish_reason"] == "tool_calls"
    content = ""

    if wants_to_use_function:
        tool_call = chat_response.json()["choices"][0]["message"]["tool_calls"][0]
        if tool_call["function"]["name"] == "hello":
            arguments = tool_call["function"]["arguments"]
            content = hello(json.loads(arguments)["text"])

        if tool_call["function"]["name"] == "get_designs":
            arguments = tool_call["function"]["arguments"]
            content = desygner.get_designs(json.loads(arguments)["company"])

    messages.append(chat_response.json()["choices"][0]["message"])

    tool_message = {
            "role": "tool",
            "name": tool_call["function"]["name"],
            "content": content,
            "tool_call_id": tool_call["id"],
        }
    messages.append(tool_message)

    new_response = chat_completion_request(
        messages, tools=tools
    )

    messages.append(new_response.json()["choices"][0]["message"])

    return messages

messages = []
messages.append({"role": "system", "content": "Perform function request for the user"})
messages.append({"role": "user", "content": "I would like to get all the design names of Desygner"})

pretty_print_conversation(call_chatgpt_with_functions(messages))
