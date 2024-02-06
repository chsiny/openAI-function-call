import json
import re
import requests
import os
from urllib.parse import urlencode

# Load OpenAPI schema, mapping, definitions, etc.
with open("json/open-api.json", 'r') as f:
    open_api_schema = json.load(f)

with open("json/to-map-all.json", 'r') as f:
    to_map = json.load(f)

with open("json/to-map-useful.json", 'r') as f:
    useful_api = json.load(f)

with open("json/curated-definitions.json", 'r') as f:
    curated_definitions = json.load(f)

functions = []
extended_data = {}

def extract_open_ai_parameter_definition(parameters, request_body):
    properties = {}
    required = []

    # Extract payload schema if present
    payload_schema = request_body and request_body.get('content', {}).get('application/json', {}).get('schema', {})
    if payload_schema:
        properties['payload'] = get_schema_path(payload_schema)

    # Extract parameters
    for parameter in parameters or []:
        name = parameter.get('name', '')

        # Use get method to handle cases where 'schema' or 'type' keys are not present
        schema = parameter.get('schema', {})
        parameter_type = schema.get('type') if 'type' in schema else parameter.get('type', '')

        # Handle domain parameter
        if name == 'domain' and parameter.get('in') == 'path':
            continue

        properties[name] = {
            'description': parameter.get('description', ''),
            'type': clear_type(parameter_type) or 'string',
        }

        if parameter.get('required'):
            required.append(name)

        if properties[name]['type'] == 'array':
            items = schema.get('items') or parameter.get('items', {})
            properties[name]['items'] = {
                'type': clear_type(items.get('type') or items['schema']['type']),
            }

    return {'type': 'object', 'required': required, 'properties': properties}

def extract_open_ai_function_definition(path):
    description = path.get('summary', '')
    description += f" {path.get('description', '')}" if description else path.get('description', '')
    description += f" {' '.join(path['tags'])}" if path.get('tags') else ''

    return {'description': description.strip(), 'parameters': extract_open_ai_parameter_definition(path.get('parameters'), path.get('requestBody'))}

def get_schema_path(path):
    parts = []
    root = path

    while isinstance(root, dict):
        key, root = next(iter(root.items()))
        parts.append(key)

    # Deep clone
    return json.loads(json.dumps(root))

def clear_type(type_):
    if type_ == 'int':
        return 'integer'
    if type_ == 'bool':
        return 'boolean'

    return type_

def get_function_name(endpoint, method):
    parts = [part for part in endpoint.split('/') if part and not part.startswith('{')]
    parts.pop(0)

    def replace_dash(match):
        return match.group(1).upper()

    return method + ''.join([re.sub(r'-([a-zA-Z])', replace_dash, s) for s in parts]).capitalize()

def get_endpoint_handler(endpoint, method, parameters):
    domain = 'desygner'
    token = 'dd-'
    known_maps = {'resource_id': 'entity_id'}

    def handler(args):
        nonlocal endpoint

        params = {
            'method': method,
            'headers': {
                'Content-Type': 'application/json',
                'Authorization': f'Basic {token}',
            },
        }

        query = urlencode({})

        endpoint = endpoint.replace('{domain}', domain)

        for name, value in args.items():
            if name == 'payload':
                if method.lower() in ['put', 'post', 'patch']:
                    params['body'] = json.dumps(value)
                else:
                    raise ValueError(f'Payload not supported for {method} method')
            else:
                parameter = next((p for p in parameters if p.get('name') == name), None)

                if parameter and parameter.get('in') == 'path':
                    initial_endpoint = endpoint
                    endpoint = re.sub(r'{[^\}]+}', lambda arg: args[name] if arg.group().startswith(f'{{{name}') else arg.group(), endpoint)

                    if initial_endpoint == endpoint and name in known_maps:
                        # Hacky workaround for wrongly documented fragments
                        endpoint = re.sub(r'{[^\}]+}', lambda arg: args[name] if arg.group().startswith(f'{{{known_maps[name]}') else arg.group(), endpoint)
                elif parameter and parameter.get('in') == 'query':
                    query += f'&{name}={args[name]}'
                else:
                    raise ValueError(f'Unexpected argument {name}')

        if '{' in endpoint:
            raise ValueError(f'Missing path arguments {endpoint}')

        response = requests.get(f"{os.environ['API']}{endpoint}?{query}", **params)
        return response.text

    return handler

# Build functions and extended_data
for endpoint, methods in to_map.items():
    if endpoint in useful_api:
        for method in methods:
            if endpoint not in extended_data:
                extended_data[endpoint] = {}

            endpoint_schema = open_api_schema['paths'][endpoint][method]
            extended_data[endpoint][method] = (
                curated_definitions[endpoint][method]
                if curated_definitions.get(endpoint) and curated_definitions[endpoint].get(method)
                else extract_open_ai_function_definition(endpoint_schema)
            )

            functions.append({
                **extended_data[endpoint][method],
                'parse': json.loads,
                'name': get_function_name(endpoint, method),
                'function': get_endpoint_handler(endpoint, method, endpoint_schema.get('parameters', [])),
            })

# Use this for extending "curated-definition.json"
# print(json.dumps(extended_data, indent=2))

# Export functions
# functions

# Example usage:
def pretty_print(data):
    for entry in data:
        print(f"Name: {entry['name']}")
        print(f"Description: {entry['description']}")
        print("Parameters:")
        for param, details in entry['parameters'].items():
            print(f"  {param}: {details}")
        print(f"Function: {entry['function']}")
        print("-----")

for entry in functions:
    if entry["name"] == "headCompaniesdesignsfolderschildren":
        print(entry)
