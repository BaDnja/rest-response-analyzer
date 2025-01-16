import json
from typing import Any, Dict, List, Union

import requests


def merge_types(existing: Union[str, List[str]], new: str) -> List[str]:
    """Aggregate types into a list of unique types."""
    if isinstance(existing, str):
        existing = [existing]
    if new not in existing:
        existing.append(new)
    return existing


def aggregate_schema(existing: Dict, new: Dict) -> Dict:
    """Merge two schemas together, handling type aggregation."""
    for key, value in new.items():
        if key not in existing:
            existing[key] = value
        else:
            if isinstance(value, dict) and "type" in value:
                if existing[key]["type"] == value["type"] == "object":
                    existing[key]["properties"] = aggregate_schema(
                        existing[key]["properties"], value["properties"]
                    )
                elif existing[key]["type"] == value["type"] == "array":
                    existing[key]["items"] = aggregate_schema(
                        existing[key]["items"], value["items"]
                    )
                else:
                    existing[key]["type"] = merge_types(
                        existing[key]["type"], value["type"]
                    )
    return existing


def get_type(value: Any) -> Union[str, Dict]:
    """Determine the type of value."""
    if value is None:
        return "null"
    elif isinstance(value, list):
        if len(value) == 0:
            return {"type": "array", "items": {}}
        item_schemas = [generate_schema(item) for item in value]
        aggregated_items = {}
        for item_schema in item_schemas:
            aggregated_items = aggregate_schema(aggregated_items, item_schema)
        return {"type": "array", "items": aggregated_items}
    elif isinstance(value, dict):
        return {"type": "object", "properties": generate_schema(value)}
    else:
        return type(value).__name__


def generate_schema(data: Any) -> Dict[str, Any]:
    """
    Generate a schema for a given JSON-like Python object (dict or list).
    """
    if isinstance(data, dict):
        schema = {}
        for key, value in data.items():
            value_type = get_type(value)
            if isinstance(value_type, dict) and "type" in value_type:
                schema[key] = value_type
            else:
                schema[key] = {"type": value_type}
        return schema
    elif isinstance(data, list):
        return get_type(data)
    else:
        return {"type": type(data).__name__}


def fetch_and_generate_schema(url: str) -> Dict[str, Any]:
    """
    Fetch data from an API and generate its schema.
    """
    # Sometimes, you will not be using token to authenticate, so change this part as needed.
    token = "replaceWithRealToken"
    headers = {
        "Authorization": f"Bearer {token}",
        "accept": "application/json",
    }
    params = {"page": 0}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        return generate_schema(data)
    else:
        raise Exception(f"Failed to fetch data. Status code: {response.status_code}")


if __name__ == "__main__":
    # Replace with your API URL
    api_url = "https://api.url.com/endpoint"
    schema = fetch_and_generate_schema(api_url)
    print(json.dumps(schema, indent=2))
    # Open your favorite JSON viewer (for example: https://jsonviewer.stack.hu/) and paste printed JSON.
