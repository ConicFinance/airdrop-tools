from typing import List, Tuple, Union

from conicfinance.merkle.tree import generate_merkle_tree
from web3 import Web3


class ProofGenerator:
    def __init__(self, target_address: str, users: List[Union[dict, str]]):
        self.users = users
        target = Web3.toChecksumAddress(target_address)
        self.target_index = [self._get_address(u) for u in users].index(target)
        self.node_index = self.target_index
        target_user = users[self.target_index]
        if isinstance(target_user, dict):
            self.value = int(target_user["value"])
        else:
            self.value = 0
        self.proof = []

    def process_leaves(self, leaves: List[bytes]):
        if self.node_index % 2 == 0:
            self.proof.append(leaves[self.node_index + 1])
        else:
            self.proof.append(leaves[self.node_index - 1])
        self.node_index //= 2

    def _get_address(self, user: Union[dict, str]):
        if isinstance(user, str):
            return Web3.toChecksumAddress(user)
        return Web3.toChecksumAddress(user["address"])


def generate_proof(
    user_address: str, users: List[Union[dict, str]]
) -> Tuple[Tuple[List[bytes], int], int]:
    proof_generator = ProofGenerator(user_address, users)
    generate_merkle_tree(users, proof_generator.process_leaves)
    return (proof_generator.proof, proof_generator.target_index), proof_generator.value
