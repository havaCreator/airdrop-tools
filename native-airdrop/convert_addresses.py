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


converted_dir = os.path.join(parent_dir, "_CONVERSIONS")
os.makedirs(converted_dir, exist_ok=True)

TARGET_CHAIN_PREFIX = os.getenv('TARGET_CHAIN_PREFIX', "osmo")
CONVERTION_INPUT_FILE = os.path.join(converted_dir, os.getenv('CONVERTION_INPUT_FILE', ""))
CONVERTION_OUTPUT_FILE = os.path.join(converted_dir, os.getenv('CONVERTION_OUTPUT_FILE', ""))
CONVERT_INPUT_COLUMN = os.getenv('CONVERT_INPUT_COLUMN', "")
CONVERT_OUTPUT_COLUMN = os.getenv('CONVERT_OUTPUT_COLUMN', "")

# list of groups of chains with the same key derivation path
# others can not be converted
SUPPORTED_CONVERSIONS = [
    ['celestia', 'cosmos', 'juno', 'osmo', 'chihuahua', 'neutron', 'persistence', 'quick', 'stride', 'stars'],
    ['inj', 'dym'],
    ['agoric'],
]

def main():    
    convert()


def convert(): 
    headers = []
    entries = []

    # find group of supported prefixes
    supported_prefixes = []
    for group in SUPPORTED_CONVERSIONS:
        if TARGET_CHAIN_PREFIX in group:
            supported_prefixes = group
            break
    if len(supported_prefixes) == 0:
        print(f"Conversion to {TARGET_CHAIN_PREFIX} not known!")
        return
    print(TARGET_CHAIN_PREFIX, "can be converted between", supported_prefixes)

    with open(CONVERTION_INPUT_FILE, 'r') as f:
        reader = csv.reader(f)
        headers = reader.__next__()

        for row in reader:
            address = row[headers.index(CONVERT_INPUT_COLUMN)]
            hrp, converted = bech32decode(address)
            if hrp not in supported_prefixes:
                print(f"Address {address} can not be converted to {TARGET_CHAIN_PREFIX}!")
                return
            target_addr = bech32encode(TARGET_CHAIN_PREFIX, converted)
            print(address, "to", target_addr) 

            entries.append(row + [target_addr])
    
    headers.append(CONVERT_OUTPUT_COLUMN)

    with open(CONVERTION_OUTPUT_FILE, 'w') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for row in entries:
            writer.writerow(row)
    
    print(f"Saved to '{CONVERTION_OUTPUT_FILE}'")


def test():
    addresses = [
        # 'celestia195asgku87kxgu48s447z0ryhsyn5rl3y95m9ju',
        # 'cosmos195asgku87kxgu48s447z0ryhsyn5rl3y5724g3',
        # 'juno195asgku87kxgu48s447z0ryhsyn5rl3yzvfw0d',
        # 'osmo195asgku87kxgu48s447z0ryhsyn5rl3yu9e97r',
        # 'chihuahua195asgku87kxgu48s447z0ryhsyn5rl3yht8mfn',
        # 'inj1h0ypsdtjfcjynqu3m75z2zwwz5mmrj8rtk2g52',
        # 'agoric1wmjfhcdl6d5wqq56k7qdy7zk9wnstmqezqpqyp',
        # 'dym1h0ypsdtjfcjynqu3m75z2zwwz5mmrj8rnz32ru',
        # 'neutron195asgku87kxgu48s447z0ryhsyn5rl3ysprhjk',
        # 'persistence195asgku87kxgu48s447z0ryhsyn5rl3y6jvxx4',
        # 'quick195asgku87kxgu48s447z0ryhsyn5rl3yl6683r',
        # 'stride195asgku87kxgu48s447z0ryhsyn5rl3yh42fua',
        # 'stars195asgku87kxgu48s447z0ryhsyn5rl3yqzagrq',
        # 'osmo17txgrugvf4snxrxladf8v9ge8lw2n4hjq2j79z',
        # 'inj1ynrh862r4nq0e0uav09uk6ku5yxt9k8jkt0y2j',
        # 'agoric18j75nrrx765xx73gdrhu4d90hkkkrmfwss57td',
        'osmo1mcc4uk8e8x7ylk4v60g3yadkz4fs6ky9nzfxxl',
    ]
    for addr in addresses:
        hrp, converted = bech32decode(addr)
        print(converted, hrp, addr)
        print(bech32encode('osmo', converted)) 

if __name__ == '__main__':
    # test()
    main()    