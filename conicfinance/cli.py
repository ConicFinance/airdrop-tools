import argparse
import gzip
import json
import os

from eth_account import Account
from tqdm import tqdm
from web3 import HTTPProvider, Web3

from conicfinance.airdrop.generate_sample import generate_users
from conicfinance.initial_distribution import whitelist
from conicfinance.plotting import plot_airdrop_boost_dist
from conicfinance.merkle.proof import generate_proof
from conicfinance.merkle.tools import generate_merkle_root
from conicfinance.locker_v2.airdrop import compute_airdrop as compute_boost_airdrop

parser = argparse.ArgumentParser(description="Set of tools for Conic Finance")

supbarsers = parser.add_subparsers(dest="command")

plot_parser = supbarsers.add_parser("plot", help="Visualise boosts")
plot_subparsers = plot_parser.add_subparsers(dest="subcommand")
boost_plot_parser = plot_subparsers.add_parser(
    name="plot-boosts", help="plot the CDF of the airdrop boosts"
)
boost_plot_parser.add_argument("input", help="Input file with airdrop boosts")
boost_plot_parser.add_argument("-o", "--output", required=True, help="Output figure file")

merkle_parser = supbarsers.add_parser("merkle", help="Merkle tree related tools")
merkle_subparser = merkle_parser.add_subparsers(dest="subcommand")

generate_proof_parser = merkle_subparser.add_parser(
    name="generate-proof", help="Generate a proof for an address"
)
generate_proof_parser.add_argument("input", help="Input file with aidrop information")
generate_proof_parser.add_argument(
    "-a", "--address", required=True, help="Address to generate proof for"
)


generate_root_parser = merkle_subparser.add_parser(
    "generate-root", help="Generate Merkle root"
)
generate_root_parser.add_argument("input", help="Input file with aidrop information")

airdrop_parser = supbarsers.add_parser("airdrop", help="Airdrop related tools")
airdrop_subparser = airdrop_parser.add_subparsers(dest="subcommand")
sample_airdrop_parser = airdrop_subparser.add_parser(
    "generate-sample", help="Generate sample airdrop"
)
sample_airdrop_parser.add_argument(
    "-o", "--output", required=True, help="Output JSON file"
)
sample_airdrop_parser.add_argument(
    "-c", "--users-count", default=500, help="Total number of users"
)
sample_airdrop_parser.add_argument(
    "-t", "--total-amount", default=1_000_000, help="Total amount to airdrop"
)

boost_airdrop_parser = airdrop_subparser.add_parser(
    "generate-boost", help="Generates the airdrop for the Locker V2 boost"
)
boost_airdrop_parser.add_argument(
    "-o", "--output", required=True, help="Output JSON file"
)

distribution_parser = supbarsers.add_parser(
    "distribution", help="Initial distribution related tools"
)
distribution_subparser = distribution_parser.add_subparsers(dest="subcommand")
sample_whitelist_parser = distribution_subparser.add_parser(
    "sample-whitelist", help="Generate sample whitelist"
)

sample_whitelist_parser.add_argument(
    "-o", "--output", required=True, help="Output JSON file"
)
sample_whitelist_parser.add_argument(
    "-c", "--users-count", default=500, help="Total number of users"
)
sample_whitelist_parser.add_argument(
    "addresses", nargs="*", help="Users to add to the list"
)

generate_whitelist_parser = distribution_subparser.add_parser(
    "generate-whitelist", help="Generate whitelist"
)
generate_whitelist_parser.add_argument(
    "-o", "--output", required=True, help="Output JSON file"
)

misc_parser = supbarsers.add_parser("misc", help="Miscalenous tools")
misc_subparser = misc_parser.add_subparsers(dest="subcommand")
fetch_event_times_parser = misc_subparser.add_parser(
    "fetch-event-times", help="Fetches the timestamps for events"
)
fetch_event_times_parser.add_argument("input", help="Input JSON lines file")
fetch_event_times_parser.add_argument(
    "-o", "--output", required=True, help="Output JSON file"
)


class Command:
    def __init__(self, args):
        self.args = args

    def run(self):
        if not self.args.subcommand:
            self.parser.error("no subcommand given")
        getattr(self, self.normalized_subcommand)()

    @property
    def parser(self):
        raise NotImplementedError()

    @property
    def normalized_subcommand(self) -> str:
        return self.args.subcommand.replace("-", "_")


class PlotCommand(Command):
    def plot_boosts(self):
        plot_airdrop_boost_dist(self.args.input, self.args.output)

    @property
    def parser(self):
        return plot_parser

class DistributionCommand(Command):
    def sample_whitelist(self):
        n = self.args.users_count - len(self.args.addresses)
        users = [Account.create().address for _ in range(n)]
        users.extend(self.args.addresses)
        with open(self.args.output, "w") as f:
            json.dump(users, f, indent=2)

    def generate_whitelist(self):
        whitelist.generate(self.args.output)

    @property
    def parser(self):
        return distribution_parser


class MerkleCommand(Command):
    def generate_root(self):
        print(generate_merkle_root(self.args.input))

    def generate_proof(self):
        with open(self.args.input) as f:
            users = json.load(f)
        try:
            proof, value = generate_proof(self.args.address, users)
            print(f"claimer: `{self.args.address}`")
            if value > 0:
                print(f"amount: `{value}`")
            formatted_proof = [proof[1], [v.hex() for v in proof[0]]]
            print("proof: `" + json.dumps(formatted_proof) + "`")
        except ValueError:
            print("Address not found")

    @property
    def parser(self):
        return merkle_parser


class AirdropCommand(Command):
    def generate_sample(self):
        users = generate_users(self.args.users_count, self.args.total_amount)
        print(sum(int(user["value"]) for user in users))
        with open(self.args.output, "w") as f:
            json.dump(users, f, indent=2)

    def generate_boost(self):
        users = compute_boost_airdrop()
        with open(self.args.output, "w") as f:
            json.dump(users, f, indent=2)

    @property
    def parser(self):
        return airdrop_parser


class MiscCommand(Command):
    def fetch_event_times(self):
        with gzip.open(self.args.input) as f:
            events = [json.loads(line) for line in f]
            block_numbers = set(event["blockNumber"] for event in events)
        web3 = Web3(HTTPProvider(os.environ["ETH_RPC_URL"]))
        block_timestamps = {}
        for number in tqdm(block_numbers):
            block_timestamps[number] = web3.eth.getBlock(number)["timestamp"]
        with open(self.args.output, "w") as f:
            json.dump(block_timestamps, f)

    @property
    def parser(self):
        return misc_parser


class RootCommand(Command):
    def merkle(self):
        return MerkleCommand(self.args)

    def airdrop(self):
        return AirdropCommand(self.args)

    def distribution(self):
        return DistributionCommand(self.args)

    def plot(self):
        return PlotCommand(self.args)

    def misc(self):
        return MiscCommand(self.args)

    def run(self):
        if not self.args.command:
            parser.error("no command given")
        command = getattr(self, self.args.command)()
        command.run()


def main():
    args = parser.parse_args()
    root_command = RootCommand(args)
    root_command.run()


if __name__ == "__main__":
    main()
