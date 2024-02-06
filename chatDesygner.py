import json
import requests
import os
from desygner import *
from tenacity import retry, wait_random_exponential, stop_after_attempt
from termcolor import colored
from dotenv import load_dotenv


class ChatDesygner():
    """
    This is a class that start a conversation with ChatGPT and be able to call
    Desygner's APIs
    """

    def __init__(self) -> None:
        """
        Start a new conversation with ChatGPT agent
        """

        self.new_chat()
        
    def new_chat(self) -> None:
        """
        Sets or resets the conversation to an initial state.
        """

        # Load configuration
        load_dotenv()
        self._gpt_model = os.environ.get("GPT_MODEL")
        self._api_key = os.environ.get("OPENAI_API_KEY")
        self._tools = TOOLS
        self._role_to_color = {
            "system": "red",
            "user": "green",
            "assistant": "blue",
            "tool": "magenta",
        }
        self.messages = []
        self.messages.append(
            {"role": "system", "content": "Perform function request for the user. Don't make assumptions about what values to plug into functions. Ask for clarification if a user request is ambiguous."}
        )

    def add_message(self, messages: dict[str: object]) -> None:
        """
        Append the user messages or OpenAI response
        """

        self.messages.append(messages)

    @retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
    def chat_completion_request(self, messages: list(dict[str: str]), tools=None, tool_choice=None) -> dict[str: str]:
        """
        Request OpenAI API to response with messages
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

    def respond(self, messages) -> None:
        """
        Respond to the user
        """

        print(colored(f"assistant: {messages['content']}\n", self._role_to_color[messages["role"]]))

    def display_conversation(self) -> None:
        """
        Print out the whole conversation
        """

        for messages in self.messages:
            if messages["role"] == "system":
                print(colored(f"system: {messages['content']}\n", self._role_to_color[messages["role"]]))
            elif messages["role"] == "user":
                print(colored(f"user: {messages['content']}\n", self._role_to_color[messages["role"]]))
            elif messages["role"] == "assistant" and messages.get("function_call"):
                print(colored(f"assistant: {messages['function_call']}\n", self._role_to_color[messages["role"]]))
            elif messages["role"] == "assistant" and not messages.get("function_call"):
                print(colored(f"assistant: {messages['content']}\n", self._role_to_color[messages["role"]]))
            elif messages["role"] == "tool":
                print(colored(f"function ({messages['name']}): {messages['content']}\n", self._role_to_color[messages["role"]]))

    def call_openai_function(self, messages: dict[str: str]) -> None:
        """
        Ask ChatGPT to call OpenAI functions
        """

        self.add_message(messages)
        chat_response = self.chat_completion_request(
            messages=self.messages, tools=self._tools
        )

        wants_to_use_function = chat_response.json()["choices"][0]["finish_reason"] == "tool_calls"
        content = ""

        if wants_to_use_function:
            tool_call_id, function_name, content = self.call_function(chat_response)

        self.add_message(chat_response.json()["choices"][0]["messages"])
        tool_message = {
                "role": "tool",
                "name": function_name,
                "content": content,
                "tool_call_id": tool_call_id,
            }
        self.add_message(tool_message)

        new_response = self.chat_completion_request(
            messages=self.messages, tools=self._tools
        )
        self.add_message(new_response.json()["choices"][0]["messages"])
        self.respond(new_response.json()["choices"][0]["messages"])

    def call_function(self, chat_response: json) -> (str, str, str):
        """
        Determine which function being called, and return corresponding tool call, 
        function name, and content
        """

        tool_call = chat_response.json()["choices"][0]["messages"]["tool_calls"][0]
        arguments = tool_call["function"]["arguments"]
        function_name = tool_call["function"]["name"]

        # Add more functions: make a dict that str: function
        # eg. functions = {'a': a()}
        # content = functions[function_name]
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

        return tool_call["id"], function_name, content
