'''
Script to combine balances from multiple chains
'''

import os
import csv
from utils import bech32encode, bech32decode

current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
from dotenv import load_dotenv
load_dotenv(os.path.join(parent_dir, ".env"))


balances_dir = os.path.join(parent_dir, "_AIRDROP_BALANCES")
os.makedirs(balances_dir, exist_ok=True)
combined_dir = os.path.join(balances_dir, "combined")
os.makedirs(combined_dir, exist_ok=True)

# New Chain Airdrop logic
SNAPSHOT_IGNORE_CONTRACTS = os.getenv('SNAPSHOT_IGNORE_CONTRACTS', 'false').lower().startswith('t')
CHAINS_TO_COMBINE = os.getenv('CHAINS_TO_COMBINE', 'cosmos')
KEY_PREFIX_DEFAULT = os.getenv('KEY_PREFIX', 'cosmos')

airdrop_amounts = {} # 'addr': uamount

def main():
    global airdrop_amounts

    print("Combining balances from ", CHAINS_TO_COMBINE)

    for chain in CHAINS_TO_COMBINE.split(','):
        print(f"Reading {chain} balance amounts...")
        new_balances = load_balances(chain)
        print(f"Loaded {len(new_balances)} balances from {chain}")

        amount_before = len(airdrop_amounts)
        add_balances(chain, new_balances, KEY_PREFIX_DEFAULT)
        print(f"Added {len(airdrop_amounts) - amount_before} new recipients from {chain}")

    # remove any addresses with 0 balance
    addrs_to_remove = []
    total_airdrop_amount = 0
    for addr, data in airdrop_amounts.items():
        if data['total_balance'] == 0:
            addrs_to_remove.append(addr)
        total_airdrop_amount += data['total_balance']
    for addr in addrs_to_remove:
        airdrop_amounts.pop(addr)

    
    save_to_csv(f'combined_balances.csv')
    
    print(f"Saved to '{balances_dir}'")
    print(f"Total airdrop amount {total_airdrop_amount}")
    print(f"Total amount recipients {len(airdrop_amounts)}")

def add_balances(chain, new_balances, key_chain_default='cosmos'):
    global airdrop_amounts

    for addr, balance in new_balances.items():
        # get address to use as key
        destination_chain, converted = bech32decode(addr)
        # because some chains have different key derivation paths, some of them do not fit to the default key_chain
        # instead we use another one for them
        key_chain = key_chain_default
        if destination_chain in ['inj', 'dym']:
            key_chain = 'inj'
        elif destination_chain in ['agoric']:
            key_chain = 'agoric'

        key_addr = bech32encode(key_chain, converted)

        if key_addr not in airdrop_amounts:
            airdrop_amounts[key_addr] = {'total_balance': 0.0}
        
        airdrop_amounts[key_addr][chain + " address"] = addr
        airdrop_amounts[key_addr][chain + " rewards"] = float(balance)
        airdrop_amounts[key_addr]['total_balance'] += float(balance)


def load_balances(chain):
    filename = os.path.join(balances_dir, f'{chain}_hava_airdrop_balances.csv')
    if not os.path.exists(filename):
        print(f"File '{filename}' does not exist!")
        return
    
    balances = {}
    with open(filename, 'r') as f:
        reader = csv.reader(f)
        reader.__next__() # skip header
        for row in reader:
            addr = row[0]
            balances[addr] = row[5]

    return balances

def save_to_csv(filename='airdrop.csv'):
    if len(airdrop_amounts) == 0:
        # print("No airdrop amounts to save!")
        return

    with open(os.path.join(combined_dir, filename), 'w') as f:
        writer = csv.writer(f)
        keys = ['key', 'total_balance']
        for chain in CHAINS_TO_COMBINE.split(','):
            keys.append(chain + " address")
            keys.append(chain + " rewards")
        writer.writerow(keys)
        for addr, data in airdrop_amounts.items():
            row_to_write = [addr, data['total_balance']]
            for chain in CHAINS_TO_COMBINE.split(','):
                if chain + " address" in data:
                    row_to_write.append(data[chain + " address"])
                    row_to_write.append(data[chain + " rewards"])
                else:
                    row_to_write.append("")
                    row_to_write.append("")
            writer.writerow(row_to_write)


if __name__ == '__main__':
    main()
    # test()