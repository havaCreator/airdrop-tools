'''
Reece Williams | Oct 31st 2022
Example script on how to read the genesis data from the state export

Variant to calculate Hava airdrop amounts based on staking
'''

import json, os
import csv
from utils import bech32encode, bech32decode
import math

current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
from dotenv import load_dotenv
load_dotenv(os.path.join(parent_dir, ".env"))


SNAPSHOT_SORTED_FOLDER = os.getenv('SNAPSHOT_SORTED_FOLDER', 'juno_sorted')
sorted_dir = os.path.join(parent_dir, "_SORTED", SNAPSHOT_SORTED_FOLDER)
balances_dir = os.path.join(parent_dir, "_AIRDROP_BALANCES")
os.makedirs(sorted_dir, exist_ok=True)
os.makedirs(balances_dir, exist_ok=True)

SNAPSHOT_CHAIN_PREFIX = os.getenv('SNAPSHOT_CHAIN_PREFIX', "juno")
SNAPSHOT_CHAIN_TOKEN = os.getenv('SNAPSHOT_CHAIN_TOKEN', "ujuno")

# New Chain Airdrop logic
SNAPSHOT_IGNORE_CONTRACTS = os.getenv('SNAPSHOT_IGNORE_CONTRACTS', 'false').lower().startswith('t')
SNAPSHOT_STAKING_MINIMUM = int(os.getenv('SNAPSHOT_STAKING_MINIMUM', '0')) 
SNAPSHOT_STAKING_MAXIMUM = int(os.getenv('SNAPSHOT_STAKING_MAXIMUM', '0')) 
SNAPSHOT_PRICE = float(os.getenv('SNAPSHOT_PRICE', '0')) 
SNAPSHOT_DECIMALS = int(os.getenv('SNAPSHOT_DECIMALS', '0')) 
AIRDROP_AMOUNT = float(os.getenv('AIRDROP_AMOUNT', '0')) 

NEW_CHAIN_PREFIX = os.getenv('NEW_CHAIN_PREFIX', 'cosmos')
NEW_CHAIN_TOKEN = os.getenv('NEW_CHAIN_TOKEN', 'uatom')


airdrop_amounts = {} # 'addr': uamount

def main():
    global airdrop_amounts

    # if SNAPSHOT_IGNORE_CONTRACTS=True, we ignore any addresses which are longer than 39+len(SNAPSHOT_CHAIN_PREFIX)
    title = f'{SNAPSHOT_CHAIN_PREFIX}_{NEW_CHAIN_TOKEN}_airdrop'

    # balance_airdrop()
    # save_commands_to_file(f'{title}_balances.sh')
    # balances_airdroped = len(airdrop_amounts)
    
    staking_airdrop()
    save_to_csv(f'{title}_balances.csv')
    
    print(f"Saved to '{balances_dir}'")

def balance_airdrop():
    global airdrop_amounts    
    airdrop_amounts = {}
    print(f"Reading {SNAPSHOT_CHAIN_PREFIX} balance amounts...")

    bankJSON = os.path.join(sorted_dir, f'{SNAPSHOT_CHAIN_PREFIX}_bank.json')

    if not os.path.exists(bankJSON):
        print(f"\tERROR: '{SNAPSHOT_CHAIN_PREFIX}_bank.json' is not found, so no balances to airdrop too. If this is a mistake ensure you ran sorter.py...")
        print(f"\tand that .env has SNAPSHOT_WANTED_SECTIONS=\"bank\"\n")
        return

    balances = json.load(open(bankJSON, 'r'))['balances']

    # loop through bank
    for account in balances: # {'address': 'cosoms1...', 'coins': [{'amount': '1000000', 'denom': 'utoken'}]}
        addr = account['address']

        if SNAPSHOT_IGNORE_CONTRACTS and len(addr) > 39+len(SNAPSHOT_CHAIN_PREFIX):
            continue # normal public key = length of 39. So prefix+39 = 44. Contracts are longer

        coins = account['coins']
        for coin in coins:
            if coin['denom'] == SNAPSHOT_CHAIN_TOKEN:
                amt = coin['amount']
                if int(amt) < SNAPSHOT_BALANCE_MINIMUM:
                    continue

                # save as the new address
                _, data = bech32decode(addr)
                new_addr = bech32encode(NEW_CHAIN_PREFIX, data)
                
                updated_amt = int(eval(NEW_CHAIN_FORMULA_BALANCES.replace('AMT', str(amt))))
                airdrop_amounts[new_addr] = updated_amt


def staking_airdrop(): 
    # {'delegator_address': 'cosoms1...', 'shares': '11458136.000000000000000000', 'validator_address': 'cosmosvaloper1xxxx'}
    global airdrop_amounts    
    airdrop_amounts = {}
    print(f"Reading {SNAPSHOT_CHAIN_PREFIX} staked amounts...")
    
    stakingJSON = os.path.join(sorted_dir, f'{SNAPSHOT_CHAIN_PREFIX}_staking.json')
    if not os.path.exists(stakingJSON):
        print(f"\tERROR: '{SNAPSHOT_CHAIN_PREFIX}_staking.json' is not found, so no stakers to airdrop too. If this is a mistake ensure you ran sorter.py...")
        print(f"\tand that .env has SNAPSHOT_WANTED_SECTIONS=\"staking\"\n")
        return

    staking = json.load(open(stakingJSON, 'r'))['delegations']

    for stake in staking:
        addr = stake['delegator_address']
        shares = stake['shares']

        if SNAPSHOT_IGNORE_CONTRACTS and len(addr) > 39+len(SNAPSHOT_CHAIN_PREFIX):
            continue # ignore contract addresses

        # LOGIC HERE
        # round shares up to 0 decimal places
        shares = int(float(shares))
        if shares == 0: continue

        if addr not in airdrop_amounts.keys():
            airdrop_amounts[addr] = {'stake': 0, 'stake_value': 0,'eligible_stake': 0, 'airdrop_share': 0, 'airdrop_amount': 0}

        airdrop_amounts[addr]['stake'] += int(shares)

    # calculate airdrop share
    total_stake = 0
    total_eligible_stake = 0
    amount_airdrop_receivers = 0
    
    for addr, data in airdrop_amounts.items():
        total_stake += data['stake']
        
        value = float(data['stake']) / math.pow(10.0, SNAPSHOT_DECIMALS) * float(SNAPSHOT_PRICE)
        data['stake_value'] = value
        # check min max conditions
        if value < SNAPSHOT_STAKING_MINIMUM:
            continue
        if value > float(SNAPSHOT_STAKING_MAXIMUM):
            data['eligible_stake'] = int(float(SNAPSHOT_STAKING_MAXIMUM) / SNAPSHOT_PRICE * math.pow(10.0, SNAPSHOT_DECIMALS))
        else:
            data['eligible_stake'] = data['stake']
        total_eligible_stake += data['eligible_stake']
        amount_airdrop_receivers += 1
        
    for addr, data in airdrop_amounts.items():
        airdrop_amounts[addr]['airdrop_share'] = float(data['eligible_stake']) / float(total_eligible_stake)
        airdrop_amounts[addr]['airdrop_amount'] = float(data['eligible_stake']) * (float(AIRDROP_AMOUNT) / float(total_eligible_stake))

    print(f"Total staked: {total_stake} {SNAPSHOT_CHAIN_TOKEN}")
    print(f"Total eligible staked: {total_eligible_stake} {SNAPSHOT_CHAIN_TOKEN}")
    print(f"Amount of stakers: {len(airdrop_amounts)}")
    print(f"Amount of stakers with eligible stake: {amount_airdrop_receivers}")

    

# ====================
def save_commands_to_file(filename='commands.sh'):
    if len(airdrop_amounts) == 0:
        # print("No airdrop amounts to save!")
        return

    with open(os.path.join(balances_dir, filename), 'w') as f:
        output = []
        for addr, amount in airdrop_amounts.items():                      
            s = GENESIS_CMD_FORMAT.replace('ADDR', addr).replace('COIN', f'{amount}{NEW_CHAIN_TOKEN}')            
            output.append(s)
        f.write('\n'.join(output))

def save_to_csv(filename='airdrop.csv'):
    if len(airdrop_amounts) == 0:
        # print("No airdrop amounts to save!")
        return

    with open(os.path.join(balances_dir, filename), 'w') as f:
        writer = csv.writer(f)
        writer.writerow(['address', 'stake ' + SNAPSHOT_CHAIN_TOKEN, 'stake_value $', 'eligible_stake ' + SNAPSHOT_CHAIN_TOKEN, 'airdrop_share', 'airdrop_amount ' + NEW_CHAIN_TOKEN])
        for addr, data in airdrop_amounts.items():
            writer.writerow([addr, data['stake'], data['stake_value'], data['eligible_stake'], data['airdrop_share'], data['airdrop_amount']])

def test():
    addresses = [
        'celestia195asgku87kxgu48s447z0ryhsyn5rl3y95m9ju',
        'cosmos195asgku87kxgu48s447z0ryhsyn5rl3y5724g3',
        'juno195asgku87kxgu48s447z0ryhsyn5rl3yzvfw0d',
        'osmo195asgku87kxgu48s447z0ryhsyn5rl3yu9e97r',
        'chihuahua195asgku87kxgu48s447z0ryhsyn5rl3yht8mfn',
        'inj1h0ypsdtjfcjynqu3m75z2zwwz5mmrj8rtk2g52',
    ]
    for addr in addresses:
        hrp, converted = bech32decode(addr)
        print(addr, hrp, converted)
        # print(bech32encode('inj', converted)) 

if __name__ == '__main__':
    test()
    # main()    