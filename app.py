from chat import *


if __name__ == '__main__':
    chat = ChatDesygner()

    while True:

        user_input = input("(Enter 'c' to exit): ")

        if user_input == 'c':
            break

        message = {"role": "user", "content": user_input}
        
        chat.call_openai_function(message)
