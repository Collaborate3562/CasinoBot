"""
First, a few callback functions are defined. Then, those functions are passed to
the Application and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.
Usage:
Example of a bot-user conversation using ConversationHandler.
Send /start to initiate the conversation.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

from json import JSONEncoder
import asyncio
import datetime
import json
import logging
import pyperclip
import threading
from web3 import Web3
from telegram import __version__ as TG_VER
from dotenv.main import load_dotenv
import os

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, "alpha", 5):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. To view the "
        f"{TG_VER} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )
from telegram import (
    ForceReply, 
    ReplyKeyboardRemove, 
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup, 
    CallbackQuery
)

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
    CallbackContext,
    # Updater,
    # Dispatcher
)

# from telebot import TeleBot

from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP

from libs.util import (
    #from util.py
    getPricefromAmount,
    roll,
    getUnitString,
    controlRandCard,
    getWallet,
    getBalance,
    deploySmartContract,
    transferAssetsToContract,
    
    #from db.py
    updateSetStrWhereStr,
    updateSetFloatWhereStr,
    readFieldsWhereStr
)

load_dotenv()

ETH_CONTRACT_ADDRESS = os.environ['ETH_CONTRACT_ADDRESS']
BSC_CONTRACT_ADDRESS = os.environ['BSC_CONTRACT_ADDRESS']
PRIVATE_KEY = os.environ['OWNER_PRIVATE_KEY']
INFURA_ID = os.environ['INFURA_ID']
BOT_TOKEN = os.environ['BOT_TOKEN']

# import mysql.connector

# db = mysql.connector.connect(host="localhost", user="root", passwd="bluesky0812", database="DB_AleekkCasino")

# cur = db.cursor()


# class DateTimeEncoder(JSONEncoder):
#     def default(self, obj):
#         if isinstance(obj, (datetime.date, datetime.datetime)):
#             return obj.isoformat()

CHOOSE, WALLET, SELECT, STATUS, PAYMENT, DEPOSIT, DISPLAY, COPY, LASTSELECT, AGAINSLOT, AGAINHILO, PANELHILO, PANELSLOT, BETTINGHILO, PANELDEPOSIT, PANELWITHDRAW = range(16)
ST_DEPOSIT, ST_WITHDRAW, ST_HILO, ST_SLOT = range(4)
ETH, BNB = range(2)

g_SlotMark = "🎰 SLOTS 🎰\n\n"
g_HiloMark = "♠️♥️ HILO ♦️♣️\n\n"
g_Cashout = 0
UserName = ""
UserId = ""
FullName = ""
isBot = True
# Test Token
TOKEN = BOT_TOKEN
g_Greetings = f"/start - Enter the casino\n"
g_Help = f"/help - Describe all guide\n"
g_Wallet = f"/wallet - Show all balances in your wallet\n"
g_Deposit = f"/deposit - Deposit ETH or BNB into your wallet\n"
g_Withdraw = f"/withdraw - Withdraw ETH or BNB from your wallet\n"
g_Hilo = f"/hilo - Play hilo casino game\n"
g_Slot = f"/slot - Play slot casino game\n"
g_LeaderBoard = f"/board - Show the leaderboard\n"
g_PrevCard = None
g_NextCard = None
g_CardHistory = ""
g_Unit_ETH = 0.01
g_Unit_BNB = 0.05
g_TokenMode = ETH
g_CurTokenAmount = g_Unit_ETH
g_SlotCashout = 1.95
g_STATUS = 0
g_ETH_Web3 = None
g_BSC_Web3 = None
g_ETH_Contract = None
g_BSC_Contract = None
# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# g_Chat_ID = -1
# updater = Updater(token=TOKEN, use_context=True)
# dispatcher = updater.dispatcher

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Start the bot and ask what to do when the command /start is issued.

    init()
    # global g_Chat_ID; g_Chat_ID = update.message.chat_id
    user = update.effective_user
    userInfo = update.message.from_user

    # get User Information
    global UserName, UserId, FullName, isBot
    UserName = userInfo['username']
    UserId = userInfo['id']
    FirstName = userInfo['first_name']
    LastName = userInfo['last_name']
    FullName = "{} {}".format(FirstName, LastName)
    isBot = userInfo['is_bot']

    str_Greetings = f"🙋‍♀️Hi @{UserName}\nWelcome to Aleekk Casino!\n"
    str_Intro = f"Please enjoy High-Low & Slot machine games here.\n"
    print('You talk with user {} and his user ID: {} '.format(userInfo['username'], userInfo['id']))
    
    keyboard = [
        [
            InlineKeyboardButton("Deposit", callback_data="Deposit"),
            InlineKeyboardButton("Withdraw", callback_data="Withdraw"),
            InlineKeyboardButton("Balance", callback_data="Balance"),
        ],
        [
            InlineKeyboardButton("Play Hilo", callback_data="Play Hilo"),
            InlineKeyboardButton("Play Slot", callback_data="Play Slot"),
        ],
        [
            InlineKeyboardButton("Help", callback_data="Help"),
        ]
    ]
    await update.message.reply_text(
        str_Greetings + str_Intro + "What would you like to do?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    # await setInterval(funcInterval, 10)

    return CHOOSE

########################################################################
#                              +Wallet                                 #
########################################################################
async def wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    userInfo = update.message.from_user
    print('{} is checking wallet, his user ID: {} '.format(userInfo['username'], userInfo['id']))
    address = await getWallet(UserId, UserName, FullName, isBot, g_ETH_Contract)
    eth_amount = await getBalance(address, g_ETH_Web3, UserId)
    bnb_amount = await getBalance(address, g_BSC_Web3, UserId)
    await update.message.reply_text(
        f"@{UserName}'s wallet\nAddress : {address}\nETH : {eth_amount}\nBNB : {bnb_amount}\n/start"
    )

async def _wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    address = await getWallet(UserId, UserName, FullName, isBot, g_ETH_Contract)
    eth_amount = await getBalance(address, g_ETH_Web3, UserId)
    bnb_amount = await getBalance(address, g_BSC_Web3, UserId)
    query = update.callback_query
    await query.message.edit_text(
        f"@{UserName}'s wallet\nAddress : {address}\nETH : {eth_amount}\nBNB : {bnb_amount}\n/start"
    )

########################################################################
#                            +High - Low                               #
########################################################################
async def playHilo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    userInfo = update.message.from_user
    print('{} starts Hilo, his user ID: {} '.format(userInfo['username'], userInfo['id']))
    init()
    global g_STATUS
    g_STATUS = ST_HILO
    str_Guide = f"{g_HiloMark}Which token do you wanna bet?\n"
    return await eth_bnb_dlg(update, str_Guide)

async def _playHilo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    init()
    global g_STATUS
    g_STATUS = ST_HILO
    str_Guide = f"{g_HiloMark}Which token do you wanna bet?\n"
    return await _eth_bnb_dlg(update, str_Guide)

async def _panelHilo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    global g_PrevCard
    keyboard = []
    newCard = None
    sGreeting = ""
    if g_Cashout > 0 :
        sGreeting = f"You Won!🎉\nPrevious Cards:{g_CardHistory}\n"
        print(g_NextCard)
        newCard = g_NextCard
        g_PrevCard = newCard
        print(newCard)
        print(g_PrevCard)
        keyboard = [
            [
                InlineKeyboardButton("High", callback_data="High"),
                InlineKeyboardButton("Low", callback_data="Low"),
            ],
            [
                InlineKeyboardButton("Cashout", callback_data="CashoutHilo"),
            ]
        ]
        await query.message.edit_text(
            f"{sGreeting}Current Card: {str(newCard['label'])}\n\nCashout : x{g_Cashout}\nCashout:" + str(g_CurTokenAmount * g_Cashout) + getUnitString(g_TokenMode) + "\nWhat is your next guess? High or Low?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return BETTINGHILO
    else :
        sGreeting = "High - Low Game started!\n\n"
        newCard = controlRandCard(True, g_CardHistory, g_PrevCard)
        g_PrevCard = newCard
        keyboard = [
            [
                InlineKeyboardButton("High", callback_data="High"),
                InlineKeyboardButton("Low", callback_data="Low"),
            ]
        ]
        await query.message.edit_text(
            f"{sGreeting}Current Card: {str(newCard['label'])}\nWhat is your next guess? High or Low?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return BETTINGHILO

async def _high(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    global g_Cashout
    global g_NextCard
    global g_CardHistory
    card = None
    while True :
        card = controlRandCard(True, g_CardHistory, g_PrevCard)
        if card['value'] != g_PrevCard['value'] and card['label'] not in g_CardHistory:
            break
    g_CardHistory = g_CardHistory + g_PrevCard['label'] + " "
    print(card)
    if card['value'] > g_PrevCard['value']:
        print("High=>TRUE")
        g_Cashout += 1 
        g_NextCard = card
        return await _panelHilo(update, context)
    else :
        print("High=>FALSE")
        sCardHistory = g_CardHistory
        init()
        g_Cashout = 0
        query = update.callback_query
        keyboard = [
            [
                InlineKeyboardButton("Play Again", callback_data="againHilo"),
                InlineKeyboardButton("Change Bet", callback_data="changeBet"),
                InlineKeyboardButton("Cancel", callback_data="Cancel"),
            ]
        ]
        await query.message.edit_text(
            f"Busted!❌\n\nPrevious Cards:{sCardHistory}\n\nFinal Card:{card['label']}\n\n Do you want to play again?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return AGAINHILO

async def _low(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    global g_Cashout
    global g_NextCard
    global g_CardHistory
    card = None
    while True :
        card = controlRandCard(False, g_CardHistory, g_PrevCard)
        if g_PrevCard != None and card['value'] != g_PrevCard['value'] :
            break
    g_CardHistory = g_CardHistory + g_PrevCard['label'] + " "
    if card['value'] < g_PrevCard['value']:
        print("LOW=>TRUE")
        g_NextCard = card
        g_Cashout += 1 
        return await _panelHilo(update, context)
    else :
        print("LOW=>FALSE")
        g_Cashout = 0
        sCardHistory = g_CardHistory
        init()
        query = update.callback_query
        keyboard = [
            [
                InlineKeyboardButton("Play Again", callback_data="againHilo"),
                InlineKeyboardButton("Change Bet", callback_data="changeBet"),
                InlineKeyboardButton("Cancel", callback_data="Cancel"),
            ]
        ]
        await query.message.edit_text(
            f"Busted!❌\n\nPrevious Cards:{sCardHistory}\n\nFinal Card:{card['label']}\n\n Do you want to play again?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return AGAINHILO

async def _cashoutHilo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.message.edit_text(
        f"🏆🏆🏆\nYou win!\nProfit : x{g_Cashout}\n/start /hilo"
    )
    
########################################################################
#                              +Slot                                   #
########################################################################
async def playSlot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    userInfo = update.message.from_user
    print('{} starts SLOT, his user ID: {} '.format(userInfo['username'], userInfo['id']))
    init()
    global g_STATUS
    g_STATUS = ST_SLOT
    str_Guide = f"{g_SlotMark}Which token do you wanna bet?\n"
    return await eth_bnb_dlg(update, str_Guide)
 
async def _playSlot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    init()
    global g_STATUS
    g_STATUS = ST_SLOT
    str_Guide = f"{g_SlotMark}Which token do you wanna bet?\n"
    return await _eth_bnb_dlg(update, str_Guide)
 
async def _panelSlot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    slot = roll()
    label = slot["label"]
    res = ""
    if slot["value"] == True:
        res = "You Won " + str(g_CurTokenAmount * g_SlotCashout) + getUnitString(g_TokenMode) + "💰"
    else :
        res = "You lost " + str(g_CurTokenAmount) + " " + getUnitString(g_TokenMode) + "💸"
    query: CallbackQuery = update.callback_query
    keyboard = [
        [
            InlineKeyboardButton("Play again", callback_data="againSlot"),
            InlineKeyboardButton("Change bet", callback_data="changeBet"),
            InlineKeyboardButton("Cancel", callback_data="Cancel"),
        ]
    ]

    await query.message.edit_text(
        f"{g_SlotMark}{label}\n\n{res}\n",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return AGAINSLOT

########################################################################
#                              +Deposit                                #
########################################################################
async def deposit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    global g_STATUS
    g_STATUS = ST_DEPOSIT
    str_Guide = f"💰 Please select token to deposit\n"
    return await eth_bnb_dlg(update, str_Guide)

async def _deposit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    global g_STATUS
    g_STATUS = ST_DEPOSIT
    str_Guide = f"💰 Please select token to deposit\n"
    return await _eth_bnb_dlg(update, str_Guide)

########################################################################
#                             +Withdraw                                #
########################################################################
async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    userInfo = update.message.from_user
    print('{} tries to withdraw, his user ID: {} '.format(userInfo['username'], userInfo['id']))
    global g_STATUS
    g_STATUS = ST_WITHDRAW
    str_Guide = f"💰 Please select token to withdraw\n"
    return await eth_bnb_dlg(update, str_Guide)

async def _withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    global g_STATUS
    g_STATUS = ST_WITHDRAW
    str_Guide = f"💰 Please select token to withdraw\n"
    return await _eth_bnb_dlg(update, str_Guide)

async def confirm_dlg_withdraw(update: Update, msg : str) -> int:
    query = update.callback_query
    keyboard = [
        [
            InlineKeyboardButton("Cancel", callback_data="Cancel"),
        ]
    ]
    await query.message.edit_text(
        msg,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    # ForceReply(selective=True) #TODO
    return PANELWITHDRAW
########################################################################
#                            +eth_bnb_dlg                              #
########################################################################
async def eth_bnb_dlg(update: Update, msg : str) -> int:
    keyboard = [
        [
            InlineKeyboardButton("ETH", callback_data="funcETH"),
            InlineKeyboardButton("BNB", callback_data="funcBNB"),
        ],
        [
            InlineKeyboardButton("Cancel", callback_data="Cancel"),
        ]
    ]
    await update.message.reply_text(
        msg,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return SELECT

async def _eth_bnb_dlg(update: Update, msg : str) -> int:
    query = update.callback_query
    keyboard = [
        [
            InlineKeyboardButton("ETH", callback_data="funcETH"),
            InlineKeyboardButton("BNB", callback_data="funcBNB"),
        ],
        [
            InlineKeyboardButton("Cancel", callback_data="Cancel"),
        ]
    ]
    await query.message.edit_text(
        msg,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return SELECT
 
########################################################################
#                          +Func ETH - BNB                             #
########################################################################
async def funcETH(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    global g_TokenMode; g_TokenMode = ETH
    address = await getWallet(UserId, UserName, FullName, isBot, g_ETH_Contract)
    n_Balance = await getBalance(address, g_ETH_Web3, UserId)
    str_Guide = ""
    if g_STATUS == ST_DEPOSIT:
        return await panelDeposit(update, context)
    if g_STATUS == ST_WITHDRAW :
        str_Guide = f"How much do you wanna withdraw?\nCurrent Balance : {n_Balance} ETH\n"
        return await confirm_dlg_withdraw(update, str_Guide)
    else :
        str_Guide = f"How much do you wanna bet?\nCurrent Balance : {n_Balance} ETH\n"
        return await confirm_dlg_game(update, context, str_Guide, g_Unit_ETH)
 
async def funcBNB(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    global g_TokenMode; g_TokenMode = BNB
    address = await getWallet(UserId, UserName, FullName, isBot, g_ETH_Contract)
    n_Balance = await getBalance(address, g_BSC_Web3, UserId)
    str_Guide = ""
    if g_STATUS == ST_DEPOSIT:
        return await panelDeposit(update, context)
    if g_STATUS == ST_WITHDRAW :
        str_Guide = f"How much do you wanna withdraw?\nCurrent Balance : {n_Balance} BNB\n"
        return await confirm_dlg_withdraw(update, str_Guide)
    else :
        str_Guide = f"How much do you wanna bet?\nCurrent Balance : {n_Balance} BNB\n"
        return await confirm_dlg_game(update, context, str_Guide, g_Unit_BNB)

async def confirm_dlg_game(update: Update, context: ContextTypes.DEFAULT_TYPE, msg : str, tokenAmount : float) -> int:
    sAmount = f"\nYou can bet {tokenAmount}" + getUnitString(g_TokenMode) + await getPricefromAmount(tokenAmount, g_TokenMode)
    query = update.callback_query
    
    sPlayButton = ""
    sMark = ""
    match g_STATUS:
        case 2: #ST_HILO
            sPlayButton = "Play"
            sMark = g_HiloMark
        case 3: #ST_SLOT
            sPlayButton = "Roll"
            sMark = g_SlotMark

    keyboard = [
        [
            InlineKeyboardButton("/2", callback_data="changeBetAmount:0"),
            InlineKeyboardButton("Cancel", callback_data="Cancel"),
            InlineKeyboardButton("x2", callback_data="changeBetAmount:1"),
        ],
        [
            InlineKeyboardButton(sPlayButton, callback_data=sPlayButton),
        ]
    ]
    try:
        await query.message.edit_text(
            sMark + msg + sAmount,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        print("Error",e)

    return LASTSELECT

########################################################################
#                         +changeBetAmount                             #
########################################################################
async def _changeBetAmount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query: CallbackQuery = update.callback_query
    # query.answer()
    param = query.data.split(":")[1]

    balance = ""
    if g_TokenMode == ETH :
        UnitToken = g_Unit_ETH
        balance = str(await getBalance(await getWallet(UserId, UserName, FullName, isBot, g_ETH_Contract), g_ETH_Web3, UserId))
    else :
        UnitToken = g_Unit_BNB
        balance = str(await getBalance(await getWallet(UserId, UserName, FullName, isBot, g_BSC_Contract), g_BSC_Web3, UserId))
    global g_CurTokenAmount
    print(param)
    if int(param) == 0 :
        print(g_CurTokenAmount)
        g_CurTokenAmount /= 2
        print(g_CurTokenAmount)
    else :
        g_CurTokenAmount *= 2
    
    if g_CurTokenAmount < UnitToken :
        g_CurTokenAmount = UnitToken

    str_Guide = f"How much do you wanna bet?\nCurrent Balance : " + balance + " " + getUnitString(g_TokenMode) + "\n"
    print("debug 1")
    return await confirm_dlg_game(update, context, str_Guide, g_CurTokenAmount)

async def panelDeposit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    address = await getWallet(UserId, UserName, FullName, isBot, g_ETH_Contract)
    query = update.callback_query
    pattern = f"copyToClipboard:{address}"
    keyboard = [
        [
            InlineKeyboardButton("Copy", callback_data=pattern),
        ],
    ]
    await query.message.edit_text(
        f"You can deposit here!\n{address}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return COPY

async def panelWithdraw(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Submit your withdraw request",
    )

async def help(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text(
        g_Greetings + g_Help + g_Wallet + g_Deposit + g_Withdraw + g_Hilo + g_Slot + g_LeaderBoard
    )
 
async def _help(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    # await query.answer()
    # await query.edit_message_text(text=f"Selected option: {query.data}")
    # await context.bot.send_message(update.effective_user.id, "start")
    # chat_id = g_Chat_ID
    # await context.bot.send_message(chat_id=chat_id, text="/help")
    # await context.bot.send_chat_action(chat_id=chat_id, text="/help")
    await query.message.edit_text(
        g_Greetings + g_Help + g_Wallet + g_Deposit + g_Withdraw + g_Hilo + g_Slot + g_LeaderBoard
    )

async def board(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Shows the order of the users who had won\n1. Thomas $999\n2. Thomas $999\n3. Thomas $999"
    )
 
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    user = query.from_user
    await query.answer()
    await query.message.edit_text("Canceled!\nIf you want to do something else, enter /start")
 
async def end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text(
        "Bye! I hope we can talk again some day.", reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

def init():
    global g_TokenMode; g_TokenMode = ETH
    global g_CurTokenAmount; g_CurTokenAmount = g_Unit_ETH
    global g_CardHistory;   g_CardHistory = ""
    global g_Cashout;       g_Cashout = 0
    global g_NextCard;      g_NextCard = None
    global g_PrevCard;      g_PrevCard = None

############################################################################
#                               Incomplete                                 #
############################################################################
async def funcInterval() -> None:
    if UserId and UserName and FullName:
        address = await getWallet(UserId, UserName, FullName, isBot, g_ETH_Contract)
        ethBalance = await getBalance(address, g_ETH_Web3, UserId)
        bnbBalance = await getBalance(address, g_BSC_Web3, UserId)

        field = "UserID=\"{}\"".format(UserId)
        res = await readFieldsWhereStr('tbl_users', 'ReadyTransfer', field)

        if res[0][0] == 0:
            return

        onChainEthBalance = g_ETH_Web3.eth.getBalance(address)
        onChainBnbBalance = g_BSC_Web3.eth.getBalance(address)
        if onChainEthBalance > 0:
            await deploySmartContract(g_ETH_Web3, g_ETH_Contract, UserId)
            await transferAssetsToContract(address, g_ETH_Web3, UserId)

        # await deploySmartContract(g_ETH_Web3, g_ETH_Contract, UserId)
        # await transferAssetsToContract(address, g_ETH_Web3, UserId)
    
        # await deploySmartContract(g_BSC_Web3, g_BSC_Contract, UserId)
        # await transferAssetsToContract(address, g_BSC_Web3, UserId)

async def copyToClipboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query: CallbackQuery = update.callback_query
    query.answer()
    param = query.data.split(":")[1]
    pyperclip.copy(param)
    print(param)
    a = pyperclip.paste()
    print(a)

############################################################################
#                       complete(1st edition)                              #
############################################################################

# def setInterval(func:any, sec:int) -> any:
#     def func_wrapper():
#         setInterval(asyncio.run(func()), sec)
#         asyncio.run(func())
#     t = threading.Timer(sec, func_wrapper)
#     t.start()
#     return t

def getWeb3() -> None:
    eth_infura_url = "https://goerli.infura.io/v3/" + INFURA_ID
    global g_ETH_Web3
    g_ETH_Web3 = Web3(Web3.HTTPProvider(eth_infura_url))

    bsc_infura_url = "https://data-seed-prebsc-1-s1.binance.org:8545"
    global g_BSC_Web3
    g_BSC_Web3 = Web3(Web3.HTTPProvider(bsc_infura_url))

def getContract() -> None:
    abi = []
    with open("./abi/bank_roll_abi.json") as f:
        abi = json.load(f)

    global g_ETH_Contract
    g_ETH_Contract = g_ETH_Web3.eth.contract(address=ETH_CONTRACT_ADDRESS, abi=abi)

    global g_BSC_Contract
    g_BSC_Contract = g_BSC_Web3.eth.contract(address=BSC_CONTRACT_ADDRESS, abi=abi)

# dispatcher.add_handler(CommandHandler('start', start))
# def call_start_command() :
#     update = telegram.Update(
#         update_id=1,
#         message=telegram.Message(
#             message_id=1,
#             chat=telegram.Chat(id=1, type=telegram.Chat.PRIVATE),
#             text='/start'
#         )
#     )
#     dispatcher.process_update(update)     

async def setInterval(func,time):
    e = threading.Event()
    while not e.wait(time):
        await func()

# async def foo():
#     address = await getWallet(UserId, UserName, FullName, isBot, g_ETH_Contract)
#     await getBalance(address, g_ETH_Web3, UserId)
#     await getBalance(address, g_BSC_Web3, UserId)

def main() -> None:
    """Run the bot."""
    getWeb3()
    getContract()

    # setInterval(funcInterval, 5)
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TOKEN).build()

    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start),
                      CommandHandler("wallet", wallet),
                      CommandHandler("help", help),
                      CommandHandler("hilo", playHilo),
                      CommandHandler("slot", playSlot),
                      CommandHandler("withdraw", withdraw),
                      CommandHandler("board", board),
                      CommandHandler("deposit", deposit)],
        states={
            WALLET: [MessageHandler("wallet", wallet)],
            CHOOSE: [CallbackQueryHandler(_deposit, pattern="Deposit"),
                     CallbackQueryHandler(_withdraw, pattern="Withdraw"),
                     CallbackQueryHandler(_wallet, pattern="Balance"),
                     CallbackQueryHandler(_playHilo, pattern="Play Hilo"),
                     CallbackQueryHandler(_playSlot, pattern="Play Slot"),
                     CallbackQueryHandler(_help, pattern="Help")],
            DEPOSIT: [MessageHandler(filters.TEXT, deposit)],
            COPY: [CallbackQueryHandler(copyToClipboard, pattern="^copyToClipboard:")],
            SELECT: [CallbackQueryHandler(funcETH, pattern="funcETH"),
                     CallbackQueryHandler(funcBNB, pattern="funcBNB"),
                     CallbackQueryHandler(cancel, pattern="Cancel")],
            LASTSELECT : [CallbackQueryHandler(_changeBetAmount, pattern="^changeBetAmount:"),
                          CallbackQueryHandler(cancel, pattern="Cancel"),
                          CallbackQueryHandler(_panelHilo, pattern="Play"),
                          CallbackQueryHandler(_panelSlot, pattern="Roll")],
            # PANELHILO: [MessageHandler(filters.TEXT, _panelHilo)],
            # PANELSLOT: [MessageHandler(filters.TEXT, _panelSlot)],
            AGAINSLOT: [CallbackQueryHandler(cancel, pattern="Cancel"),
                        CallbackQueryHandler(_panelSlot, pattern="againSlot"),
                        CallbackQueryHandler(_playSlot, pattern="changeBet"),],
            AGAINHILO: [CallbackQueryHandler(cancel, pattern="Cancel"),
                        CallbackQueryHandler(_panelHilo, pattern="againHilo"),
                        CallbackQueryHandler(_playHilo, pattern="changeBet")],
            PANELDEPOSIT: [MessageHandler(filters.TEXT, panelDeposit)],
            PANELWITHDRAW: [MessageHandler(filters.TEXT, panelWithdraw)],
            BETTINGHILO: [CallbackQueryHandler(_cashoutHilo, pattern="CashoutHilo"),
                          CallbackQueryHandler(_high, pattern="High"),
                          CallbackQueryHandler(_low, pattern="Low"),]
        },
        fallbacks=[CommandHandler("end", end)],
        allow_reentry=True,
    )

    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling()

if __name__ == "__main__":
    main()