# Conic Finance airdrop

This is the repo to generate the Conic Finance airdrop snapshot.

## Generation logic

The snapshot is generated at block [14,494,800](https://etherscan.io/block/14494800), which is the time at which the airdrop was announced on Twitter.

The snapshot requires to have at least 3 vlCVX locked to be eligible.

The amount received per user is logarithmically proportional to their share with respect to the total amount of vlCVX locked.

## Reproducing the snapshot

To reproduce the snapshot, you will need an archive node.
Set the `ETH_RPC_URL` environment variable to the URL of the archive node.
Then run the following commands:

```
python generate_snapshot.py fetch-users -o data/vlcvx-historical-holders.txt.gz
python generate_snapshot.py fetch-balances data/vlcvx-historical-holders.txt.gz -o data/vlcvx-snapshot-balances.json.gz
python generate_snapshot.py generate-snapshot data/vlcvx-snapshot-balances.json.gz -o data/airdrop.json
```
