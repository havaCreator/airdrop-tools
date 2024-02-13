'''
Queries the WASM state of a smart contract to get stake balances of users.
Exported in the same format as the sorted staking export.
'''

import json
import os
import httpx
import base64


current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
from dotenv import load_dotenv
load_dotenv(os.path.join(parent_dir, ".env"))

# Variables
NAME = os.getenv("SNAPSHOT_CHAIN_PREFIX", "juno")
CONTRACT = os.getenv("WASM_CONTRACT", "osmo1rd2m6vqy6jj04uq80mxmx479pescz7cnc83yk3te72m3p55ntfpqnyxcfp")
EXPORT_NAME = os.getenv("WASM_EXPORT_NAME", "wosmo_staking")
ENDPOINT = os.getenv("ENDPOINT", "http://localhost:1317")
ENTRIES_PER_QUERY = int(os.getenv("ENTRIES_PER_QUERY", 30))
HEIGHT = os.getenv("HEIGHT", "latest")

SNAPSHOT_SORTED_FOLDER = os.getenv("SNAPSHOT_SORTED_FOLDER", f"{NAME}_sorted")

sorted_dir = os.path.join(parent_dir, "_SORTED", SNAPSHOT_SORTED_FOLDER)
os.makedirs(sorted_dir, exist_ok=True)



def get_stakes():
    last_query_res = run_query()
    stakes = last_query_res
    # because the REST API is paginated, we need to loop through the results
    while len(last_query_res) == ENTRIES_PER_QUERY:
        last_query_res = run_query(first=last_query_res[-1]["delegator_address"])
        stakes.extend(last_query_res)
        print(len(stakes), stakes[-1]["delegator_address"])

    # print(stakes)
    return stakes

def run_query(first=None):

    query = {"list_stakers":{"limit":ENTRIES_PER_QUERY}}
    if first:
        query["list_stakers"]["start_after"] = first
    
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
            "x-cosmos-block-height": str(HEIGHT),
        },
    ).json()

    # put in same format as sorted staking export
    formatted = [{"delegator_address": entry["address"], "shares": entry["balance"]} for entry in res["data"]["stakers"]]
    return formatted


def main():
    stakes = get_stakes()

    with open(os.path.join(sorted_dir, f"{NAME}_{EXPORT_NAME}.json"), "w") as f:
        json.dump({"delegations":stakes}, f, indent=1)

if __name__ == "__main__":
    main()