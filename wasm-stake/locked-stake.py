'''
Queries the WASM state of a smart contract to get locked stake of users.
It is made for the HAVA staking contract that uses https://github.com/DA0-DA0/dao-contracts/tree/v2.4.0/contracts/voting/dao-voting-token-staked 
The team chose to use the unbonding period of the contract as locking time. Therefore all stake should be locked in claims.
'''

import csv
import json
import os
import httpx
import base64


current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
from dotenv import load_dotenv
load_dotenv(os.path.join(parent_dir, ".env"))

# Variables
NAME = os.getenv("LOCKED_STAKE_CHAIN", "juno")
CONTRACT = os.getenv("LOCKED_STAKE_CONTRACT", "osmo1rd2m6vqy6jj04uq80mxmx479pescz7cnc83yk3te72m3p55ntfpqnyxcfp")
EXPORT_NAME = os.getenv("LOCKED_STAKE_EXPORT_NAME", "hava_staking")
ENDPOINT = os.getenv("ENDPOINT", "http://localhost:1317")
ENTRIES_PER_QUERY = int(os.getenv("ENTRIES_PER_QUERY", 30))
HEIGHT = os.getenv("LOCKED_STAKE_EXPORT_HEIGHT", "latest")
LOCKED_STAKE_RELEASED_BEFORE = int(os.getenv("LOCKED_STAKE_RELEASED_BEFORE", "latest"))

LOCKED_STAKE_DIR = os.getenv("LOCKED_STAKE_DIR", "_LOCKED_STAKE")

output_dir = os.path.join(parent_dir, LOCKED_STAKE_DIR)
os.makedirs(output_dir, exist_ok=True)



def get_stakes():
    print("Querying all stakers...")
    last_query_res = query_stakes()
    stakes = last_query_res
    # because the REST API is paginated, we need to loop through the results
    while len(last_query_res) == ENTRIES_PER_QUERY:
        last_query_res = query_stakes(first=last_query_res[-1]["address"])
        stakes.extend(last_query_res)
        print(len(stakes), stakes[-1]["address"])
    return stakes

def get_claims(stakes, latest_unlock_time):
    print("Querying claims...")
    for i in range(len(stakes)):
        if i % 100 == 0:
            print(f"{i}/{len(stakes)}")
        stake = stakes[i]
        query = {"claims":{"address":stake["address"]}}
        res = run_query(query)
        stake["claims"] = res["data"]["claims"]
        stake["total_claim"] = sum([int(claim["amount"]) for claim in stake["claims"]])
        stake["amount_of_claims"] = len(stake["claims"])
        stake["eligible_claim"] = 0
        for claim in stake["claims"]:
            if int(claim["release_at"]["at_time"]) < latest_unlock_time * 1000000000:
                stake["eligible_claim"] += int(claim["amount"])
    return stakes

def query_stakes(first=None):
    query = {"list_stakers":{"limit":ENTRIES_PER_QUERY}}
    if first:
        query["list_stakers"]["start_after"] = first
    
    res = run_query(query)

    # put in same format as sorted staking export
    formatted = [{"address": entry["address"], "unclaimed_balance": entry["balance"]} for entry in res["data"]["stakers"]]
    for entry in formatted:
        if entry["unclaimed_balance"] != "0":
            print("found unclaimed balance:", entry["address"], entry["unclaimed_balance"])
    return formatted

def run_query(query):
    query_str = json.dumps(query)
    
    base64_encoded_query = base64.b64encode(query_str.encode()).decode()

    base64_encoded_query = base64_encoded_query.replace("=", "%3D")
    url = f"""{ENDPOINT}/cosmwasm/wasm/v1/contract/{CONTRACT}/smart/{base64_encoded_query}"""
    # print(url)
    res = httpx.get(
        url,
        timeout=60,
        headers={
            "accept": "application/json",
            # "x-cosmos-block-height": str(HEIGHT),
        },
    ).json()
    if "data" not in res:
        raise Exception("Query did not return data." + str(res))
    return res

def write_table(stakes, filename):
    with open(os.path.join(output_dir, filename), 'w') as f:
        writer = csv.writer(f)
        keys = ['address', 'unclaimed_balance', 'amount_of_claims', "total_claim", "eligible_claim"]
        writer.writerow(keys)
        for stake in stakes:
            row_to_write = [stake[key] for key in keys]
            writer.writerow(row_to_write)
    print(f"Saved to '{filename}'")


def main():
    stakes = get_stakes()
    print(f"Found {len(stakes)} stakes")
    stakes = get_claims(stakes, LOCKED_STAKE_RELEASED_BEFORE)

    write_table(stakes, f"{NAME}_{EXPORT_NAME}.csv")

    # with open(os.path.join(sorted_dir, f"{NAME}_{EXPORT_NAME}.json"), "w") as f:
    #     json.dump({"delegations":stakes}, f, indent=1)



if __name__ == "__main__":
    main()