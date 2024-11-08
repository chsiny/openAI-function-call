import requests
import os
import color
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ.get("DESYGNER_API_TOKEN")
TOOLS = [
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
                        "description": "The company name, e.g. desygner",
                    }
                },
                "required": ["company"]
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "post_palette",
            "description": "add a new palette for the company",
            "parameters": {
                "type": "object",
                "properties": {
                    "company": {
                        "type": "string",
                        "description": "The company name, e.g. desygner",
                    },
                    "name": {
                        "type": "string",
                        "description": "The palettes name, e.g. christmas",
                    },
                },
                "required": ["company"]
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "post_palette_with_colors",
            "description": "add a new palette for the company with specific colors",
            "parameters": {
                "type": "object",
                "properties": {
                    "company": {
                        "type": "string",
                        "description": "The company name, e.g. desygner",
                    },
                    "colors": {
                        "type": "array",
                        "description": "A list of rgb, e.g. [(255, 240, 240), (255, 0, 240), (255, 240, 0), (255, 240, 100), (100, 240, 240), (0, 240, 240)]",
                        "items": {
                            "type": "array",
                            "items": {
                                "type": "integer"
                            },
                            "minItems": 3,
                            "maxItems": 3
                        },
                    },
                    "name": {
                        "type": "string",
                        "description": "The palettes name, e.g. christmas",
                    },
                },
                "required": ["company", "colors"]
            },
        }
    },
]

def get_invoices(company: str) -> str | None:
    """
    Get the invoices info of the company

    @company: domain name
    @return: 
    """
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
            return response.json()
        else:
            # Print an error message if the request was not successful
            print(f"Error: {response.status_code}")
            return None
    except Exception as e:
        # Handle exceptions, such as network errors
        print(f"An error occurred: {e}")
        return None
    
def get_designs(company: str) -> str:
    api_url = f"https://api.makedesygner.xyz/brand/companies/{company}/designs"
    try:
        # Define the headers with authorization information
        headers = {
            'Authorization': f'Basic {api_key}',
            'Content-Type': 'application/json',
        }

        # Make a GET request to the API with the specified headers
        response = requests.get(api_url, headers=headers)

        output = ""
        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Parse and return the JSON data from the response
            designs = response.json()
            for idx, design in enumerate(designs):
                output += f"{idx + 1}. {design['name']}\n"

            return output

        else:
            # Print an error message if the request was not successful
            print(f"Error: {response.status_code}")
            return None
    except Exception as e:
        # Handle exceptions, such as network errors
        print(f"An error occurred: {e}")
        return None

def post_palette(company: str, name: str = "test") -> str:
    api_url = f"https://api.makedesygner.xyz/brand/companies/{company}/library/palettes"

    try:
        # Define the headers with authorization information
        headers = {
            'Authorization': f'Basic {api_key}',
            'Content-Type': 'application/json',
        }

        data = {
            "is_deleted": False,
            "is_linked": False,
            "smart_asset": [],
            "is_under_review": False,
            "is_smart_asset": False,
            "id": 0,
            "type": "Palette",
            "data": {
                "id": 0,
                "name": name,
                "colors": []
            },
            "order": 0,
            "tags": []
        }

        # Make a POST request to the API with the specified headers
        response = requests.post(api_url, headers=headers, json=data)

        # Check if the request was successful (status code 200)
        if response.status_code == 201:
            return "success"

        else:
            # Print an error message if the request was not successful
            print(f"Error: {response.status_code}")
            return None
    except Exception as e:
        # Handle exceptions, such as network errors
        print(f"An error occurred: {e}")
        return None
    
def post_color(company: str, pid: int, color_code: int) -> str:
    api_url = f"https://api.makedesygner.xyz/brand/companies/{company}/library/colors"

    try:
        # Define the headers with authorization information
        headers = {
            'Authorization': f'Basic {api_key}',
            'Content-Type': 'application/json',
        }

        data = {
            "is_deleted": False,
            "is_linked": False,
            "smart_asset": [],
            "is_under_review": False,
            "is_smart_asset": False,
            "id": 0,
            "type": "Color",
            "data": {
                "color_code": color_code,
                "palette": pid
            },
            "order": 0,
            "tags": []
        }

        # Make a POST request to the API with the specified headers
        response = requests.post(api_url, headers=headers, json=data)

        # Check if the request was successful (status code 200)
        if response.status_code == 201:
            return "success"

        else:
            # Print an error message if the request was not successful
            print(f"Error: {response.status_code}")
            return None
    except Exception as e:
        # Handle exceptions, such as network errors
        print(f"An error occurred: {e}")
        return None
    
def post_palette_with_colors(
        company: str,
        colors: list[tuple[int, int, int]],
        name="Untitle"
        ) -> str:
    api_url = f"https://api.makedesygner.xyz/brand/companies/{company}/library/palettes"

    try:
        # Define the headers with authorization information
        headers = {
            'Authorization': f'Basic {api_key}',
            'Content-Type': 'application/json',
        }

        data = {
            "is_deleted": False,
            "is_linked": False,
            "smart_asset": [],
            "is_under_review": False,
            "is_smart_asset": False,
            "id": 0,
            "type": "Palette",
            "data": {
                "id": 0,
                "name": name,
                "colors": []
            },
            "order": 0,
            "tags": []
        }

        # Make a POST request to the API with the specified headers
        response = requests.post(api_url, headers=headers, json=data)

        # Check if the request was successful (status code 200)
        if response.status_code == 201:
            pid = response.json()["data"]["id"]
            
            # Add 6 colors
            for c in colors:
                color_code = color.rgb_to_color_code(c)
                post_color(company, pid, color_code)

            return "success"

        else:
            # Print an error message if the request was not successful
            print(f"Error: {response.status_code}")
            return None
    except Exception as e:
        # Handle exceptions, such as network errors
        print(f"An error occurred: {e}")
        return None
