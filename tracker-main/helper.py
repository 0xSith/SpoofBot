import os.path
import json
import requests
import time
import re
from web3 import Web3
from dotenv import load_dotenv



load_dotenv()

ETHERSCAN_API_KEY = os.environ.get("EtherscanAPI")
BSCSCAN_API_KEY = os.environ.get("BscScanAPI")
TELEGRAM_BOT_TOKEN = os.environ.get("TelegramBotToken")
TELEGRAM_CHAT_ID = os.environ.get("TelegramChatID")
AlCHEMY_KEY = os.environ.get("AlchemyKey")


# #ALCHEMY-API KEY
# AlchemyKey = "oF5h_6DhZgvo4-iQn1p2u67COdWJRyTf"

#function checkAddress to check either Wallet or Contract
#               with 1 parameter as transaction address
def checkAdress(address):
    #API request url
    url = "https://eth-mainnet.g.alchemy.com/v2/" + AlCHEMY_KEY
    
#SETTINGS:
    #payload with the trasaction address
    payload = {
        "id": 1,
        "jsonrpc": "2.0",
        "params": [address, "latest"],
        "method": "eth_getCode",
    }
    #header
    headers = {
        "accept": "application/json",
        "content-type": "application/json"
    }

    #Call/request API and save the result to response.
    response = requests.post(url, json=payload, headers=headers)
    
    #check condition to return the Wallet Type
    if len(response.text) > 38 :
        return("contract")
    else:
        return("wallet")




# Define some helper functions, HANNDLE respond within wallet
def get_wallet_transactions(wallet_address, blockchain, wallet_name):
    if blockchain == 'eth':
        url = f'https://api.etherscan.io/api?module=account&action=txlist&address={wallet_address}&sort=desc&apikey={ETHERSCAN_API_KEY}'
    elif blockchain == 'bnb':
        url = f'https://api.bscscan.com/api?module=account&action=txlist&address={wallet_address}&sort=desc&apikey={BSCSCAN_API_KEY}'
    else:
        raise ValueError('Invalid blockchain specified')

    #The function then sends a GET request to the API URL using
    #The requests.get() function and assigns the response to the response variable.
    response = requests.get(url)
    #Base on response above and run text through it
    data = json.loads(response.text)

    #If the key 'result' exists in the data dictionary, it assigns the corresponding value to the result variable.
    #If the key 'result' doesn't exist in the data dictionary, it assigns an empty list ([]) as the default value for result.
    result = data.get('result', [])

    #This line checks if the variable result is not an instance of the list class.
    #If result is not a list, it indicates an error in fetching the transactions.
    #       This could happen if the API response doesn't contain the expected data structure.
    if not isinstance(result, list):
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Error fetching transactions for {wallet_name} on {blockchain.upper()} blockchain: {data}")
        return []

    return result





#HANDLE TELEGRAM with 4 args
def send_telegram_notification(message, value, usd_value, tx_hash, blockchain):
    #Determind which blockchain is in use with a specific output.
    if blockchain == 'eth':
        etherscan_link = f'<a href="https://etherscan.io/tx/{tx_hash}">Etherscan</a>'
    elif blockchain == 'bnb':
        etherscan_link = f'<a href="https://bscscan.com/tx/{tx_hash}">BscScan</a>'
    else:
        raise ValueError('Invalid blockchain specified')

    #save telegram message command in URL with f-string literal (type of string that can be pass value in)
    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'

    #use to send format message, created to specify the chat ID, text message, and other parameters and storage in payload
    payload = {'chat_id': f'{TELEGRAM_CHAT_ID}', 'text': f'{message}: {etherscan_link}\nValue: {value:.6f} {blockchain.upper()} (${usd_value:.2f})',
               'parse_mode': 'HTML'}
    # used to send a POST request to the Telegram API with the constructed URL and payload
    response = requests.post(url, data=payload)
    #prints a confirmation message with the current timestamp and the content of the notification message and returns the response object.
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Telegram notification sent with message: {message}, value: {value} {blockchain.upper()} (${usd_value:.2f})")
    return response




def monitor_wallets():
    #creates an empty set called watched_wallets.
    watched_wallets = set()

    #set file_path with watched_wallets.txt file and
    #check if that file has been created or exist
    #Specifies the file path where the watched wallet addresses will be stored.
    file_path = "watched_wallets.txt"
    if not os.path.exists(file_path):
        #if not exist, then creating it.
        open(file_path, 'w').close()



    #Then setup an empty dictionary called latest_tx_hashes
    #    and assigns the path "latest_tx_hashes.json" to the latest_tx_hashes_path variable.
    # store the latest transaction hashes.
    latest_tx_hashes = {}
    latest_tx_hashes_path = "latest_tx_hashes.json" #storage the latest transaction
    #check if latest_tx_hashes_path exist
    if os.path.exists(latest_tx_hashes_path):
        #If it is exists then read it and called as variable "f"
        with open(latest_tx_hashes_path, "r") as f:
            #read the file with json format from variable "f" above.
            latest_tx_hashes = json.load(f)


    last_run_time = 0 #initialize
    last_run_time_path = "last_run_time.txt"

    #check if last_run_time_path path exist or not.
    if os.path.exists(last_run_time_path):
        #with open the file and read it as variable "f"
        #with open help automatically close file as it done.
        with open(last_run_time_path, "r") as f:
            #Reads the contents of the file using f.read() and converts it to an integer using int().
            # The resulting value is assigned to last_run_time.
            last_run_time = int(f.read())



    while True:
        try:
            # Fetch current ETH and BNB prices in USD from CoinGecko API
            #Inside the loop, the code fetches the current ETH and BNB prices in USD from the CoinGecko API.
            eth_usd_price_url = 'https://api.coingecko.com/api/v3/simple/price?ids=ethereum%2Cbinancecoin&vs_currencies=usd'
            response = requests.get(eth_usd_price_url)
            data = json.loads(response.text)
            eth_usd_price = data['ethereum']['usd']
            bnb_usd_price = data['binancecoin']['usd']

            # It reads the watched wallet addresses from the watched_wallets.txt file and updates the watched_wallets set.
            with open(file_path, 'r') as f:
                watched_wallets = set(f.read().splitlines())

            #For each wallet address in watched_wallets,
            # it retrieves the transactions using the get_wallet_transactions function.
            for wallet in watched_wallets:
                blockchain, wallet_address, wallet_name = wallet.split(':')
                transactions = get_wallet_transactions(wallet_address, blockchain, wallet_name)
                for tx in transactions:
                    tx_hash = tx['hash']
                    tx_time = int(tx['timeStamp'])

                    # checks if it is a new transaction by comparing the transaction hash with the latest_tx_hashes dictionary.
                    #AND
                    # If new transaction and the transaction time is greater than last_run_time,
                    # it determines if it is an incoming or outgoing transaction based on the wallet address.
                    if tx_hash not in latest_tx_hashes and tx_time > last_run_time:

                        if tx['to'].lower() == wallet_address.lower():
                            # Convert from wei to ETH or BNB
                            value = float(tx['value']) / 10**18
                            usd_value = value * (eth_usd_price if blockchain == 'eth' else bnb_usd_price) # Calculate value in USD
                            message = f'🚨 Incoming transaction detected on {wallet_address}'
                            send_telegram_notification(message, value, usd_value, tx['hash'], blockchain)
                            #print(f'\n{message}, Value: {value} {blockchain.upper()}, ${usd_value:.2f}\n')

                        elif tx['from'].lower() == wallet_address.lower():
                            # Convert from wei to ETH or BNB
                            value = float(tx['value']) / 10**18
                            usd_value = value * (eth_usd_price if blockchain == 'eth' else bnb_usd_price) # Calculate value in USD
                            #sends the notification message using the send_telegram_notification function
                            message = f'🚨 Outgoing transaction detected on {wallet_address}'
                            send_telegram_notification(message, value, usd_value, tx['hash'], blockchain)
                            #print(f'\n{message}, Value: {value} {blockchain.upper()}, ${usd_value:.2f}\n')


                        latest_tx_hashes[tx_hash] = int(tx['blockNumber'])

            #SAVE FILES AFTERWARD. Updates the latest_tx_hashes dictionary with the new transaction hash.
            # Save latest_tx_hashes to file
            with open(latest_tx_hashes_path, "w") as f:
                json.dump(latest_tx_hashes, f)

            # Update last_run_time
            last_run_time = int(time.time())
            with open(last_run_time_path, "w") as f:
                f.write(str(last_run_time))

            # Sleep for 1 minute after everything
            time.sleep(60)

        #CASE THAT CANCEL THE LOOP
        except Exception as e:
                print(f'An error occurred: {e}')
                # Sleep for 10 seconds before trying again
                time.sleep(10)


#Creates add_wallet function apply
#       4 params which including wallet_addy, blockchain, name, address
def add_wallet(wallet_address, blockchain, name, walletType):
    file_path = "watched_wallets.txt"
    #wallet_type will storage the wallet type [could be contract or wallet]
    #statement to open the file in append mode
    with open(file_path, 'a') as f:
        #  f.write(f'{blockchain}:{wallet_address}\n'): Writes the formatted string
        #                                {blockchain}:{wallet_address}\n to the file f.
        #  The f-string allows you to embed the values of blockchain and wallet_address in the string. 
        #  The '\n' adds a newline character at the end of the line.
        f.write(f'{blockchain}:{wallet_address}:{name}\n')



#create remove_wallet function
def remove_wallet(wallet_address, blockchain,wallet_name):
    file_path = "watched_wallets.txt"
    temp_file_path = "temp.txt"

    #open and read file_path, at same time and with open will close when its over,
    #open and write temp_file_path
    with open(file_path, 'r') as f, open(temp_file_path, 'w') as temp_f:
        #iterates over each line in original file
        for line in f:
            #Writes the line to the temporary file temp_f if it doesn't match the wallet address.
            if line.strip() != f'{blockchain}:{wallet_address}:{wallet_name}':
                temp_f.write(line)
    #Replaces the original file with the temporary file. This effectively removes the wallet address from the original file.
    os.replace(temp_file_path, file_path)
