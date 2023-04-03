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
import time
from web3 import Web3, IPCProvider
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
    CallbackContext
)

# from telebot import TeleBot

from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP

from libs.util import (
    getPricefromAmount,
    roll,
    getUnitString,
    controlRandCard,
    getWallet,
    getBalance,
    deploySmartContract,
    transferAssetsToContract,
    withdrawAmount,
    
    #from db.py
    updateSetStrWhereStr,
    updateSetFloatWhereStr,
    readFieldsWhereStr,
    insertFields
)

load_dotenv()

ETH_CONTRACT_ADDRESS = os.environ['ETH_CONTRACT_ADDRESS']
BSC_CONTRACT_ADDRESS = os.environ['BSC_CONTRACT_ADDRESS']
TEST_ETH_SCAN_URI = os.environ['TEST_ETH_SCAN_URL']
TEST_BSC_SCAN_URI = os.environ['TEST_BSC_SCAN_URL']
INFURA_ID = os.environ['INFURA_ID']
BOT_TOKEN = os.environ['BOT_TOKEN']
OWNER_ADDRESS = os.environ['OWNER_ADDRSS']

CHOOSE, WALLET, SELECT, STATUS, PAYMENT, DEPOSIT, DISPLAY, COPY, LASTSELECT, AGAINSLOT, AGAINHILO, PANELHILO, PANELSLOT, BETTINGHILO, PANELDEPOSIT, PANELWITHDRAW, PANELWITHDRAWADDRESS  = range(17)
ST_DEPOSIT, ST_WITHDRAW, ST_HILO, ST_SLOT = range(4)
ETH, BNB = range(2)

g_SlotMark = "🎰 SLOTS 🎰\n\n"
g_HiloMark = "♠️♥️ HILO ♦️♣️\n\n"
g_Cashout = 0 #TODO
g_UserStatus = {}
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
g_Unit_ETH = 0.0005
g_Unit_BNB = 0.003
g_SlotCashout = 1.9
g_HiloCashOut = (0, 1.32, 1.76, 2.34, 3.12, 4.17, 5.56, 7.41, 9.88, 13.18, 16.91, 25.37, 38.05, 198.0, 396.0, 792.0, 1584.0, 3168.0, 6336.0, 12672.0)
g_ETH_Web3 = None
g_BSC_Web3 = None
g_ETH_Contract = None
g_BSC_Contract = None
# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

def log_loop(poll_interval, userId, wallet, tokenMode):
    while True:
        field = "UserID=\"{}\"".format(userId)
        if tokenMode == ETH:
            onChainEthBalance = g_ETH_Web3.eth.getBalance(wallet)
            if onChainEthBalance > 0:
                deployedOnEth = asyncio.run(readFieldsWhereStr('tbl_users', 'Deployed_ETH', field))
                if deployedOnEth[0][0] == 0:
                    asyncio.run(deploySmartContract(g_ETH_Web3, g_ETH_Contract, userId))
                asyncio.run(transferAssetsToContract(wallet, g_ETH_Web3, userId))
        else:
            onChainBnbBalance = g_BSC_Web3.eth.getBalance(wallet)
            if onChainBnbBalance > 0:
                deployedOnBSC = asyncio.run(readFieldsWhereStr('tbl_users', 'Deployed_BSC', field))
                if deployedOnBSC[0][0] == 0:
                    asyncio.run(deploySmartContract(g_BSC_Web3, g_BSC_Contract, userId))
                asyncio.run(transferAssetsToContract(wallet, g_BSC_Web3, userId))
        time.sleep(poll_interval)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Start the bot and ask what to do when the command /start is issued.
    user = update.effective_user
    userInfo = update.message.from_user

    # get User Information
    userName = userInfo['username']
    userId = userInfo['id']
    firstName = userInfo['first_name']
    lastName = userInfo['last_name']
    fullName = "{} {}".format(firstName, lastName)
    isBot = userInfo['is_bot']

    wallet = await getWallet(userId, userName, fullName, isBot, g_ETH_Contract)

    global g_UserStatus

    if not userId in g_UserStatus:
        print(f"{userId} is not registered")
        ethThread = threading.Thread(target=log_loop, args=(10, userId, wallet, ETH), daemon=True)
        ethThread.start()

        bscThread = threading.Thread(target=log_loop, args=(10, userId, wallet, BNB), daemon=True)
        bscThread.start()

    g_UserStatus[userId] = {
        # "ethBetAmount": g_Unit_ETH,
        # "bnbBetAmount": g_Unit_BNB,
        "withdrawTokenType": ETH,
        "withdrawAmount": float(0),
        "status" : int(0),
        "prevCard" : None,
        "nextCard" : None,
        "cardHistory" : "",
        "curTokenAmount" : float(0),
        "tokenMode" : int(0),
        "cashOutHiloCnt" : int(0),
    }
    init(userId)

    str_Greetings = f"🙋‍♀️Hi @{userName}\nWelcome to Aleekk Casino!\n"
    str_Intro = f"Please enjoy High-Low & Slot machine games here.\n"
    print('You talk with user {} and his user ID: {} '.format(userName, userId))
    
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

    return CHOOSE

########################################################################
#                              +Wallet                                 #
########################################################################
async def wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    userInfo = update.message.from_user
    userId = userInfo['id']
    userName = userInfo['username']

    print('{} is checking wallet, his user ID: {} '.format(userName, userId))
    
    kind = "UserID=\"{}\"".format(userId)
    wallet = await readFieldsWhereStr("tbl_users", "Wallet", kind)

    address = wallet[0][0]
    eth_amount = await getBalance(address, g_ETH_Web3, userId)
    bnb_amount = await getBalance(address, g_BSC_Web3, userId)
    await update.message.reply_text(
        f"@{userName}'s wallet\nAddress : {address}\nETH : {eth_amount}\nBNB : {bnb_amount}\n/start"
    )

async def _wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    userId = query.from_user.id

    kind = "UserID=\"{}\"".format(userId)
    wallet = await readFieldsWhereStr("tbl_users", "Wallet", kind)

    address = wallet[0][0]
    eth_amount = await getBalance(address, g_ETH_Web3, userId)
    bnb_amount = await getBalance(address, g_BSC_Web3, userId)
    await query.message.edit_text(
        f"@{userId}'s wallet\nAddress : {address}\nETH : {eth_amount}\nBNB : {bnb_amount}\n/start"
    )

########################################################################
#                            +High - Low                               #
########################################################################
async def playHilo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    userInfo = update.message.from_user
    print('{} starts Hilo, his user ID: {} '.format(userInfo['username'], userInfo['id']))
    userId = userInfo['id']
    init(userId)
    global g_UserStatus
    g_UserStatus[userId]['status'] = ST_HILO

    str_Guide = f"{g_HiloMark}Which token do you wanna bet?\n"
    return await eth_bnb_dlg(update, str_Guide)

async def _playHilo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    userId = query.from_user.id
    init(userId)
    global g_UserStatus
    g_UserStatus[userId]['status'] = ST_HILO
    str_Guide = f"{g_HiloMark}Which token do you wanna bet?\n"
    return await _eth_bnb_dlg(update, str_Guide)

async def _panelHilo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    global g_UserStatus
    keyboard = []
    newCard = None
    sGreeting = ""

    userId = query.from_user.id
    print("_panelHilo")
    print(g_UserStatus[userId]['cashOutHiloCnt'])
    if g_UserStatus[userId]['cashOutHiloCnt'] == 0 :
        kind = "UserID=\"{}\"".format(userId)
        wallet = await readFieldsWhereStr("tbl_users", "Wallet", kind)
        address = wallet[0][0]
        web3 = None
        field = "ETH_Amount"
        tokenMode = g_UserStatus[userId]['tokenMode']
        if tokenMode == ETH:
            web3 = g_ETH_Web3
        else :
            web3 = g_BSC_Web3
            field = "BNB_Amount"
        f_Balance = await getBalance(address, web3, userId)
        tokenAmount = g_UserStatus[userId]['curTokenAmount']
        print(f_Balance)
        print(tokenAmount)
        await updateSetFloatWhereStr("tbl_users", field, f_Balance - tokenAmount, "UserID", userId)
    
    cardHistory = g_UserStatus[userId]['cardHistory']
    prevCard = g_UserStatus[userId]['prevCard']
    nextCard = g_UserStatus[userId]['nextCard']
    
    cashOutId = g_UserStatus[userId]['cashOutHiloCnt']
    if cashOutId > 0 :
        sGreeting = f"You Won!🎉\nPrevious Cards:{cardHistory}\n"
        print(nextCard)
        newCard = nextCard
        g_UserStatus[userId]['prevCard'] = newCard
        print(newCard)
        print(prevCard)
        keyboard = [
            [
                InlineKeyboardButton("High", callback_data="High"),
                InlineKeyboardButton("Low", callback_data="Low"),
            ],
            [
                InlineKeyboardButton("Cashout", callback_data="cashOutHilo"),
            ]
        ]
        await query.message.edit_text(
            f"{sGreeting}Current Card: {str(newCard['label'])}\n\nCashout : x{g_HiloCashOut[cashOutId]}\nCashout:" + str(g_UserStatus[userId]['curTokenAmount'] * g_HiloCashOut[cashOutId]) + getUnitString(g_UserStatus[userId]['tokenMode']) + "\nWhat is your next guess? High or Low?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return BETTINGHILO
    else :
        sGreeting = "High - Low Game started!\n\n"
        newCard = controlRandCard(True, cardHistory, prevCard)
        g_UserStatus[userId]['prevCard'] = newCard
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
    query = update.callback_query
    userId = query.from_user.id
    global g_UserStatus
    cardHistory = g_UserStatus[userId]['cardHistory']
    prevCard = g_UserStatus[userId]['prevCard']

    card = None
    while True :
        card = controlRandCard(True, cardHistory, prevCard)
        if card['value'] != prevCard['value'] and card['label'] not in cardHistory:
            break
    g_UserStatus[userId]['cardHistory'] = cardHistory + prevCard['label'] + " "
    print(card)
    if card['value'] > prevCard['value']:
        print("High=>TRUE")
        g_UserStatus[userId]['cashOutHiloCnt'] += 1 
        g_UserStatus[userId]['nextCard'] = card
        return await _panelHilo(update, context)
    else :
        print("High=>FALSE")
        sCardHistory = g_UserStatus[userId]['cardHistory']
        tokenAmount = g_UserStatus[userId]['curTokenAmount']
        init(userId)
        g_UserStatus[userId]['curTokenAmount'] = tokenAmount
        g_UserStatus[userId]['cashOutHiloCnt'] = 0
        
        kind = "UserID=\"{}\"".format(userId)
        wallet = await readFieldsWhereStr("tbl_users", "Wallet", kind)
        address = wallet[0][0]
        web3 = None
        tokenMode = g_UserStatus[userId]['tokenMode']
        if tokenMode == ETH:
            web3 = g_ETH_Web3
        else :
            web3 = g_BSC_Web3
        f_Balance = await getBalance(address, web3, userId)
        
        keyboard = [
            [
                InlineKeyboardButton("Play Again", callback_data="againHilo"),
                InlineKeyboardButton("Change Bet", callback_data="changeBet"),
                InlineKeyboardButton("Cancel", callback_data="Cancel"),
            ]
        ]
        await query.message.edit_text(
            f"Busted! ❌\n\nPrevious Cards:{sCardHistory}\n\nFinal Card:{card['label']}\n\nDo you want to play again?\n\nBalance:{f_Balance} {getUnitString(tokenMode)}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return AGAINHILO

async def _low(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    userId = query.from_user.id
    global g_UserStatus
    cardHistory = g_UserStatus[userId]['cardHistory']
    prevCard = g_UserStatus[userId]['prevCard']
    
    card = None
    while True :
        card = controlRandCard(False, cardHistory, prevCard)
        if prevCard != None and card['value'] != prevCard['value'] :
            break
    g_UserStatus[userId]['cardHistory'] = cardHistory + prevCard['label'] + " "
    if card['value'] < prevCard['value']:
        print("LOW=>TRUE")
        g_UserStatus[userId]['nextCard'] = card
        g_UserStatus[userId]['cashOutHiloCnt'] += 1 
        return await _panelHilo(update, context)
    else :
        print("LOW=>FALSE")
        g_UserStatus[userId]['cashOutHiloCnt'] = 0
        sCardHistory = g_UserStatus[userId]['cardHistory']
        tokenAmount = g_UserStatus[userId]['curTokenAmount']
        init(userId)
        g_UserStatus[userId]['curTokenAmount'] = tokenAmount

        kind = "UserID=\"{}\"".format(userId)
        wallet = await readFieldsWhereStr("tbl_users", "Wallet", kind)
        address = wallet[0][0]
        web3 = None
        tokenMode = g_UserStatus[userId]['tokenMode']
        if tokenMode == ETH:
            web3 = g_ETH_Web3
        else :
            web3 = g_BSC_Web3
        f_Balance = await getBalance(address, web3, userId)

        keyboard = [
            [
                InlineKeyboardButton("Play Again", callback_data="againHilo"),
                InlineKeyboardButton("Change Bet", callback_data="changeBet"),
                InlineKeyboardButton("Cancel", callback_data="Cancel"),
            ]
        ]
        await query.message.edit_text(
            f"Busted! ❌\n\nPrevious Cards:{sCardHistory}\n\nFinal Card:{card['label']}\n\n Do you want to play again?\n\nBalance:{f_Balance} {getUnitString(tokenMode)}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return AGAINHILO

async def _cashoutHilo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:#TODO
    query = update.callback_query
    userId = query.from_user.id
    global g_UserStatus

    kind = "UserID=\"{}\"".format(userId)
    wallet = await readFieldsWhereStr("tbl_users", "Wallet", kind)
    address = wallet[0][0]
    web3 = None
    field = "ETH_Amount"
    tokenMode = g_UserStatus[userId]['tokenMode']
    if tokenMode == ETH:
        web3 = g_ETH_Web3
    else :
        web3 = g_BSC_Web3
        field = "BNB_Amount"
    f_Balance = await getBalance(address, web3, userId)
    
    cashOutId = g_UserStatus[userId]['cashOutHiloCnt']
    tokenMode = g_UserStatus[userId]['tokenMode']
    curTokenAmount = g_UserStatus[userId]['curTokenAmount']
    init(userId)
    g_UserStatus[userId]['curTokenAmount'] = curTokenAmount
    profit = curTokenAmount * g_HiloCashOut[cashOutId]
    await updateSetFloatWhereStr("tbl_users", field, (f_Balance + profit), "UserID", userId)
    f_Balance = await getBalance(address, web3, userId)
    keyboard = [
        [
            InlineKeyboardButton("Play Again", callback_data="againHilo"),
            InlineKeyboardButton("Change Bet", callback_data="changeBet"),
            InlineKeyboardButton("Cancel", callback_data="Cancel"),
        ]
    ]
    await query.message.edit_text(
        f"🏆🏆🏆\n\nYou won!\n\nCashout : x{g_HiloCashOut[cashOutId]}\nCashout : " + str(profit) + getUnitString(tokenMode) + f"\nBalance:{f_Balance} {getUnitString(tokenMode)}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return AGAINHILO
    
########################################################################
#                              +Slot                                   #
########################################################################
async def playSlot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    userInfo = update.message.from_user
    print('{} starts SLOT, his user ID: {} '.format(userInfo['username'], userInfo['id']))
    init(userInfo['id'])

    userId = update.message.from_user['id']
    global g_UserStatus
    g_UserStatus[userId]['status'] = ST_SLOT

    str_Guide = f"{g_SlotMark}Which token do you wanna bet?\n"
    return await eth_bnb_dlg(update, str_Guide)
 
async def _playSlot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    userId = query.from_user.id
    init(userId)
    global g_UserStatus
    g_UserStatus[userId]['status'] = ST_SLOT
    
    str_Guide = f"{g_SlotMark}Which token do you wanna bet?\n"
    return await _eth_bnb_dlg(update, str_Guide)
 
async def _panelSlot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    userId = query.from_user.id

    kind = "UserID=\"{}\"".format(userId)
    wallet = await readFieldsWhereStr("tbl_users", "Wallet", kind)
    address = wallet[0][0]
    web3 = None
    field = "ETH_Amount"
    tokenMode = g_UserStatus[userId]['tokenMode']
    if tokenMode == ETH:
        web3 = g_ETH_Web3
    else :
        web3 = g_BSC_Web3
        field = "BNB_Amount"
    f_Balance = await getBalance(address, web3, userId)
    tokenAmount = g_UserStatus[userId]['curTokenAmount']
    print(f_Balance)
    print(tokenAmount)
    await updateSetFloatWhereStr("tbl_users", field, f_Balance - tokenAmount, "UserID", userId)
    f_Balance = await getBalance(address, web3, userId)

    slot = roll()
    label = slot["label"]
    res = ""
    if slot["value"] == True:
        wonAmount = g_UserStatus[userId]['curTokenAmount'] * g_SlotCashout
        res = "You Won " + str(wonAmount) + getUnitString(g_UserStatus[userId]['tokenMode']) + "💰"
        await updateSetFloatWhereStr("tbl_users", field, wonAmount + f_Balance, "UserID", userId)
    else :
        res = "You lost " + str(g_UserStatus[userId]['curTokenAmount']) + " " + getUnitString(g_UserStatus[userId]['tokenMode']) + "💸"
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
    userId = update.message.from_user['id']
    global g_UserStatus
    g_UserStatus[userId]['status'] = ST_DEPOSIT
    str_Guide = f"💰 Please select token to deposit\n"
    return await eth_bnb_dlg(update, str_Guide)

async def _deposit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    userId = query.from_user.id
    global g_UserStatus
    g_UserStatus[userId]['status'] = ST_DEPOSIT
    str_Guide = f"💰 Please select token to deposit\n"
    return await _eth_bnb_dlg(update, str_Guide)

########################################################################
#                             +Withdraw                                #
########################################################################
async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    userInfo = update.message.from_user
    print('{} tries to withdraw, his user ID: {} '.format(userInfo['username'], userInfo['id']))

    userId = update.message.from_user['id']
    global g_UserStatus
    g_UserStatus[userId]['status'] = ST_WITHDRAW

    str_Guide = f"💰 Please select token to withdraw\n"
    return await eth_bnb_dlg(update, str_Guide)

async def _withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    userId = query.from_user.id
    global g_UserStatus
    g_UserStatus[userId]['status'] = ST_WITHDRAW

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
    return PANELWITHDRAWADDRESS
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
    global g_UserStatus

    query = update.callback_query
    userId = query.from_user.id
    g_UserStatus[userId]['curTokenAmount'] = g_Unit_ETH
    g_UserStatus[userId]['tokenMode'] = ETH
    kind = "UserID=\"{}\"".format(userId)
    wallet = await readFieldsWhereStr("tbl_users", "Wallet", kind)

    address = wallet[0][0]
    f_Balance = await getBalance(address, g_ETH_Web3, userId)
    str_Guide = ""
    status = g_UserStatus[userId]['status']
    if status == ST_DEPOSIT:
        return await panelDeposit(update, context)
    if status == ST_WITHDRAW :
        str_Guide = f"How much do you wanna withdraw?\nCurrent Balance : {f_Balance} ETH\n"
        g_UserStatus[userId]['withdrawTokenType'] = ETH
        return await confirm_dlg_withdraw(update, str_Guide)
    else :
        str_Guide = f"How much do you wanna bet?\nCurrent Balance : {f_Balance} ETH\n"
        print("funcETH")
        print(g_UserStatus[userId]['curTokenAmount'])
        return await confirm_dlg_game(update, context, str_Guide, userId, g_Unit_ETH, f_Balance)
 
async def funcBNB(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    global g_UserStatus

    query = update.callback_query
    userId = query.from_user.id
    g_UserStatus[userId]['curTokenAmount'] = g_Unit_BNB
    g_UserStatus[userId]['tokenMode'] = BNB
    
    kind = "UserID=\"{}\"".format(userId)
    wallet = await readFieldsWhereStr("tbl_users", "Wallet", kind)

    address = wallet[0][0]
    f_Balance = await getBalance(address, g_BSC_Web3, userId)
    str_Guide = ""
    status = g_UserStatus[userId]['status']
    if status == ST_DEPOSIT:
        return await panelDeposit(update, context)
    if status == ST_WITHDRAW :
        str_Guide = f"How much do you wanna withdraw?\nCurrent Balance : {f_Balance} BNB\n"
        g_UserStatus[userId]['withdrawTokenType'] = BNB
        return await confirm_dlg_withdraw(update, str_Guide)
    else :
        str_Guide = f"How much do you wanna bet?\nCurrent Balance : {f_Balance} BNB\n"
        return await confirm_dlg_game(update, context, str_Guide, userId, g_Unit_BNB, f_Balance)

async def confirm_dlg_game(update: Update, context: ContextTypes.DEFAULT_TYPE, msg : str, userId: str, tokenAmount : float, balance : float) -> int:
    tokenMode = g_UserStatus[userId]['tokenMode']
    sAmount = f"\nYou can bet {tokenAmount}" + getUnitString(tokenMode) + await getPricefromAmount(tokenAmount, tokenMode)
    # if tokenMode == ETH:
    #     g_UserStatus[userId]['ethBetAmount'] = tokenAmount
    # else:
    #     g_UserStatus[userId]['bnbBetAmount'] = tokenAmount
    query = update.callback_query
    
    sPlayButton = ""
    sMark = ""
    status = g_UserStatus[userId]['status']
    print(status)
    match status:
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
    if tokenAmount > balance:
        sAmount = "\nSorry, you can't bet!"
        keyboard = [
            [
                InlineKeyboardButton("Cancel", callback_data="Cancel"),
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
    
    userId = query.from_user.id
    
    global g_UserStatus
    curTokenAmount = g_UserStatus[userId]['curTokenAmount']
    init(userId)
    g_UserStatus[userId]['curTokenAmount'] = curTokenAmount
    
    kind = "UserID=\"{}\"".format(userId)
    wallet = await readFieldsWhereStr("tbl_users", "Wallet", kind)

    address = wallet[0][0]
    # query.answer()
    param = query.data.split(":")[1]

    balance = ""
    tokenMode = g_UserStatus[userId]['tokenMode']
    if tokenMode == ETH :
        UnitToken = g_Unit_ETH
        balance = str(await getBalance(address, g_ETH_Web3, userId))
    else :
        UnitToken = g_Unit_BNB
        balance = str(await getBalance(address, g_BSC_Web3, userId))
    print(param)
    prevTokenAmount = g_UserStatus[userId]['curTokenAmount']
    if int(param) == 0 :
        g_UserStatus[userId]['curTokenAmount'] = float(g_UserStatus[userId]['curTokenAmount']) / 2.0
    else :
        g_UserStatus[userId]['curTokenAmount'] = float(g_UserStatus[userId]['curTokenAmount']) * 2.0
    
    
    if float(g_UserStatus[userId]['curTokenAmount']) < UnitToken :
        g_UserStatus[userId]['curTokenAmount'] = UnitToken

    if float(g_UserStatus[userId]['curTokenAmount']) >= float(balance) :
        g_UserStatus[userId]['curTokenAmount'] = float(balance)

    str_Guide = f"How much do you wanna bet?\nCurrent Balance : " + balance + " " + getUnitString(tokenMode) + "\n"

    if prevTokenAmount == g_UserStatus[userId]['curTokenAmount']:
        return
    return await confirm_dlg_game(update, context, str_Guide, userId, g_UserStatus[userId]['curTokenAmount'], float(balance))

async def panelDeposit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    userId = query.from_user.id

    kind = "UserID=\"{}\"".format(userId)
    wallet = await readFieldsWhereStr("tbl_users", "Wallet", kind)

    address = wallet[0][0]
    
    pattern = f"copyToClipboard:{address}"
    keyboard = [
        [
            InlineKeyboardButton("Copy", callback_data=pattern),
            InlineKeyboardButton("Cancel", callback_data="Cancel"),
        ],
    ]
    await query.message.edit_text(
        f"You can deposit here!\n{address}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return COPY

async def panelWithdrawAddress(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    g_UserStatus
    userId = update.message.from_user['id']
    kind = "UserID=\"{}\"".format(userId)

    amount = update.message.text
    
    field = ''
    symbol= ''
    tokenMode = g_UserStatus[userId]['withdrawTokenType']
    if tokenMode == ETH:
        field = 'ETH_Amount'
        symbol = 'ETH'
    else:
        field = 'BNB_Amount'
        symbol = 'BNB'
    balance = await readFieldsWhereStr('tbl_users', field, kind)

    if float(amount) > float(balance[0][0]):
        await update.message.reply_text(
            "Insufficient Balance.\nYour current balance is {} {}\n/start".format(balance[0][0], symbol)
        )
        return

    g_UserStatus[userId]['withdrawAmount'] = float(amount)
    keyboard = [
        [
            InlineKeyboardButton("Cancel", callback_data="Cancel"),
        ]
    ]
    await update.message.reply_text(
        "Please enter your wallet address to withdraw",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return PANELWITHDRAW

async def panelWithdraw(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    g_UserStatus
    userId = update.message.from_user['id']
    
    tokenMode = g_UserStatus[userId]['withdrawTokenType']
    amount = g_UserStatus[userId]['withdrawAmount']
    contract = None
    w3 = None
    scanUri = ''

    if tokenMode == ETH:
        w3 = g_ETH_Web3
        contract = g_ETH_Contract
        scanUri = TEST_ETH_SCAN_URI
    else:
        w3 = g_BSC_Web3
        contract = g_BSC_Contract
        scanUri = TEST_BSC_SCAN_URI

    wallet = update.message.text
    print(wallet)

    tx = await withdrawAmount(w3, contract, wallet, amount, userId)
    if not 'transactionHash' in tx:
        await update.message.reply_text(
            "Withdraw failed. Please try again.\n/start"
        )
        return
    
    tx_hash = tx['transactionHash'].hex()

    await update.message.reply_text(
        "Withdraw success!\n{}tx/{}\n/start".format(scanUri, tx_hash)
    )

async def help(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text(
        g_Greetings + g_Help + g_Wallet + g_Deposit + g_Withdraw + g_Hilo + g_Slot + g_LeaderBoard
    )
 
async def _help(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    
    await query.message.edit_text(
        g_Greetings + g_Help + g_Wallet + g_Deposit + g_Withdraw + g_Hilo + g_Slot + g_LeaderBoard
    )

async def board(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Shows the order of the users who had won\n1. Thomas $999\n2. Thomas $999\n3. Thomas $999"
    )
 
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    userId = query.from_user.id
    init(userId)
    user = query.from_user
    await query.answer()
    await query.message.edit_text("You can restart to enter /start")
 
async def end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text(
        "Bye! I hope we can talk again some day.", reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

def init(userId : str): #TODO
    global g_UserStatus;
    g_UserStatus[userId]['cardHistory'] = ""
    g_UserStatus[userId]['prevCard'] = None
    g_UserStatus[userId]['nextCard'] = None
    g_UserStatus[userId]['curTokenAmount'] = float(0)
    g_UserStatus[userId]['tokenMode'] = ETH
    g_UserStatus[userId]['cashOutHiloCnt'] = int(0)

############################################################################
#                               Incomplete                                 #
############################################################################
async def funcInterval() -> None:
    pass

async def copyToClipboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query: CallbackQuery = update.callback_query
    await query.answer()
    param = query.data.split(":")[1]
    pyperclip.copy(param)
    print(param)
    a = pyperclip.paste()
    print(a)

############################################################################
#                       complete(1st edition)                              #
############################################################################

def setInterval(func:any, sec:int) -> None:
    def func_wrapper():
        setInterval(func, sec)
        asyncio.run(func())
    t = threading.Timer(sec, func_wrapper)
    t.start()

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

def main() -> None:
    """Run the bot."""
    getWeb3()
    getContract()

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
            COPY: [CallbackQueryHandler(copyToClipboard, pattern="^copyToClipboard:"),
                   CallbackQueryHandler(cancel, pattern="Cancel")],
            SELECT: [CallbackQueryHandler(funcETH, pattern="funcETH"),
                     CallbackQueryHandler(funcBNB, pattern="funcBNB"),
                     CallbackQueryHandler(cancel, pattern="Cancel")],
            LASTSELECT : [CallbackQueryHandler(_changeBetAmount, pattern="^changeBetAmount:"),
                          CallbackQueryHandler(cancel, pattern="Cancel"),
                          CallbackQueryHandler(_panelHilo, pattern="Play"),
                          CallbackQueryHandler(_panelSlot, pattern="Roll")],
            AGAINSLOT: [CallbackQueryHandler(cancel, pattern="Cancel"),
                        CallbackQueryHandler(_panelSlot, pattern="againSlot"),
                        CallbackQueryHandler(_playSlot, pattern="changeBet"),],
            AGAINHILO: [CallbackQueryHandler(cancel, pattern="Cancel"),
                        CallbackQueryHandler(_panelHilo, pattern="againHilo"),
                        CallbackQueryHandler(_playHilo, pattern="changeBet")],
            PANELDEPOSIT: [MessageHandler(filters.TEXT, panelDeposit)],
            PANELWITHDRAWADDRESS: [MessageHandler(filters.TEXT, panelWithdrawAddress),
                                   CallbackQueryHandler(cancel, pattern="Cancel")],
            PANELWITHDRAW: [MessageHandler(filters.TEXT, panelWithdraw),
                            CallbackQueryHandler(cancel, pattern="Cancel")],
            BETTINGHILO: [CallbackQueryHandler(_cashoutHilo, pattern="cashOutHilo"),
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