import json


def check_json(json_str: str, verbose: bool = True) -> bool:
    """Check if a string is a valid JSON."""
    try:
        json.loads(json_str)
        if verbose:
            print("Valid JSON! 🎉")
        return True
    except json.JSONDecodeError:
        if verbose:
            print("Not a valid JSON!")
        return False
