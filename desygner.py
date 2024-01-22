import requests
import os
from dotenv import load_dotenv

load_dotenv()

# class Desygner():

#     def __init__(self) -> None:
#         self.api_key = os.environ.get("DESYGNER_API_TOKEN")

api_key = os.environ.get("DESYGNER_API_TOKEN")

def get_invoices(company: str):
    api_url = f"https://api.makedesygner.xyz/brand/companies/{company}/invoices"
    try:
        # Define the headers with authorization information
        headers = {
            'Authorization': f'Basic {api_key}',
            'Content-Type': 'application/json',
        }

        # Make a GET request to the API with the specified headers
        response = requests.get(api_url, headers=headers)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Parse and return the JSON data from the response
            print(response.json())
        else:
            # Print an error message if the request was not successful
            print(f"Error: {response.status_code}")
            return None
    except Exception as e:
        # Handle exceptions, such as network errors
        print(f"An error occurred: {e}")
        return None
    
def get_designs(company):
    api_url = f"https://api.makedesygner.xyz/brand/companies/{company}/designs"
    try:
        # Define the headers with authorization information
        headers = {
            'Authorization': f'Basic {api_key}',
            'Content-Type': 'application/json',
        }

        # Make a GET request to the API with the specified headers
        response = requests.get(api_url, headers=headers)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Parse and return the JSON data from the response
            return response.json()
        else:
            # Print an error message if the request was not successful
            print(f"Error: {response.status_code}")
            return None
    except Exception as e:
        # Handle exceptions, such as network errors
        print(f"An error occurred: {e}")
        return None

