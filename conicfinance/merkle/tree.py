from typing import Callable, List, Optional, Union

from web3 import Web3


def compute_hash(user):
    if isinstance(user, str):
        address = Web3.toChecksumAddress(user)
        return Web3.solidityKeccak(["address"], [address])
    else:
        address = Web3.toChecksumAddress(user["address"])
        value = int(user["value"])
        return Web3.solidityKeccak(["address", "uint256"], [address, value])


def generate_merkle_tree(
    users: List[Union[dict, str]],
    process_leaves: Optional[Callable[[List[bytes]], None]] = None,
) -> bytes:
    leaves = [compute_hash(user) for user in users]
    while len(leaves) > 1:
        if len(leaves) % 2 == 1:
            leaves.append(Web3.solidityKeccak(["uint256"], [0]))
        if process_leaves:
            process_leaves(leaves)

        new_leaves = []
        for i in range(0, len(leaves), 2):
            new_leaves.append(
                Web3.solidityKeccak(["bytes32", "bytes32"], [leaves[i], leaves[i + 1]])
            )
        leaves = new_leaves
    return leaves[0]
