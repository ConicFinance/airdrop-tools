import json

from .tree import generate_merkle_tree


def generate_merkle_root(input_file: str) -> str:
    with open(input_file) as f:
        users = json.load(f)

    root = generate_merkle_tree(users)
    return root.hex()
