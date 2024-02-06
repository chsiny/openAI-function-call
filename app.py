from chatDesygner import *


if __name__ == '__main__':
    chat = ChatDesygner()

    while True:

        user_input = input("(Enter 'c' to exit): ")

        if user_input == 'c':
            break

        elif user_input == 'print all':
            chat.pretty_print_conversation()

        else:
            message = {"role": "user", "content": user_input}
            chat.call_openai_function(message)
