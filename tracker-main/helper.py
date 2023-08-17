import os.path
import json
import requests
import time
import re
from dotenv import load_dotenv
from web3 import Web3
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


load_dotenv()

ETHERSCAN_API_KEY = os.environ.get("EtherscanAPI")
BSCSCAN_API_KEY = os.environ.get("BscScanAPI")
TELEGRAM_BOT_TOKEN = os.environ.get("TelegramBotToken")
TELEGRAM_CHAT_ID = os.environ.get("TelegramChatID")
AlCHEMY_KEY = os.environ.get("AlchemyKey")




#function to check either Wallet or Contract

def checkAdress(address):
    url = "https://eth-mainnet.g.alchemy.com/v2/" + AlCHEMY_KEY

    payload = {
        "id": 1,
        "jsonrpc": "2.0",
        "params": [address, "latest"],
        "method": "eth_getCode",
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)

    #Condition to return Type

    if len(response.text) > 38 :
        return("contract")
    else:
        return("wallet")


# Fetches addresses transactions through *chain*scan API by address & name, optionally assigning blockchain (default:eth).
#Helper of monitor function

def fetch_txns(address, blockchain, name, type, last_run_time):

    topic0 = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'

    block_url = f'https://api.etherscan.io/api?module=block&action=getblocknobytime&timestamp={last_run_time}&closest=before&apikey={ETHERSCAN_API_KEY}'
    response = requests.get(block_url)
    block_data = json.loads(response.text)
    block_number = int(block_data['result'])


    if blockchain == 'eth':
        token = ETHERSCAN_API_KEY
        chain = 'etherscan.io'

    elif blockchain =='bsc' or blockchain == 'bnb':
        token = BSCSCAN_API_KEY
        chain = 'bscan.com'

    elif blockchain == 'arb':
        # token = ARBSCAN_API_KEY
        chain = 'arbscan.io'
    else:
        raise ValueError('Invalid blockchain specified')

    url = f'https://api.{chain}/api?module=logs&action=getLogs&page=1&fromBlock={block_number}&address={address}&topic0={topic0}&apikey={token}'
    response = requests.get(url)
    data = json.loads(response.text)

    #Check if variable result is not an instance of list class.
    #If result is not a list, indicates an error in fetching the txns.
    if response.status_code > 300:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Error fetching transactions for {name} on {blockchain.upper()} /n Error: {response}")
        return []
    return data.get('result')


#Send a telegram notification of the user interaction and a preset formatted message

def post_telegram(message, value, usd_value, tx_hash, blockchain):

    if blockchain == 'eth':
        chainscan_link = f"https://etherscan.io/tx/{tx_hash}"
    elif blockchain == 'bnb':
        chainscan_link = f'<a href="https://bscscan.com/tx/{tx_hash}">BscScan</a>'
    else:
        raise ValueError('Invalid blockchain specified')


# Create the inline keyboard buttons
    buttons = [
        [InlineKeyboardButton("Etherscan", url = chainscan_link),
         InlineKeyboardButton("Option 2", url="https://example.com/option2"),
         InlineKeyboardButton("Option 3", url="https://example.com/option3")]
    ]
    keyboard = InlineKeyboardMarkup(buttons)


    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'

    payload = {
        'chat_id': f'{TELEGRAM_CHAT_ID}',
        'text': f'{message}',
        'parse_mode': 'HTML',
        'reply_markup': keyboard.to_json()
    }

    response = requests.post(url, data=payload)
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Telegram notification sent with message: {message}, value: {value} {blockchain.upper()} (${usd_value:.2f})")
    return response


#Start monitoring addresses; turning "ON" the Spoof Bot to monitor.

def spoof_monitor():

    watched_addresses = set()
    file_path = "watched_addresses.txt"
    if not os.path.exists(file_path):
        open(file_path, 'w').close()


    last_run_time = int(time.time())

    time_tracker_path = "time_tracker.txt"

    with open(time_tracker_path, "w") as f:
        f.write(str(last_run_time))


    #Monitor continously
    while True:
        try:
            # Fetch current ETH and BNB prices in USD from CoinGecko API

            eth_usd_price_url = 'https://api.coingecko.com/api/v3/simple/price?ids=ethereum%2Cbinancecoin&vs_currencies=usd'
            response = requests.get(eth_usd_price_url)
            data = json.loads(response.text)
            eth_usd_price = data['ethereum']['usd']
            bnb_usd_price = data['binancecoin']['usd']

            with open(file_path, 'r') as f:
                watched_addresses = set(f.read().splitlines())
                #PRINT COMMENT OUT
                # print(watched_addresses)
            #For each address in watched_addresses,
            # it retrieves the transactions using the fetch_txns function.

            for i_address in watched_addresses:
                #PRINT COMMENT OUT
                # print(i_address)
                blockchain, address, name, type = i_address.split(':')
                transactions = fetch_txns(address, blockchain, name, type, last_run_time)


                # print(transactions)
                for tx in transactions:
                    print(tx)
                    tx_hash = tx['transactionHash']
                    tx_block_number = int(tx['blockNumber'],16)
                    tx_time = int(tx['timeStamp'],16)
                    tx_to = tx['topics'][1]
                    tx_from = tx['topics'][2]
                    value = float(int(tx['data'],16)) / 10**18
                    usd_value = value * (eth_usd_price if blockchain == 'eth' else bnb_usd_price)


                    #validates new transaction by comparing block number > latest block number
                    # and time > last run time.

                    #PRINT COMMENT OUT
                    # print(tx['topics'][1])

                    if tx_time >= last_run_time:
                        print("tx time pass successful")
                        if tx_to.lower() == address.lower():
                            print("address to check")
                            message = f'🚨 Incoming transaction detected on {address}'
                            post_telegram(message, value, usd_value, tx_hash, blockchain)

                        elif tx_from.lower() == address.lower():
                            print("address from check")
                            message = f'🚨 Outgoing transaction detected on {address}'
                            post_telegram(message, value, usd_value, tx_hash, blockchain)

                    #PRINT COMMENT OUT
                    # print("iterate tx")
                time.sleep(1)

            last_run_time = int(time.time())
            with open(time_tracker_path, "w") as f:
                f.write(str(last_run_time))

            time.sleep(10)

        #Catch error

        except Exception as e:
                print(f'An error occurred: {e}')
                time.sleep(10)


#Remove address and add address function handlers

#add address function will write down information file
def add_address(address, blockchain, name, type):
    file_path = "watched_addresses.txt"
    
    with open(file_path, 'a') as f:
        #open and append file with blockchain-address-name-type
        f.write(f'{blockchain}:{address}:{name}:{type}\n')

##checkDuplicate function will return true of false regarding duplicate address
def checkDuplicate(address):
    #create an array to storage current address in the list
    compareAddresses = [ ]
    #read the addresses list file
    file_path = "watched_addresses.txt"
    with open(file_path, 'r') as f2:
        for line in f2:
            #Add every address into the compareAddresses array
            words = line.split(':')
            compareAddresses.append(words[1])
    #If state to check if the added address is already in the watched list
    if address in compareAddresses: return True
    else: return False


def changeName(originalName, newName):
    file_path = "watched_addresses.txt"

    # Read the existing content of the file
    with open(file_path, 'r') as f:
        #lines = each line of the text file
        lines = f.readlines()

    # Modify the data in memory
    #create new array to storage any changes
    modified_lines = []
    for line in lines:
        words = line.strip().split(':')
        #check conditions
        if len(words) >= 4 and words[2] == originalName:
            #modified newName in the txt file
            words[2] = newName
            #put them into the right format and add them into the text
            modified_line = ':'.join(words) + '\n'
            modified_lines.append(modified_line)

        else:
            modified_lines.append(line)
            


    # Write the modified data back to the file
    with open(file_path, 'w') as f:
        f.writelines(modified_lines)


            


def remove_address(addy):

    with open("watched_addresses.txt", "r") as file:
        lines = file.readlines()


    for index, line in enumerate(lines):
        blockchain, address, name = line.strip().split(":")
        if addy == address or addy == name:
            del lines[index]
            break

    with open("watched_addresses.txt", "w") as file:
        file.writelines(lines)
