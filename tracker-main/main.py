

from helper import *
from dotenv import load_dotenv


load_dotenv()

TELEGRAM_BOT_TOKEN = os.environ.get("TelegramBotToken")


#Start interface of Spoof Bot in Telegram

def start(update, context):
    message = """


👋 Welcome to the Spoof Monitoring Bot!

Use /add <blockchain (optional)> <address> <name> to add a new address to monitor.

Example: /add eth 0x123456789abcdef Whale Wallet

Use /remove <address> or <name> to stop monitoring an address.

Example: /remove $PEPE

Use /list <blockchain> to list all addresses being monitored for a specific blockchain.

Example: /list ETH or just /list

    """
    context.bot.send_message(chat_id=update.message.chat_id, text=message)


#telegram add command
#input: blockchain {optional}, address, name


#THIS FUNCTION USE TO READ INPUT FROM USER
def add(update, context):

    message_text = update.message.text
    #split down each line of the message (if any)
    lines = message_text.split('\n')
    #set lineNumber = 0 to determind if it is multiple addresses or 1 address
    lineNumber = 0
    #set addressNumber = 0 to keep track how many address(es) being add.
    addressAddedCount = 0
    

    #count lineNumber of message for different address addition case. 
    #           Either 1 address (1 line) or Multiple address (1+ line)
    for line in lines:
        lineNumber+= 1


    #if user input format is wrong
    if len(context.args) < 2:
        context.bot.send_message(chat_id=update.message.chat_id, text="Please provide a blockchain (optional) + address + name\n->Example: /add chain (default:eth) address name")
        return

    #if user input in default case
    if len(context.args[0]) > 4:

        #CASE OF 1 ADDRESS
        if lineNumber == 1 :
            words = line.split()
                        #check user input 
            if len(words) >= 2:
                #Wallet information
                blockchain = "eth" #block chain is set default with eth
                address = words[1]
                name = words[2]
                type = (checkAdress(address)).lower()
                duplicate = checkDuplicate(address)
                

                #CHECKING ADDRESS TYPE
                #ADDRESS ERRORS 
                if blockchain == 'eth' or blockchain == 'bnb' or blockchain == 'arb':
                    if not re.match(r'^0x[a-fA-F0-9]{40}$', address):
                        context.bot.send_message(chat_id=update.message.chat_id, text=f"{address} is not a valid address.")
                        return

                #if block isnt in the type we provide
                else:
                    context.bot.send_message(chat_id=update.message.chat_id, text=f"Invalid blockchain specified: {blockchain}")
                    return

            #if user input their own blockchain type
            else:
                #data value fit with the args[]
                blockchain = context.args[0].lower()
                address = context.args[1]
                name = ' '.join(context.args[2:]).strip()
                type = (checkAdress(context.args[1])).lower()
                duplicate = checkDuplicate(address)

                #do not need to check blockchain type and THEN format if all chains are EVM compatible
                # will have same format
                if blockchain == 'eth' or blockchain == 'bnb' or blockchain == 'arb':
                    if not re.match(r'^0x[a-fA-F0-9]{40}$', address):
                        context.bot.send_message(chat_id=update.message.chat_id, text=f"{address} is not a valid address.")
                        return

                #if block isnt in the type we provide
                else:
                    context.bot.send_message(chat_id=update.message.chat_id, text=f"Invalid blockchain specified: {blockchain}")
                    return

            #THIS FUNCTION READ AND ADD ADDRESS INTO WATCH LIST
            #if there is Duplicate
            if (duplicate): 
                message = f'The address above is already in the watch list'
                context.bot.send_message(chat_id=update.message.chat_id, text=message)
                return
            #if there is no Duplicate
            else :
                add_address(address, blockchain, name, type)
                message = f'Added {type} {name} to the list of watched {blockchain.upper()} addresses.'
                context.bot.send_message(chat_id=update.message.chat_id, text=message)
                return

        

        #CASE OF MORE THAN 1 ADDRESS
        if lineNumber > 1 :
            address_added = [ ]
            for line in lines:
            #split each line of lines into words
                words = line.split()
                
                #check user input 
                if len(words) >= 2:
                    #Wallet information
                    blockchain = 'eth' #blockchain is set default with eth
                    address = words[0]
                    name = words[1]
                    type = (checkAdress(words[0])).lower()

                    #check addess(es) if there is any duplicate and return True or False
                    duplicate = checkDuplicate(address)
                    


                    #CHECKING ADDRESS TYPE
                    #ADDRESS ERRORS 
                    if blockchain == 'eth' or blockchain == 'bnb' or blockchain == 'arb':
                        if not re.match(r'^0x[a-fA-F0-9]{40}$', address):
                            context.bot.send_message(chat_id=update.message.chat_id, text=f"{address} is not a valid address.")
                            return

                    #if block isnt in the type we provide
                    else:
                        context.bot.send_message(chat_id=update.message.chat_id, text=f"Invalid blockchain specified: {blockchain}")
                        return
                    
                    #if there is any duplicate address
                    if (duplicate):
                        message = f'All of the addresses above is already in watched list'
                        
                    #Add address and set message if no Duplicate
                    if (duplicate == False):
                        add_address(address,blockchain,name,type)
                        addressAddedCount += 1
                        address_added.append(name)
                        message = f'{addressAddedCount} addresses added successfully into the watch list \n{address_added}'
                    
        context.bot.send_message(chat_id=update.message.chat_id, text=message)
        return
        

                
            

def remove(update, context):

    address_delete = ' '.join(context.args[0:]).strip()

    with open("watched_addresses.txt", "r") as file:
        lines = file.readlines()


    for index, line in enumerate(lines):
        blockchain, address, name = line.strip().split(":")
        if address_delete == address or address_delete == name:
            message = f'Removed {address_delete} from the list of watched addresses.'
            remove_address(address_delete)
            break
        else:
            message = f'{type} {address_delete} not found.'


    context.bot.send_message(chat_id=update.message.chat_id, text=message)




#List command in telegram; outputs: addresses tracked.
#Seperates wallets and contracts

def list(update, context):

    with open("watched_addresses.txt", "r") as f:

        # creates a list of addresses by strip() each line in the file.
        #splits it into blockchain and address using the colon (:) as the separator.
        addresses = [line.strip() for line in f.readlines()]

    if addresses:
        eth_addresses = []
        bnb_addresses = []
        #create wallet and contract addresses string array to storage - address & name & message
        walletAddress = []
        contractAddress = []        
        walletName = []
        contractName = []
        messageContract = ""
        messageWallet = ""


        for i_address in addresses:
            blockchain, address, name, type = i_address.split(':')

            if blockchain == 'eth':
                eth_addresses.append((address, name,type))
            elif blockchain == 'bnb':
                bnb_addresses.append((address, name))

        message = "The following addresses are currently being monitored\n"
        



        if eth_addresses:
            message += "Ethereum Addresses:\n\n"

            #The enumerate function returns both the index i
            # and the value address, name for each element in the list.
            #Unpacks the tuple in message var
            for i, (address, name, type) in enumerate(eth_addresses):
                    #print message when /list command

                    #two type of address case : Wallet and Contract
                    #WALLET CASE
                    if (type == "wallet"): 
                        #setup data for wallet including name + Wallet address.
                        walletAddress.append(address)
                        walletName.append(name)
                        #shorten the Wallet address
                        walletChop = [(address[i:i+5]) for i in range(0, len(address), 5)]         
                        #message format               
                        messageWallet += f"{name}:{walletChop[0]}...{walletChop[len(walletChop)-2]}{walletChop[len(walletChop)-1]}\n"

                    #CONTRACT CASE
                    if (type == "contract"):
                        contractAddress.append(address)
                        #setup data for contract including name + Contract address.
                        contractName.append(name)
                        #shorten the Contract address
                        contractChop = [(address[i:i+5]) for i in range(0, len(address), 5)]
                        #message format
                        messageContract += f"${name}:{contractChop[0]}...{contractChop[len(contractChop)-2]}{contractChop[len(contractChop)-1]}\n"

        #Combined 2 messageContract and messageWallet into 1 message
        message += messageContract
        message += f"\n\n"
        message += messageWallet




        if bnb_addresses:
            message += "Binance Addresses:\n"
            for i, (address, name) in enumerate(bnb_addresses):
                message += f"{i+1}. {address} as {name} \n"
        
        #send out message
        context.bot.send_message(chat_id=update.message.chat_id, text=message)
    #If message error
    else:
        message = "There are no addresses currently being monitored."
        context.bot.send_message(chat_id=update.message.chat_id, text=message)


def edit(update, context):
    originalName = context.args[0]
    newName = context.args[1]

    changeName(originalName,newName)
    message = f'{originalName} is successfully changed to {newName}'
    context.bot.send_message(chat_id=update.message.chat_id, text=message)

    



# Initialization of telegram bot through telegram packages

from telegram.ext import Updater, CommandHandler

updater = Updater(token=TELEGRAM_BOT_TOKEN, use_context=True)
dispatcher = updater.dispatcher

start_handler = CommandHandler('start', start)
add_handler = CommandHandler('add', add)
remove_handler = CommandHandler('remove', remove)
list_handler = CommandHandler('list', list)
editName_handler = CommandHandler('editName', edit)

dispatcher.add_handler(start_handler)
dispatcher.add_handler(add_handler)
dispatcher.add_handler(remove_handler)
dispatcher.add_handler(list_handler)
dispatcher.add_handler(editName_handler)

updater.start_polling()
print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Telegram bot started.")

print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Monitoring addresses...")
spoof_monitor()
