__all__ = ["hash_from_dict"]

import hashlib
import json
from typing import Any, Dict, List


def hash_from_dict(dict: Dict[str, Any]) -> str:
    """Get a hash from a dictionary"""
    dict_str = json.dumps(dict, sort_keys=True)
    result = hashlib.md5(dict_str.encode())
    return result.hexdigest()


def find_in_list_with_key(list: List[Dict[str, Any]], key: str, value: str) -> Any:
    found_item = None
    for item in list:
        if key in item and item[key] == value:
            found_item = item
    return found_item
