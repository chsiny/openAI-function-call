import json
from urllib.parse import urlencode
import re
import requests
import os

with open("open-api.json", 'r') as f:
    open_api_schema = json.load(f)

with open("to-map-dummy.json", 'r') as f:
    to_map = json.load(f)

with open("curated-definitions.json", 'r') as f:
    curated_definitions = json.load(f)

functions = []
extended_data = {}

def extract_open_ai_parameter_definition(parameters, request_body):
    properties = {}
    required = []
    payload_schema = (
        request_body
        and request_body.get('content', {}).get('application/json', {}).get('schema', {})
        and request_body['content']['application/json']['schema'].get('$ref')
    )

    if payload_schema:
        properties['payload'] = get_schema_path(payload_schema)

    for parameter in parameters or []:
        if parameter.get('name') == 'domain' and parameter.get('in') == 'path':
            continue  # Domain is automatically added under the hood

        properties[parameter['name']] = {
            'description': parameter.get('description', ''),
            'type': clear_type(
                parameter['schema']['type'] if 'schema' in parameter else parameter.get('type')
            ) or 'string',
        }

        if parameter.get('required'):
            required.append(parameter['name'])

        if properties[parameter['name']]['type'] == 'array':
            items = parameter.get('items') or parameter['schema'].get('items')

            properties[parameter['name']]['items'] = {
                'type': clear_type(items.get('type') or items['schema']['type']),
            }

    return {'type': 'object', 'required': required, 'properties': properties}

def extract_open_ai_function_definition(path):
    description = ''

    if path.get('summary'):
        description = path['summary']

    if path.get('description'):
        description = f"{description} {path['description']}" if description else path['description']

    if path.get('tags'):
        description = f"{description} {' '.join(path['tags'])}"

    return {'description': description.strip(), 'parameters': extract_open_ai_parameter_definition(path.get('parameters'), path.get('requestBody'))}

def get_schema_path(path):
    parts = path.split('/')
    key = parts.pop(0)
    root = open_api_schema

    for key in parts:
        root = root[key]

    # Deep clone
    return json.loads(json.dumps(root))

def expand_references(def_, deep=0):
    for attr, value in def_.items():
        if attr == '$ref':
            def_.update(get_schema_path(value))
            del def_['$ref']

    if deep > 10:
        return def_

    for attr, value in def_.items():
        if not isinstance(value, list) and isinstance(value, dict):
            expand_references(value, deep + 1)

    return def_

def clear_references(def_):
    properties = def_['properties']
    def_['properties'] = {}

    for prop, value in properties.items():
        if '$ref' not in value:
            def_['properties'][prop] = value

    return def_

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
    # TODO
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

for endpoint, methods in to_map.items():
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
def pretty_print(data):
    for entry in data:
        print(f"Name: {entry['name']}")
        print(f"Description: {entry['description']}")
        print("Parameters:")
        for param, details in entry['parameters'].items():
            print(f"  {param}: {details}")
        print(f"Function: {entry['function']}")
        print("-----")

# Example usage:
pretty_print(functions)