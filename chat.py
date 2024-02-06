import json
import requests
import os
from desygner import *
from tenacity import retry, wait_random_exponential, stop_after_attempt
from termcolor import colored
from dotenv import load_dotenv


class ChatDesygner():
    def __init__(self) -> None:
        # Load configuration
        load_dotenv()
        self._gpt_model = os.environ.get("GPT_MODEL")
        self._api_key = os.environ.get("OPENAI_API_KEY")
        self._tools = TOOLS
        self.message = []
        self.message.append(
            {"role": "system", "content": "Perform function request for the user. Don't make assumptions about what values to plug into functions. Ask for clarification if a user request is ambiguous."}
        )

    def append_message(self, message):
        self.message.append(message)

    @retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
    def chat_completion_request(self, messages, tools=None, tool_choice=None):
        """
        Request OpenAI API
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self._api_key,
        }
        json_data = {"model": self._gpt_model, "messages": messages}
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

    def pretty_print_conversation(self, messages) -> None:
        """
        Pretty print the message logs
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

    def call_openai_function(self, message) -> list(dict[str, str]):
        """
        Ask ChatGPT to call OpenAI functions
        """
        self.append_message(message)
        chat_response = self.chat_completion_request(
            messages=self.message, tools=self._tools
        )

        wants_to_use_function = chat_response.json()["choices"][0]["finish_reason"] == "tool_calls"
        content = ""

        if wants_to_use_function:
            tool_call = chat_response.json()["choices"][0]["message"]["tool_calls"][0]
            arguments = tool_call["function"]["arguments"]
            function_name = tool_call["function"]["name"]

            if function_name == "get_designs":
                content = get_designs(json.loads(arguments)["company"])

            if function_name == "post_palette":
                content = post_palette(
                    json.loads(arguments)["company"],
                    json.loads(arguments)["name"]
                )
                
            if function_name == "post_palette_with_colors":
                content = post_palette_with_colors(
                    json.loads(arguments)["company"],
                    json.loads(arguments)["colors"],
                    json.loads(arguments)["name"]
                )
            # Add more conditions for other functions

        self.message.append(chat_response.json()["choices"][0]["message"])
        tool_message = {
                "role": "tool",
                "name": function_name,
                "content": content,
                "tool_call_id": tool_call["id"],
            }
        self.message.append(tool_message)

        new_response = self.chat_completion_request(
            messages=self.message, tools=self._tools
        )
        # print(new_response.json())
        self.message.append(new_response.json()["choices"][0]["message"])

        self.pretty_print_conversation()
