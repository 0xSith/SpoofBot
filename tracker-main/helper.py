import os.path
import json
import requests
import time
import re
from web3 import Web3
from dotenv import load_dotenv
import hyperlink
import telegram
import pyperclip
from telegram import ParseMode


load_dotenv()

ETHERSCAN_API_KEY = os.environ.get("EtherscanAPI")
BSCSCAN_API_KEY = os.environ.get("BscScanAPI")
TELEGRAM_BOT_TOKEN = os.environ.get("TelegramBotToken")
TELEGRAM_CHAT_ID = os.environ.get("TelegramChatID")
AlCHEMY_KEY = os.environ.get("AlchemyKey")



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

def checkTxnType(methodId,TransferOut):
    swap = ["0x791ac947","0xb6f9de95","0x12aa3caf"]
    approveOrRevoke = "0x095ea7b3"
    execute = "0x3593564c"
    transferOrReceived = "0x"
    updateState = "0x77552641"

    
    if methodId in swap:
        return "Swap"
    if methodId == approveOrRevoke:
        return "⭐ Approve"
        # return "⭐ Approve Or Revoke"
    if methodId == execute:
        return "Execute"
    if methodId == transferOrReceived:
        if TransferOut == 0:
            return "Received"
        else:
            return "Transfer Out"
    if methodId == updateState:
        return "UpdateState"
    else:
        return "new type - " + methodId



# Define some helper functions, HANNDLE respond within wallet
def get_wallet_transactions(wallet_address, blockchain, wallet_name):
    if blockchain == 'eth':
        url = f'https://api.etherscan.com/api?module=account&action=txlist&address={wallet_address}&sort=desc&apikey={ETHERSCAN_API_KEY}'
        # url_log = f'https://api.etherscan.io/api?module=account&action=tokentx&address={wallet_address}&startblock=0&endblock=999999999&sort=asc&apikey={ETHERSCAN_API_KEY}'
    elif blockchain == 'bnb':

        url = f'https://api.bscscan.com/api?module=account&action=txlist&address={wallet_address}&sort=desc&apikey={BSCSCAN_API_KEY}'
    else:
        raise ValueError('Invalid blockchain specified')



    #The function then sends a GET request to the API URL using
    #The requests.get() function and assigns the response to the response variable.
    response = requests.get(url)

    #Base on response above and run text through it
    data = json.loads(response.text)


    # response2 = requests.get(url_log)
    # data_log = json.loads(response2.text)

    #If the key 'result' exists in the data dictionary, it assigns the corresponding value to the result variable.
    #If the key 'result' doesn't exist in the data dictionary, it assigns an empty list ([]) as the default value for result.
    #Fetch data from API and storage in result?
    result = data.get('result', [])
    
    # print(data_log)
    #This line checks if the variable result is not an instance of the list class.
    #If result is not a list, it indicates an error in fetching the transactions.
    #       This could happen if the API response doesn't contain the expected data structure.
    if not isinstance(result, list):
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Error fetching transactions for {wallet_name} on {blockchain.upper()} blockchain: {data}")
        return []

    return result






#HANDLE TELEGRAM with 4 args
def send_telegram_notification(wallet_address, message, value, usd_value, tx_hash, blockchain, tx_methodId,TransferOut):
    #Determind which blockchain is in use with a specific output.
    if blockchain == 'eth':
        etherscan_link = f'<a href="https://etherscan.io/tx/{tx_hash}">TXN</a>'
    elif blockchain == 'bnb':
        etherscan_link = f'<a href="https://bscscan.com/tx/{tx_hash}">Bsc</a>'
    else:
        raise ValueError('Invalid blockchain specified')

    #save telegram message command in URL with f-string literal (type of string that can be pass value in)
    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'


    #fetch DexScreener URL for the transaction
    DexScreener_link = f'<a href="https://dexscreener.com/ethereum/{wallet_address}">CHART</a>'
    
    #this will be the format send to the telegram
        #-                         --FLASHBOT--                             -
        #⬅️ IN     " exchange in something " 
        #➡️  OUT " exchange out something " 
        #💱 : 0.029735740650255683 ETH ($57.7284)
        # TXN             CHART               BOT

    tx_Type = checkTxnType(tx_methodId,TransferOut)

    telegramMessage = f'- \
                        --{message}-- \
                            -\n------------------------------------------------------------------------------------\n💱 : {value} {blockchain.upper()} (${usd_value:.4f})\n🟢 IN:     " exchange in something " \
    -    {tx_Type}\n🔴 OUT: " exchange out something "\n------------------------------------------------------------------------------------\n {etherscan_link} \
                     {DexScreener_link}        \
                 BOT     \n'
    
    #Wallet that can be copy by a click
    walletAddressCopy = f'<code>{wallet_address}</code>'

    combined_message = f'{telegramMessage}\n{walletAddressCopy}'
    #use to send format message, created to specify the chat ID, text message, and other parameters and storage in payload
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': telegramMessage + '\n\n' + walletAddressCopy,
        'parse_mode': ParseMode.HTML,
        'disable_web_page_preview': True
    }

    # payload = {'chat_id': f'{TELEGRAM_CHAT_ID}', 'text': {telegramMessage}, 'parse_mode': 'HTML' }
    # used to send a POST request to the Telegram API with the constructed URL and payload
    response = requests.post(url, data=payload)

    # used to send a wallet adddress as a second message that can be copy by clicked on it
    # payload2 = {'chat_id': f'{TELEGRAM_CHAT_ID}', 'text': {walletAddressCopy}, 'parse_mode': telegram.ParseMode.MARKDOWN }
    # send out the message contain wallet address that can be copy by click on it
    # response2 = requests.post(url, data=payload2)

    # payload = {'chat_id': f'{TELEGRAM_CHAT_ID}', text=combined_message, parse_mode=telegram.ParseMode.HTML}

    #prints a confirmation message with the current timestamp and the content of the notification message and returns the response object.
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}]\n Telegram notification sent with message: {message} \n-> Value : {value} {blockchain.upper()} (${usd_value:.2f})\n-> Address : {etherscan_link}\n")

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
                    #
                    tx_methodId = tx["methodId"]
                    tx_from = tx["from"]
                    tx_to = tx["to"]
                    


                    # checks if it is a new transaction by comparing the transaction hash with the latest_tx_hashes dictionary.
                    #AND
                    # If new transaction and the transaction time is greater than last_run_time,
                    # it determines if it is an incoming or outgoing transaction based on the wallet address.
                    if tx_hash not in latest_tx_hashes and tx_time > last_run_time:

                        if tx['to'].lower() == wallet_address.lower():
                            TransferOut = 0
                            # Convert from wei to ETH or BNB
                            value = float(tx['value']) / 10**18
                            usd_value = value * (eth_usd_price if blockchain == 'eth' else bnb_usd_price) # Calculate value in USD
                            # message = f'\n⬅️🚨 Incoming   transaction detected 🚨\n->📬 : {wallet_name} @ {wallet_address}'

                            #new message that generate a Wallet name as a Hyperlink that user can click
                            message = f'<a href="https://etherscan.io/address/{wallet_address}">{wallet_name}</a>'

                            send_telegram_notification(wallet_address, message, value, usd_value, tx['hash'], blockchain, tx_methodId,TransferOut)
                            #print(f'\n{message}, Value: {value} {blockchain.upper()}, ${usd_value:.2f}\n')

                        elif tx['from'].lower() == wallet_address.lower():
                            TransferOut = 1
                            # Convert from wei to ETH or BNB
                            value = float(tx['value']) / 10**18
                            usd_value = value * (eth_usd_price if blockchain == 'eth' else bnb_usd_price) # Calculate value in USD
                            # message = f'\n➡️ 🚨 Outgoing  transaction detected 🚨\n->📬 : {wallet_name} @ {wallet_address}'
                            message = f'<a href="https://etherscan.io/address/{wallet_address}">{wallet_name}</a>' 
                            send_telegram_notification(wallet_address, message, value, usd_value, tx['hash'], blockchain, tx_methodId,TransferOut)
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
