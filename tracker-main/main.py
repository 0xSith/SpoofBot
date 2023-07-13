
from helper import *
from dotenv import load_dotenv

# Create a .env file with the variable names below and
# update with your own Etherscan and BscScan API keys and Telegram bot token

load_dotenv()

TELEGRAM_BOT_TOKEN = os.environ.get("TelegramBotToken")


# Define the command handlers for the Telegram bot
def start(update, context):
    message = """


👋 Welcome to the Ethereum and Binance Wallet Monitoring Bot!

Use /add <blockchain> <wallet_address> to add a new wallet to monitor.

Example: /add ETH 0x123456789abcdef

Use /remove <blockchain> <wallet_address> to stop monitoring a wallet.

Example: /remove ETH 0x123456789abcdef

Use /list <blockchain> to list all wallets being monitored for a specific blockchain.

Example: /list ETH or just /list

    """
    context.bot.send_message(chat_id=update.message.chat_id, text=message)



#Creates add function apply
def add(update, context):
    #if there are not enough informations/arguments as update and context return ERORR
    if len(context.args) < 2:
        context.bot.send_message(chat_id=update.message.chat_id, text="Please provide a blockchain + Wallet address + Name + address type.\n->Example: /add blockchain 0xadress WalletName (blockchain will be set as ETH if not provided)")
        return


    if len(context.args[0]) > 4:
    #converts the blockchain name to lowercase for consistency.
        blockchain = "eth"
        #Assigns the second argument (context.args[1]) to the wallet_address variable.
        wallet_address = context.args[0]
        #Assigns the third argument (context.args[2]) to the wallet_name variable.
        wallet_name = ' '.join(context.args[1:]).strip()
        #Assigns the forth argument to the walletType variable with the address user input (wallet_address = context.args[1])
        wallet_type = (checkAdress(context.args[0])).lower()
            
    
    else: 
        blockchain = context.args[0].lower()
        #Assigns the second argument (context.args[1]) to the wallet_address variable.
        wallet_address = context.args[1]
        #Assigns the third argument (context.args[2]) to the wallet_name variable.
        wallet_name = ' '.join(context.args[2:]).strip()
        #Assigns the forth argument to the walletType variable with the address user input (wallet_address = context.args[1])
        wallet_type = (checkAdress(context.args[1])).lower()



    if blockchain == 'eth':
        if not re.match(r'^0x[a-fA-F0-9]{40}$', wallet_address):
            context.bot.send_message(chat_id=update.message.chat_id, text=f"{wallet_address} is not a valid Ethereum wallet address.")
            return
    elif blockchain == 'bnb':
        if not re.match(r'^0x[a-fA-F0-9]{40}$', wallet_address):
            context.bot.send_message(chat_id=update.message.chat_id, text=f"{wallet_address} is not a valid Binance Smart Chain wallet address.")
            return
        # If the wallet address is not in the correct format, 
        # it sends a message indicating that the address is not valid for the specified blockchain and returns.
    else:
        context.bot.send_message(chat_id=update.message.chat_id, text=f"Invalid blockchain specified: {blockchain}")
        return
        
    #If all the validation checks pass, it calls the add_wallet function with the wallet_address 
    # and blockchain as arguments to add the wallet to the list of watched wallets.
    add_wallet(wallet_address, blockchain, wallet_name, wallet_type)
    #it sends a message indicating that the wallet address has been added to the list of watched wallets.
    message = f'Added {wallet_type} {wallet_name} to the list of watched {blockchain.upper()} wallets.'
    context.bot.send_message(chat_id=update.message.chat_id, text=message)
        

def remove(update, context):

    wallet_delete = ' '.join(context.args[0:]).strip()

    with open("watched_wallets.txt", "r") as file:
        lines = file.readlines()

    # loop thru the watched_wallet.txt to see if the wallet exist or not
    for index, line in enumerate(lines):
        blockchain, wallet_address, wallet_name = line.strip().split(":")
        if wallet_delete == wallet_address or wallet_delete == wallet_name:
            message = f'Removed {wallet_delete} from the list of watched wallets.'
            remove_wallet(wallet_delete)
            break
        else:
            message = f'Wallet {wallet_delete} not found.'


    context.bot.send_message(chat_id=update.message.chat_id, text=message)






def list_wallets(update, context):
    #read watched_wallets.txt as variable f
    with open("watched_wallets.txt", "r") as f:
        # creates a list of wallets by strip() each line in the file.
        wallets = [line.strip() for line in f.readlines()]
    #checks if the wallets list is not empty using the if wallets: condition.
    if wallets:
        eth_wallets = []
        bnb_wallets = []
        #iterates over each wallet in the wallets list and splits it into blockchain and wallet_address
        for wallet in wallets:
            #using the colon (:) as the separator.
            blockchain, wallet_address, wallet_name = wallet.split(':')
            # appends the wallet_address to the corresponding blockchain list (ETH OR BNB)
            if blockchain == 'eth':
                #store wallet_addy and name into eth_wallet[] or bnb_wallet[] array
                eth_wallets.append((wallet_address, wallet_name))
            elif blockchain == 'bnb':
                bnb_wallets.append((wallet_address, wallet_name))


        message = "The following wallets are currently being monitored\n"
        message += "\n"
        #sends the constructed message as a text message to the chat using the context.bot.send_message method

        #check if the wallets is not empty
        if eth_wallets:
            message += "Ethereum Wallets:\n"
            #The enumerate function returns both the index i
            # and the value wallet_address, wallet_name for each element in the list.
            for i, (wallet_address, wallet_name) in enumerate(eth_wallets):  # Unpack the tuple
                #adds a line to the message string with the wallet number (index + 1) followed by a dot,
                # the wallet address, and a new line character.
                message += f"{i+1}. {wallet_address} as {wallet_name}\n"
            message += "\n"
        if bnb_wallets:
            message += "Binance Coin Wallets:\n"
            for i, (wallet_address, wallet_name) in enumerate(eth_wallets):
                message += f"{i+1}. {wallet_address} as {wallet_name} \n"
        context.bot.send_message(chat_id=update.message.chat_id, text=message)
    else:
        #If the wallets list is empty, indicating that there are no wallets being monitored,
        #  it sends a message indicating that there are no wallets currently being monitored.
        message = "There are no wallets currently being monitored."
        context.bot.send_message(chat_id=update.message.chat_id, text=message)





# Set up the Telegram bot
from telegram.ext import Updater, CommandHandler

updater = Updater(token=TELEGRAM_BOT_TOKEN, use_context=True)
dispatcher = updater.dispatcher

# Define the command handlers
start_handler = CommandHandler('start', start)
add_handler = CommandHandler('add', add)
remove_handler = CommandHandler('remove', remove)
list_handler = CommandHandler('list', list_wallets)

# Add the command handlers to the dispatcher
dispatcher.add_handler(start_handler)
dispatcher.add_handler(add_handler)
dispatcher.add_handler(remove_handler)
dispatcher.add_handler(list_handler)

updater.start_polling()
print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Telegram bot started.")

print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Monitoring wallets...")
monitor_wallets()
