'''
Script to process balance csv files and create a _SORTED folder entry compatible with the airdrop calculation pipeline
'''

import os
import csv
import json

current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
from dotenv import load_dotenv
load_dotenv(os.path.join(parent_dir, ".env"))


input_dir = os.path.join(parent_dir, "_ADDITIONAL_DATA")
SNAPSHOT_SORTED_FOLDER = os.getenv('SNAPSHOT_SORTED_FOLDER', 'hava')
sorted_dir = os.path.join(parent_dir, "_SORTED", SNAPSHOT_SORTED_FOLDER)
os.makedirs(sorted_dir, exist_ok=True)

# New Chain Airdrop logic
CONVERT_INPUT = os.getenv('CONVERT_INPUT', 'cosmos')
CONVERT_DECIMALS_TO_ADD = int(os.getenv('CONVERT_DECIMALS_TO_ADD', '6'))

def main():
    print("Processing balances from ", CONVERT_INPUT)

    balances = load_balances(CONVERT_INPUT)
    print(f"Loaded {len(balances)} balances from {CONVERT_INPUT}")
    
    staking_data = convert_balances_to_staking(balances)
    save_to_json(f'{CONVERT_INPUT}_staking.json', staking_data)
    
    print(f"Saved to '{sorted_dir}'")

def load_balances(chain):
    filename = os.path.join(input_dir, f'{chain}.csv')
    if not os.path.exists(filename):
        raise FileNotFoundError(f"File '{filename}' does not exist!")
    
    balances = {}
    data_point_count = 0
    with open(filename, 'r') as f:
        reader = csv.reader(f)
        reader.__next__() # skip header
        for row in reader:
            addr = row[0]
            if addr not in balances:
                balances[addr] = 0.0
            # else:
            #     print(f"Duplicate address {addr} found!")
            # handle duplicates
            balances[addr] += float(row[1]) * 10**CONVERT_DECIMALS_TO_ADD
            data_point_count += 1

    print(f"Processed {data_point_count} data points from {filename}")

    return balances

def convert_balances_to_staking(balances):
    # Result dict to fill
    staking_data = { 'delegations': [] }

    for addr, balance in balances.items():
        staking_data['delegations'].append({
            'delegator_address': addr,
            'shares': int(balance),
        })
    
    return staking_data

def save_to_json(filename, staking_data):
    if len(staking_data) == 0:
        print("No airdrop amounts to save!")
        return

    with open(os.path.join(sorted_dir, filename), 'w') as f:
        f.write(json.dumps(staking_data, indent=2))

if __name__ == '__main__':
    main()