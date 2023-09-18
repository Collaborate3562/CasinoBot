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

import pytz
# import telegram
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
    CallbackQuery,
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
    _getRandCoin,
    getWallet,
    getBalance,
    deploySmartContract,
    transferAssetsToContract,
    createAds,
    withdrawAmount,
    isFloat,
    isValidContractOrWallet,
    calculateTotalWithdrawFee,
    calculateCryptoAmountByUSD,
    calculateFixedFee,
    truncDecimal,
    truncDecimal7,
    isValidUrl,
    isOpenedUrl,

    g_SlotCashOut,

    # from db.py
    getTopFieldsByLimit,
    updateSetStrWhereStr,
    updateSetFloatWhereStr,
    readFieldsWhereStr,
    insertInitialCoinInfos,
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

MAIN, WALLET, SELECT, STATUS, PAYMENT, DEPOSIT, DISPLAY, COPY, LASTSELECT, AGAINSLOT, AGAINHILO, AGAINCOINFLIP, PANELHILO, PANELSLOT, BETTINGHILO, BETTINGCOINFLIP, PANELDEPOSIT, PANELWITHDRAW, PANELWITHDRAWADDRESS, PANELADVERTISE, CANCEL, ADSTIME, ADSURL, ADSDESC, ADSCONFIRM, ADSPAY, ADSPAYCONFIRM = range(
    27)
ST_DEPOSIT, ST_WITHDRAW, ST_HILO, ST_COINFLIP, ST_SLOT, ST_ADS_PAY = range(6)
ETH, BNB = range(2)

HOUSE_CUT_FEE = 50
PERCENTAGE = 1000

ETH_FIXED_WITHDRAW_FEE = float(1)
BSC_FIXED_WITHDRAW_FEE = float(0.3)

g_SlotMark = "🎰 SLOTS 🎰\n\n"
g_HiloMark = "♠️♥️ HILO ♦️♣️\n\n"
g_CoinFlipMark = "🟡 COIN FLIP ⚪\n\n"
g_UserStatus = {}
# Test Token
TOKEN = BOT_TOKEN
g_Greetings = f"/start - Enter the casino\n"
g_Help = f"/help - Describe all guide\n"
g_Wallet = f"/wallet - Show all balances in your wallet\n"
g_Deposit = f"/deposit - Deposit ETH or BNB into your wallet\n"
g_Withdraw = f"/withdraw - Withdraw ETH or BNB from your wallet\n"
g_Hilo = f"/hilo - Play hilo casino game\n  "
g_SlotHelp1 = f"   Three 7 symbols\n     7️⃣ | 7️⃣ |7️⃣ => x{g_SlotCashOut[0]}\n"
g_SlotHelp2 = f"   Any three of a kind\n    🍎 | 🍎 | 🍎 => x{g_SlotCashOut[1]}\n"
g_SlotHelp3 = f"   Any pair of 7 symbol\n    7️⃣ | 🌺 | 7️⃣ => x{g_SlotCashOut[2]}\n"
g_SlotHelp4 = f"   Any 7 symbols\n  🍌 | 🍎 | 7️⃣ => x{g_SlotCashOut[3]}\n"
g_Slot = f"/slot - Play slot casino game\n" + \
    g_SlotHelp1 + g_SlotHelp2 + g_SlotHelp3 + g_SlotHelp4
g_LeaderBoard = f"/board - Show the leaderboard\n"
g_AdsBoard = f"/advertise - Show the ads at the time\n"
g_Unit_ETH = 0.0005
g_Unit_BNB = 0.003
g_SlotCashout = 1.9
g_HiloCashOut = (0, 1.32, 1.76, 2.34, 3.12, 4.17, 5.56, 7.41, 9.88, 13.18,
                 16.91, 25.37, 38.05, 198.0, 396.0, 792.0, 1584.0, 3168.0, 6336.0, 12672.0)
g_ETH_Web3 = None
g_BSC_Web3 = None
g_ETH_Contract = None
g_BSC_Contract = None
g_timeFormat = ['AM', 'PM']
g_time = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12']
g_duration = ['2', '4', '8', '12', '24']
g_price = [5, 10, 15, 20, 35]
g_adsETHPrice = [0.075, 0.13, 0.2, 0.3, 0.5]
g_adsBNBPrice = [0.45, 0.78, 1.2, 1.8, 3]
g_AdsBtns = ['6PM UTC', '7PM UTC', '8PM UTC', '9PM UTC']
g_AdsPayButton = ['2 Hours - 0.075 ETH / 0.45 BNB', '4 Hours - 0.13 ETH / 0.78 BNB',
                  '8 Hours - 0.2 ETH / 1.2 BNB', '12 Hours - 0.3 ETH / 1.8 BNB', '24 Hours - 0.5 ETH / 3 BNB']
g_AdsDesc = ""
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
                deployedOnEth = asyncio.run(readFieldsWhereStr(
                    'tbl_users', 'Deployed_ETH', field))
                if deployedOnEth[0][0] == 0:
                    asyncio.run(deploySmartContract(
                        g_ETH_Web3, g_ETH_Contract, userId))
                asyncio.run(transferAssetsToContract(
                    wallet, g_ETH_Web3, userId))
        else:
            onChainBnbBalance = g_BSC_Web3.eth.getBalance(wallet)
            if onChainBnbBalance > 0:
                deployedOnBSC = asyncio.run(readFieldsWhereStr(
                    'tbl_users', 'Deployed_BSC', field))
                if deployedOnBSC[0][0] == 0:
                    asyncio.run(deploySmartContract(
                        g_BSC_Web3, g_BSC_Contract, userId))
                asyncio.run(transferAssetsToContract(
                    wallet, g_BSC_Web3, userId))
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
        ethThread = threading.Thread(target=log_loop, args=(
            10, userId, wallet, ETH), daemon=True)
        ethThread.start()

        bscThread = threading.Thread(target=log_loop, args=(
            10, userId, wallet, BNB), daemon=True)
        bscThread.start()

    g_UserStatus[userId] = {
        "update": update,
        "context": context,
        "withdrawTokenType": ETH,
        "advertise": {
            "time": int(0),
            "duration": int(0),
            "url": "",
            "content": "",
            "adsPayTokenType": ETH,
            "adsPayTokenAmount": float(0)
        },
        "withdrawAmount": float(0),
        "status": int(0),
        "prevCard": None,
        "nextCard": None,
        "cardHistory": "",
        "curTokenAmount": float(0),
        "tokenMode": int(0),
        "cashOutHiloCnt": int(0),
        "finalCoin": None,
        "coinHistory": "",
        "cashOutCoinFlipCnt": int(0)
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
            InlineKeyboardButton("Play CoinFlip", callback_data="Play CoinFlip"),
            InlineKeyboardButton("Play Slot", callback_data="Play Slot"),
        ],
        [
            InlineKeyboardButton("LeaderBoard", callback_data="Board"),
            InlineKeyboardButton("ADS", callback_data="advertise"),
        ],
        [
            InlineKeyboardButton("Help", callback_data="Help"),
        ]
    ]
    await update.message.reply_text(
        str_Greetings + str_Intro + "What would you like to do?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return MAIN

########################################################################
#                              +Wallet                                 #
########################################################################


async def wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    userInfo = update.message.from_user
    userId = userInfo['id']
    userName = userInfo['username']

    kind = "UserID=\"{}\"".format(userId)
    wallet = await readFieldsWhereStr("tbl_users", "Wallet", kind)

    address = wallet[0][0]
    eth_amount = await getBalance(address, g_ETH_Web3, userId)
    bnb_amount = await getBalance(address, g_BSC_Web3, userId)

    keyboard = [
        [
            InlineKeyboardButton("Back", callback_data="Cancel"),
        ]
    ]
    await update.message.reply_text(
        f"@{userName}'s wallet\nAddress: {address}\nETH : {eth_amount}\nBNB : {bnb_amount}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return CANCEL


async def _wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    userId = query.from_user.id

    kind = "UserID=\"{}\"".format(userId)
    wallet = await readFieldsWhereStr("tbl_users", "Wallet", kind)

    address = wallet[0][0]

    userName = await readFieldsWhereStr("tbl_users", "UserName", kind)
    userName = userName[0][0]

    eth_amount = await getBalance(address, g_ETH_Web3, userId)
    bnb_amount = await getBalance(address, g_BSC_Web3, userId)

    keyboard = [
        [
            InlineKeyboardButton("Back", callback_data="Cancel"),
        ]
    ]
    await query.message.edit_text(
        f"@{userName}'s wallet\nAddress : {address}\nETH : {eth_amount}\nBNB : {bnb_amount}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return CANCEL
########################################################################
#                            +High - Low                               #
########################################################################


async def playHilo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    userInfo = update.message.from_user
    print('{} starts Hilo, his user ID: {} '.format(
        userInfo['username'], userInfo['id']))
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

async def _playCoinFlip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    userId = query.from_user.id
    init(userId)
    global g_UserStatus
    g_UserStatus[userId]['status'] = ST_COINFLIP
    str_Guide = f"{g_CoinFlipMark}Which token do you wanna bet?\n"
    return await _eth_bnb_dlg(update, str_Guide)

async def _panelHiloOrCoinFlip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    global g_UserStatus
    keyboard = []
    newCard = None
    sGreeting = ""

    userId = query.from_user.id
    
    status = g_UserStatus[userId]['status']
    
    if status == ST_HILO: # ST_HILO
        if g_UserStatus[userId]['cashOutHiloCnt'] == 0:
            kind = "UserID=\"{}\"".format(userId)
            wallet = await readFieldsWhereStr("tbl_users", "Wallet", kind)
            address = wallet[0][0]
            web3 = None
            field = "ETH_Amount"
            wagerField = "ETH_Wagered"
            tokenMode = g_UserStatus[userId]['tokenMode']

            if tokenMode == ETH:
                web3 = g_ETH_Web3
            else:
                web3 = g_BSC_Web3
                field = "BNB_Amount"
                wagerField = "BNB_Wagered"

            f_Balance = await getBalance(address, web3, userId)
            if float(f_Balance) <= 0:
                keyboard = [
                    [
                        InlineKeyboardButton("Deposit", callback_data="Deposit"),
                        InlineKeyboardButton("Back", callback_data="Cancel"),
                    ]
                ]
                await query.message.edit_text(
                    "Insufficient funds!\nPlease deposit more funds",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )

                return CANCEL & MAIN

            tokenAmount = g_UserStatus[userId]['curTokenAmount']
            if float(f_Balance) <= tokenAmount:
                tokenAmount = float(f_Balance)
                g_UserStatus[userId]['curTokenAmount'] = float(f_Balance)

            await updateSetFloatWhereStr("tbl_users", field, f_Balance - tokenAmount, "UserID", userId)

            previousWagered = await readFieldsWhereStr("tbl_users", wagerField, kind)
            oldWagerAmount = float(previousWagered[0][0])
            await updateSetFloatWhereStr("tbl_users", wagerField, oldWagerAmount + tokenAmount, "UserID", userId)

        cardHistory = g_UserStatus[userId]['cardHistory']
        prevCard = g_UserStatus[userId]['prevCard']
        nextCard = g_UserStatus[userId]['nextCard']

        cashOutId = g_UserStatus[userId]['cashOutHiloCnt']
        if cashOutId > 0:
            sGreeting = f"You Won!🎉\nPrevious Cards:{cardHistory}\n"
            newCard = nextCard
            g_UserStatus[userId]['prevCard'] = newCard
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
                f"{sGreeting}Current Card: {str(newCard['label'])}\n\nCashout : x{g_HiloCashOut[cashOutId]}\nCashout:" + "{:.4f}".format(
                    g_UserStatus[userId]['curTokenAmount'] * g_HiloCashOut[cashOutId]) + getUnitString(g_UserStatus[userId]['tokenMode']) + "\nWhat is your next guess? High or Low?",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return BETTINGHILO
        else:
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
    elif status == ST_COINFLIP: # ST_COINFLIP
        kind = "UserID=\"{}\"".format(userId)
        wallet = await readFieldsWhereStr("tbl_users", "Wallet", kind)
        address = wallet[0][0]
        web3 = None
        field = "ETH_Amount"
        wagerField = "ETH_Wagered"
        tokenMode = g_UserStatus[userId]['tokenMode']

        if tokenMode == ETH:
            web3 = g_ETH_Web3
        else:
            web3 = g_BSC_Web3
            field = "BNB_Amount"
            wagerField = "BNB_Wagered"

        f_Balance = await getBalance(address, web3, userId)
        if float(f_Balance) <= 0:
            keyboard = [
                [
                    InlineKeyboardButton("Deposit", callback_data="Deposit"),
                    InlineKeyboardButton("Back", callback_data="Cancel"),
                ]
            ]
            await query.message.edit_text(
                "Insufficient funds!\nPlease deposit more funds",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

            return CANCEL & MAIN

        tokenAmount = g_UserStatus[userId]['curTokenAmount']
        if float(f_Balance) <= tokenAmount:
            tokenAmount = float(f_Balance)
            g_UserStatus[userId]['curTokenAmount'] = float(f_Balance)

        await updateSetFloatWhereStr("tbl_users", field, f_Balance - tokenAmount, "UserID", userId)

        previousWagered = await readFieldsWhereStr("tbl_users", wagerField, kind)
        oldWagerAmount = float(previousWagered[0][0])
        await updateSetFloatWhereStr("tbl_users", wagerField, oldWagerAmount + tokenAmount, "UserID", userId)
    
        coinHistory = g_UserStatus[userId]['coinHistory']
        finalCoin = g_UserStatus[userId]['finalCoin']

        cashOutId = g_UserStatus[userId]['cashOutCoinFlipCnt']
        if cashOutId > 0:
            sGreeting = f"You Won!🎉\n{coinHistory}\n"
            keyboard = [
                [
                    InlineKeyboardButton("Heads", callback_data="Heads"),
                    InlineKeyboardButton("Tails", callback_data="Tails"),
                ],
                [
                    InlineKeyboardButton("Cashout", callback_data="cashOutCoinFlip"),
                ]
            ]
            await query.message.edit_text(
                f"{sGreeting}Current Coin: {str(finalCoin['label'])}\n\nCashout : x{g_HiloCashOut[cashOutId]}\nCashout:" + "{:.4f}".format(
                    g_UserStatus[userId]['curTokenAmount'] * g_HiloCashOut[cashOutId]) + getUnitString(g_UserStatus[userId]['tokenMode']) + "\nWhat is your next guess? Heads or Tails?",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return BETTINGCOINFLIP
        else:
            sGreeting = "CoinFlip Game started!\n"
            keyboard = [
                [
                    InlineKeyboardButton("Heads", callback_data="Heads"),
                    InlineKeyboardButton("Tails", callback_data="Tails"),
                ]
            ]
            await query.message.edit_text(
                f"{sGreeting}\nWhat is your next guess? Heads or Tails?",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return BETTINGCOINFLIP
    else:
        None


async def _high(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    userId = query.from_user.id
    global g_UserStatus
    cardHistory = g_UserStatus[userId]['cardHistory']
    prevCard = g_UserStatus[userId]['prevCard']

    card = None
    while True:
        card = controlRandCard(True, cardHistory, prevCard)
        if card['value'] != prevCard['value'] and card['label'] not in cardHistory:
            break
    g_UserStatus[userId]['cardHistory'] = cardHistory + prevCard['label'] + " "
    if card['value'] > prevCard['value']:
        g_UserStatus[userId]['cashOutHiloCnt'] += 1
        g_UserStatus[userId]['nextCard'] = card
        return await _panelHiloOrCoinFlip(update, context)
    else:
        sCardHistory = g_UserStatus[userId]['cardHistory']
        tokenMode = g_UserStatus[userId]['tokenMode']
        tokenAmount = g_UserStatus[userId]['curTokenAmount']
        init(userId)
        g_UserStatus[userId]['tokenMode'] = tokenMode
        g_UserStatus[userId]['curTokenAmount'] = tokenAmount
        g_UserStatus[userId]['cashOutHiloCnt'] = 0

        kind = "UserID=\"{}\"".format(userId)
        wallet = await readFieldsWhereStr("tbl_users", "Wallet", kind)
        address = wallet[0][0]
        web3 = None
        tokenMode = g_UserStatus[userId]['tokenMode']
        if tokenMode == ETH:
            web3 = g_ETH_Web3
        else:
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
    while True:
        card = controlRandCard(False, cardHistory, prevCard)
        if prevCard != None and card['value'] != prevCard['value']:
            break
    g_UserStatus[userId]['cardHistory'] = cardHistory + prevCard['label'] + " "
    if card['value'] < prevCard['value']:
        g_UserStatus[userId]['nextCard'] = card
        g_UserStatus[userId]['cashOutHiloCnt'] += 1
        return await _panelHiloOrCoinFlip(update, context)
    else:
        g_UserStatus[userId]['cashOutHiloCnt'] = 0
        sCardHistory = g_UserStatus[userId]['cardHistory']
        tokenMode = g_UserStatus[userId]['tokenMode']
        tokenAmount = g_UserStatus[userId]['curTokenAmount']
        init(userId)
        g_UserStatus[userId]['tokenMode'] = tokenMode
        g_UserStatus[userId]['curTokenAmount'] = tokenAmount

        kind = "UserID=\"{}\"".format(userId)
        wallet = await readFieldsWhereStr("tbl_users", "Wallet", kind)
        address = wallet[0][0]
        web3 = None
        tokenMode = g_UserStatus[userId]['tokenMode']
        if tokenMode == ETH:
            web3 = g_ETH_Web3
        else:
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


async def _cashoutHilo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:  # TODO
    query = update.callback_query
    userId = query.from_user.id
    global g_UserStatus

    kind = "UserID=\"{}\"".format(userId)
    wallet = await readFieldsWhereStr("tbl_users", "Wallet", kind)
    address = wallet[0][0]
    web3 = None
    field = "ETH_Amount"
    winsField = "ETH_Wins"
    tokenMode = g_UserStatus[userId]['tokenMode']
    if tokenMode == ETH:
        web3 = g_ETH_Web3
    else:
        web3 = g_BSC_Web3
        field = "BNB_Amount"
        winsField = "BNB_Wins"
    f_Balance = await getBalance(address, web3, userId)

    cashOutId = g_UserStatus[userId]['cashOutHiloCnt']
    tokenMode = g_UserStatus[userId]['tokenMode']
    curTokenAmount = g_UserStatus[userId]['curTokenAmount']
    init(userId)
    g_UserStatus[userId]['curTokenAmount'] = curTokenAmount
    profit = curTokenAmount * g_HiloCashOut[cashOutId]
    await updateSetFloatWhereStr("tbl_users", field, (f_Balance + profit), "UserID", userId)

    previousWins = await readFieldsWhereStr("tbl_users", winsField, kind)
    oldWagerAmount = float(previousWins[0][0])
    await updateSetFloatWhereStr("tbl_users", winsField, oldWagerAmount + profit - curTokenAmount, "UserID", userId)

    f_Balance = await getBalance(address, web3, userId)
    keyboard = [
        [
            InlineKeyboardButton("Play Again", callback_data="againHilo"),
            InlineKeyboardButton("Change Bet", callback_data="changeBet"),
            InlineKeyboardButton("Cancel", callback_data="Cancel"),
        ]
    ]
    await query.message.edit_text(
        f"🏆🏆🏆\n\nYou won!\n\nCashout : x{g_HiloCashOut[cashOutId]}\nCashout : " + "{:.4f}".format(
            profit) + getUnitString(tokenMode) + f"\nBalance:{f_Balance} {getUnitString(tokenMode)}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return AGAINHILO

########################################################################
#                              +Slot                                   #
########################################################################


async def playSlot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    userInfo = update.message.from_user
    print('{} starts SLOT, his user ID: {} '.format(
        userInfo['username'], userInfo['id']))
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
    wagerField = "ETH_Wagered"
    winsField = "ETH_Wins"
    tokenMode = g_UserStatus[userId]['tokenMode']

    if tokenMode == ETH:
        web3 = g_ETH_Web3
    else:
        web3 = g_BSC_Web3
        field = "BNB_Amount"
        wagerField = "BNB_Wagered"
        winsField = "BNB_Wins"

    f_Balance = await getBalance(address, web3, userId)

    if float(f_Balance) <= 0:
        await query.message.edit_text(
            "Insufficient funds.\n/start\n/deposit"
        )
        return

    tokenAmount = g_UserStatus[userId]['curTokenAmount']
    if float(f_Balance) <= float(tokenAmount):
        tokenAmount = float(f_Balance)
        g_UserStatus[userId]['curTokenAmount'] = float(f_Balance)

    await updateSetFloatWhereStr("tbl_users", field, f_Balance - tokenAmount, "UserID", userId)

    previousWagered = await readFieldsWhereStr("tbl_users", wagerField, kind)
    oldWagerAmount = float(previousWagered[0][0])
    await updateSetFloatWhereStr("tbl_users", wagerField, oldWagerAmount + tokenAmount, "UserID", userId)

    slot = roll()
    label = slot["label"]
    res = ""
    if slot["value"] == True:
        cashout = slot["cashout"]
        wonAmount = g_UserStatus[userId]['curTokenAmount'] * cashout
        res = "You Won " + truncDecimal7(wonAmount) + getUnitString(
            g_UserStatus[userId]['tokenMode']) + f"💰\nCashout : x{cashout}"
        await updateSetFloatWhereStr("tbl_users", field, wonAmount + f_Balance, "UserID", userId)

        previousWins = await readFieldsWhereStr("tbl_users", winsField, kind)
        oldWagerAmount = float(previousWins[0][0])
        await updateSetFloatWhereStr("tbl_users", winsField, oldWagerAmount + wonAmount - g_UserStatus[userId]['curTokenAmount'], "UserID", userId)
    else:
        res = "\nYou lost " + str(g_UserStatus[userId]['curTokenAmount']) + \
            " " + getUnitString(g_UserStatus[userId]['tokenMode']) + "💸"
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
#                              +CoinFilp                               #
########################################################################

async def _heads(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    userId = query.from_user.id
    global g_UserStatus
    
    coin = _getRandCoin()
    if coin['value'] == 0:
        kind = "UserID=\"{}\"".format(userId)
        wallet = await readFieldsWhereStr("tbl_users", "Wallet", kind)
        address = wallet[0][0]
        web3 = None
        field = "ETH_Amount"
        winsField = "ETH_Wins"
        tokenMode = g_UserStatus[userId]['tokenMode']
        if tokenMode == ETH:
            web3 = g_ETH_Web3
        else:
            web3 = g_BSC_Web3
            field = "BNB_Amount"
            winsField = "BNB_Wins"
        f_Balance = await getBalance(address, web3, userId)

        tokenMode = g_UserStatus[userId]['tokenMode']
        curTokenAmount = g_UserStatus[userId]['curTokenAmount']
        init(userId)
        g_UserStatus[userId]['curTokenAmount'] = curTokenAmount
        profit = curTokenAmount * 2
        await updateSetFloatWhereStr("tbl_users", field, (f_Balance + profit), "UserID", userId)

        previousWins = await readFieldsWhereStr("tbl_users", winsField, kind)
        oldWagerAmount = float(previousWins[0][0])
        await updateSetFloatWhereStr("tbl_users", winsField, oldWagerAmount + profit - curTokenAmount, "UserID", userId)
            
        keyboard = [
            [
                InlineKeyboardButton("Play Again", callback_data="againCoinFlip"),
                InlineKeyboardButton("Change Bet", callback_data="changeBet"),
                InlineKeyboardButton("Cancel", callback_data="Cancel"),
            ]
        ]
        await query.message.edit_text(
            f"🏆🏆🏆\n\nYou won!\n\n{coin['label']}\nCashout : x2\nCashout : " + "{:.4f}".format(
                profit) + getUnitString(tokenMode) + f"\nBalance:{f_Balance + profit} {getUnitString(tokenMode)}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return AGAINCOINFLIP
    else:
        tokenMode = g_UserStatus[userId]['tokenMode']
        tokenAmount = g_UserStatus[userId]['curTokenAmount']
        init(userId)
        g_UserStatus[userId]['tokenMode'] = tokenMode
        g_UserStatus[userId]['curTokenAmount'] = tokenAmount
        g_UserStatus[userId]['cashOutCoinFlipCnt'] = 0
        
        kind = "UserID=\"{}\"".format(userId)
        wallet = await readFieldsWhereStr("tbl_users", "Wallet", kind)
        address = wallet[0][0]
        web3 = None
        tokenMode = g_UserStatus[userId]['tokenMode']
        if tokenMode == ETH:
            web3 = g_ETH_Web3
        else:
            web3 = g_BSC_Web3
        f_Balance = await getBalance(address, web3, userId)

        keyboard = [
            [
                InlineKeyboardButton("Play Again", callback_data="againCoinFlip"),
                InlineKeyboardButton("Change Bet", callback_data="changeBet"),
                InlineKeyboardButton("Cancel", callback_data="Cancel"),
            ]
        ]
        await query.message.edit_text(
            f"Busted! ❌\n\n{coin['label']}\n\nDo you want to play again?\n\nBalance:{f_Balance} {getUnitString(tokenMode)}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return AGAINCOINFLIP

async def _tails(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    userId = query.from_user.id
    global g_UserStatus
    coinHistory = g_UserStatus[userId]['coinHistory']
    
    coin = _getRandCoin()
    g_UserStatus[userId]['coinHistory'] = coinHistory + coin['label']
    if coin['value'] == 1:
        kind = "UserID=\"{}\"".format(userId)
        wallet = await readFieldsWhereStr("tbl_users", "Wallet", kind)
        address = wallet[0][0]
        web3 = None
        field = "ETH_Amount"
        winsField = "ETH_Wins"
        tokenMode = g_UserStatus[userId]['tokenMode']
        if tokenMode == ETH:
            web3 = g_ETH_Web3
        else:
            web3 = g_BSC_Web3
            field = "BNB_Amount"
            winsField = "BNB_Wins"
        f_Balance = await getBalance(address, web3, userId)

        tokenMode = g_UserStatus[userId]['tokenMode']
        curTokenAmount = g_UserStatus[userId]['curTokenAmount']
        init(userId)
        g_UserStatus[userId]['curTokenAmount'] = curTokenAmount
        profit = curTokenAmount * 2
        await updateSetFloatWhereStr("tbl_users", field, (f_Balance + profit), "UserID", userId)

        previousWins = await readFieldsWhereStr("tbl_users", winsField, kind)
        oldWagerAmount = float(previousWins[0][0])
        await updateSetFloatWhereStr("tbl_users", winsField, oldWagerAmount + profit - curTokenAmount, "UserID", userId)
            
        keyboard = [
            [
                InlineKeyboardButton("Play Again", callback_data="againCoinFlip"),
                InlineKeyboardButton("Change Bet", callback_data="changeBet"),
                InlineKeyboardButton("Cancel", callback_data="Cancel"),
            ]
        ]
        await query.message.edit_text(
            f"🏆🏆🏆\n\nYou won!\n\n{coin['label']}\nCashout : x2\nCashout : " + "{:.4f}".format(
                profit) + getUnitString(tokenMode) + f"\nBalance:{f_Balance + profit} {getUnitString(tokenMode)}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return AGAINCOINFLIP
    else:
        sCoinHistory = g_UserStatus[userId]['coinHistory']
        tokenMode = g_UserStatus[userId]['tokenMode']
        tokenAmount = g_UserStatus[userId]['curTokenAmount']
        init(userId)
        g_UserStatus[userId]['tokenMode'] = tokenMode
        g_UserStatus[userId]['curTokenAmount'] = tokenAmount
        g_UserStatus[userId]['cashOutCoinFlipCnt'] = 0
        
        kind = "UserID=\"{}\"".format(userId)
        wallet = await readFieldsWhereStr("tbl_users", "Wallet", kind)
        address = wallet[0][0]
        web3 = None
        tokenMode = g_UserStatus[userId]['tokenMode']
        if tokenMode == ETH:
            web3 = g_ETH_Web3
        else:
            web3 = g_BSC_Web3
        f_Balance = await getBalance(address, web3, userId)

        keyboard = [
            [
                InlineKeyboardButton("Play Again", callback_data="againCoinFlip"),
                InlineKeyboardButton("Change Bet", callback_data="changeBet"),
                InlineKeyboardButton("Cancel", callback_data="Cancel"),
            ]
        ]
        await query.message.edit_text(
            f"Busted! ❌\n\n{sCoinHistory}\n\nFinal Coin:{coin['label']}\n\nDo you want to play again?\n\nBalance:{f_Balance} {getUnitString(tokenMode)}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return AGAINCOINFLIP

async def _cashoutCoinFlip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:  # TODO
    query = update.callback_query
    userId = query.from_user.id
    global g_UserStatus

    kind = "UserID=\"{}\"".format(userId)
    wallet = await readFieldsWhereStr("tbl_users", "Wallet", kind)
    address = wallet[0][0]
    web3 = None
    field = "ETH_Amount"
    winsField = "ETH_Wins"
    tokenMode = g_UserStatus[userId]['tokenMode']
    if tokenMode == ETH:
        web3 = g_ETH_Web3
    else:
        web3 = g_BSC_Web3
        field = "BNB_Amount"
        winsField = "BNB_Wins"
    f_Balance = await getBalance(address, web3, userId)

    cashOutId = g_UserStatus[userId]['cashOutCoinFlipCnt']
    tokenMode = g_UserStatus[userId]['tokenMode']
    curTokenAmount = g_UserStatus[userId]['curTokenAmount']
    init(userId)
    g_UserStatus[userId]['curTokenAmount'] = curTokenAmount
    profit = curTokenAmount * g_HiloCashOut[cashOutId]
    await updateSetFloatWhereStr("tbl_users", field, (f_Balance + profit), "UserID", userId)

    previousWins = await readFieldsWhereStr("tbl_users", winsField, kind)
    oldWagerAmount = float(previousWins[0][0])
    await updateSetFloatWhereStr("tbl_users", winsField, oldWagerAmount + profit - curTokenAmount, "UserID", userId)

    f_Balance = await getBalance(address, web3, userId)
    keyboard = [
        [
            InlineKeyboardButton("Play Again", callback_data="againCoinFlip"),
            InlineKeyboardButton("Change Bet", callback_data="changeBet"),
            InlineKeyboardButton("Cancel", callback_data="Cancel"),
        ]
    ]
    await query.message.edit_text(
        f"🏆🏆🏆\n\nYou won!\n\nCashout : x{g_HiloCashOut[cashOutId]}\nCashout : " + "{:.4f}".format(
            profit) + getUnitString(tokenMode) + f"\nBalance:{f_Balance} {getUnitString(tokenMode)}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return AGAINCOINFLIP

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
    print('{} tries to withdraw, his user ID: {} '.format(
        userInfo['username'], userInfo['id']))

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


async def confirm_dlg_withdraw(update: Update, msg: str) -> int:
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


async def eth_bnb_dlg(update: Update, msg: str) -> int:
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


async def _eth_bnb_dlg(update: Update, msg: str) -> int:
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
    if status == ST_WITHDRAW:
        str_Guide = f"How much do you wanna withdraw?\nCurrent Balance : {f_Balance} ETH\ne.g /0.01"
        g_UserStatus[userId]['withdrawTokenType'] = ETH
        return await confirm_dlg_withdraw(update, str_Guide)
    if status == ST_ADS_PAY:
        durationIndex = g_UserStatus[userId]['advertise']['duration']
        adsPayAmount = g_adsETHPrice[durationIndex]
        if f_Balance < adsPayAmount:
            keyboard = [
                [
                    InlineKeyboardButton("Cancel", callback_data="Cancel"),
                ]
            ]
            await query.message.edit_text(
                "Insufficient Balance.\nYour current balance is {} ETH\nYou must pay {} ETH to create advertise".format(
                    f_Balance, adsPayAmount),
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return CANCEL
        str_Guide = f"You must pay {adsPayAmount} ETH\nCurrent Balance : {f_Balance} ETH"
        g_UserStatus[userId]['advertise']['adsPayTokenType'] = ETH
        g_UserStatus[userId]['advertise']['adsPayTokenAmount'] = adsPayAmount
        return await confirm_dlg_pay_ads(update, str_Guide)
    else:
        str_Guide = f"How much do you wanna bet?\nCurrent Balance : {f_Balance} ETH\n"
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
    if status == ST_WITHDRAW:
        str_Guide = f"How much do you wanna withdraw?\nCurrent Balance : {f_Balance} BNB\ne.g /0.01"
        g_UserStatus[userId]['withdrawTokenType'] = BNB
        return await confirm_dlg_withdraw(update, str_Guide)
    if status == ST_ADS_PAY:
        durationIndex = g_UserStatus[userId]['advertise']['duration']
        adsPayAmount = g_adsBNBPrice[durationIndex]
        if f_Balance < adsPayAmount:
            keyboard = [
                [
                    InlineKeyboardButton("Cancel", callback_data="Cancel"),
                ]
            ]
            await query.message.edit_text(
                "Insufficient Balance.\nYour current balance is {} BNB\nYou must pay {} BNB to create advertise".format(
                    f_Balance, adsPayAmount),
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return CANCEL
        str_Guide = f"You must pay {adsPayAmount} BNB\nCurrent Balance : {f_Balance} BNB"
        g_UserStatus[userId]['advertise']['adsPayTokenType'] = BNB
        g_UserStatus[userId]['advertise']['adsPayTokenAmount'] = adsPayAmount
        return await confirm_dlg_pay_ads(update, str_Guide)
    else:
        str_Guide = f"How much do you wanna bet?\nCurrent Balance : {f_Balance} BNB\n"
        return await confirm_dlg_game(update, context, str_Guide, userId, g_Unit_BNB, f_Balance)


async def confirm_dlg_game(update: Update, context: ContextTypes.DEFAULT_TYPE, msg: str, userId: str, tokenAmount: float, balance: float) -> int:
    tokenMode = g_UserStatus[userId]['tokenMode']
    sAmount = f"\nYou can bet {tokenAmount}" + getUnitString(tokenMode) + "($" + truncDecimal(await getPricefromAmount(tokenAmount, tokenMode)) + ")"
    # if tokenMode == ETH:
    #     g_UserStatus[userId]['ethBetAmount'] = tokenAmount
    # else:
    #     g_UserStatus[userId]['bnbBetAmount'] = tokenAmount
    query = update.callback_query

    sPlayButton = ""
    sMark = ""
    status = g_UserStatus[userId]['status']
    match status:
        case 2:  # ST_HILO
            sPlayButton = "Play"
            sMark = g_HiloMark
        case 3:  # ST_COINFLIP
            sPlayButton = "Play"
            sMark = g_CoinFlipMark
        case 4:  # ST_SLOT
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
        print("Error", e)

    return LASTSELECT

########################################################################
#                         +changeBetAmount                             #
########################################################################


async def _changeBetAmount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query: CallbackQuery = update.callback_query

    userId = query.from_user.id

    global g_UserStatus
    tokenMode = g_UserStatus[userId]['tokenMode']
    curTokenAmount = g_UserStatus[userId]['curTokenAmount']
    init(userId)
    g_UserStatus[userId]['tokenMode'] = tokenMode
    g_UserStatus[userId]['curTokenAmount'] = curTokenAmount

    kind = "UserID=\"{}\"".format(userId)
    wallet = await readFieldsWhereStr("tbl_users", "Wallet", kind)

    address = wallet[0][0]
    # query.answer()
    param = query.data.split(":")[1]

    balance = ""
    tokenMode = g_UserStatus[userId]['tokenMode']
    if tokenMode == ETH:
        UnitToken = g_Unit_ETH
        balance = str(await getBalance(address, g_ETH_Web3, userId))
    else:
        UnitToken = g_Unit_BNB
        balance = str(await getBalance(address, g_BSC_Web3, userId))
    prevTokenAmount = g_UserStatus[userId]['curTokenAmount']
    if int(param) == 0:
        g_UserStatus[userId]['curTokenAmount'] = float(
            g_UserStatus[userId]['curTokenAmount']) / 2.0
    else:
        g_UserStatus[userId]['curTokenAmount'] = float(
            g_UserStatus[userId]['curTokenAmount']) * 2.0

    if float(g_UserStatus[userId]['curTokenAmount']) < UnitToken:
        g_UserStatus[userId]['curTokenAmount'] = UnitToken

    if float(g_UserStatus[userId]['curTokenAmount']) >= float(balance):
        g_UserStatus[userId]['curTokenAmount'] = float(balance)

    str_Guide = f"How much do you wanna bet?\nCurrent Balance : " + \
        balance + " " + getUnitString(tokenMode) + "\n"

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
    global g_UserStatus
    text = update.message.text

    if not (len(text.split('/')) == 2 and isFloat(text.split('/')[1])):
        await update.message.reply_text(
            "Incorrect form type.\ne.g /0.01\n/start"
        )
        return

    userId = update.message.from_user['id']
    kind = "UserID=\"{}\"".format(userId)

    amount = text.split('/')[1]

    field = ''
    symbol = ''
    web3 = None
    tokenMode = ETH
    gasFee = float(0)

    if g_UserStatus[userId]['status'] == ST_WITHDRAW:
        tokenMode = g_UserStatus[userId]['withdrawTokenType']
    else:
        tokenMode = g_UserStatus[userId]['advertise']['adsPayTokenType']

    if tokenMode == ETH:
        field = 'ETH_Amount'
        symbol = 'ETH'
        web3 = g_ETH_Web3
        gasFee = ETH_FIXED_WITHDRAW_FEE
    else:
        field = 'BNB_Amount'
        symbol = 'BNB'
        web3 = g_BSC_Web3
        gasFee = BSC_FIXED_WITHDRAW_FEE

    keyboard = [
        [
            InlineKeyboardButton("Cancel", callback_data="Cancel"),
        ]
    ]

    fee = float(0)
    fixedFee = float(0)
    if g_UserStatus[userId]['status'] == ST_WITHDRAW:
        fee = await calculateTotalWithdrawFee(web3, float(amount))
        fixedFee = await calculateFixedFee(web3)
        if fee > float(amount):
            await update.message.reply_text(
                "Withdraw amount must be bigger than fee.\nFee is House cut(5%) and gas(${}).\nCurrent House cut is {} {}.$1 is {} {}\n".format(
                    gasFee, float(amount) * HOUSE_CUT_FEE / PERCENTAGE, symbol, fixedFee, symbol),
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return

    balance = await readFieldsWhereStr('tbl_users', field, kind)

    if float(amount) > float(balance[0][0]):
        await update.message.reply_text(
            "Insufficient Balance.\nYour current balance is {} {}\n/start".format(
                balance[0][0], symbol),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    if g_UserStatus[userId]['status'] == ST_WITHDRAW:
        g_UserStatus[userId]['withdrawAmount'] = float(amount)
    else:
        g_UserStatus[userId]['adsPayAmount'] = float(amount)

    if g_UserStatus[userId]['status'] == ST_WITHDRAW:
        await update.message.reply_text(
            "Fee is {} {}.\nHouse Cut({} {}) and ${}({} {})\nYou will receive {} {}\nPlease enter your wallet address to withdraw\ne.g /0x43cbE0ce689dbC237A517EFAAe7B8c290C4e64df".format(
                fee, symbol, float(amount) * HOUSE_CUT_FEE / PERCENTAGE, symbol, str(gasFee).rstrip('0').rstrip('.'), fixedFee, symbol, '{:.5f}'.format(float(amount) - fee).rstrip('0'), symbol),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return PANELWITHDRAW
    else:
        amount = float(balance[0][0]) - float(amount)

        await updateSetFloatWhereStr("tbl_users", field, amount, "UserID", userId)
        await update.message.reply_text(
            "Booked your ads successfully\nYour current balance is {} {}\n/start".format(
                float(amount), symbol),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def panelWithdraw(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    g_UserStatus
    userId = update.message.from_user['id']
    text = update.message.text

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

    if not len(text.split('/')) == 2:
        await update.message.reply_text(
            "Incorrect form type.\ne.g /0x43cbE0ce689dbC237A517EFAAe7B8c290C4e64df\n/start"
        )
        return

    if not isValidContractOrWallet(w3, text.split('/')[1]):
        await update.message.reply_text(
            "Invalid wallet address.\nPlease check address again.\n/start"
        )
        return

    wallet = text.split('/')[1]

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
    keyboard = [
        [
            InlineKeyboardButton("Back", callback_data="Cancel"),
        ]
    ]

    await update.message.reply_text(
        g_Greetings + g_Help + g_Wallet + g_Deposit + g_Withdraw +
        g_Hilo + g_Slot + g_LeaderBoard + g_AdsBoard,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return CANCEL


async def _help(update: Update, context: CallbackContext) -> None:
    query = update.callback_query

    keyboard = [
        [
            InlineKeyboardButton("Back", callback_data="Cancel"),
        ]
    ]
    await query.message.edit_text(
        g_Greetings + g_Help + g_Wallet + g_Deposit + g_Withdraw +
        g_Hilo + g_Slot + g_LeaderBoard + g_AdsBoard,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return CANCEL

########################################################################
#                             +advertise                               #
########################################################################


async def adsBoard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    userInfo = update.message.from_user
    userId = userInfo['id']
    userName = userInfo['username']

    current_utc_time = datetime.datetime.now(pytz.utc)
    formatted_time = current_utc_time.strftime("%Y-%m-%d %H:%M:%S")

    current_hour = current_utc_time.hour
    # kind = "UserID=\"{}\"".format(userId)

    keyboard = []
    btnHome = [InlineKeyboardButton("Home", callback_data="Cancel")]

    id = 0
    boardButton = []
    for i in range(current_hour + 1, current_hour + 14):
        if i > 24:
            i = i - 24
        callbackData = "adsTime:" + str(i)
        timeFormat = ""
        clock = ""
        if i > 12:
            timeFormat = "PM"
            clock = str(i - 12)
        else:
            timeFormat = "AM"
            clock = str(i)
        buttonStr = clock + timeFormat + " UTC"
        button = InlineKeyboardButton(
            buttonStr, callback_data=callbackData)
        boardButton.append(button)
        if (id + 1) % 2 == 0:
            keyboard.append(boardButton)
            boardButton = []
        id += 1

    keyboard.append(btnHome)

    advertise = f"👉📃 Book the ads at the following time.\nCurrent UTC time is {formatted_time}"
    await update.message.reply_text(
        f"{advertise}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return ADSTIME


async def _adsBoard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    userId = query.from_user.id

    current_utc_time = datetime.datetime.now(pytz.utc)
    formatted_time = current_utc_time.strftime("%Y-%m-%d %H:%M:%S")

    current_hour = current_utc_time.hour

    # kind = "UserID=\"{}\"".format(userId)
    keyboard = []
    btnHome = [InlineKeyboardButton("Home", callback_data="Cancel")]

    id = 0
    boardButton = []
    for i in range(current_hour + 1, current_hour + 14):
        if i > 24:
            i = i - 24
        callbackData = "adsTime:" + str(i)
        timeFormat = ""
        clock = ""
        if i > 12:
            timeFormat = "PM"
            clock = str(i - 12)
        else:
            timeFormat = "AM"
            clock = str(i)
        buttonStr = clock + timeFormat + " UTC"
        button = InlineKeyboardButton(
            buttonStr, callback_data=callbackData)
        boardButton.append(button)
        if (id + 1) % 2 == 0:
            keyboard.append(boardButton)
            boardButton = []
        id += 1

    keyboard.append(btnHome)

    advertise = f"👉📃 Book the ads at the following time.\nCurrent UTC time is {formatted_time}"
    await query.message.edit_text(
        f"{advertise}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return ADSTIME


async def confirm_dlg_pay_ads(update: Update, msg: str) -> int:
    query = update.callback_query
    keyboard = [
        [
            InlineKeyboardButton("Confirm", callback_data="ConfirmPayAds"),
            InlineKeyboardButton("Cancel", callback_data="Cancel")
        ]
    ]
    await query.message.edit_text(
        msg,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ADSPAYCONFIRM


async def _adsConfirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    userId = query.from_user.id

    keyboard = []
    btnHome = [InlineKeyboardButton("Home", callback_data="Cancel")]

    id = 0
    for payButton in g_AdsPayButton:
        callbackData = "adsPay:" + str(id)
        boardButton = [
            InlineKeyboardButton(payButton, callback_data=callbackData)
        ]
        keyboard.append(boardButton)
        id += 1
    keyboard.append(btnHome)

    await query.message.edit_text(
        f"Please select your ad duration",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ADSPAY


async def adsDesc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    global g_UserStatus
    userId = update.message.from_user['id']
    text = update.message.text

    backBtn = [
        [InlineKeyboardButton("Back", callback_data="Cancel")]
    ]

    if text[0] != '/':
        await update.message.reply_text(
            f"Incorrect form field.\ne.g /Lorem",
            reply_markup=InlineKeyboardMarkup(backBtn)
        )
        return

    # If content ...
    content = text[1:]
    if len(content) > 30:
        await update.message.reply_text(
            f"Limited to 30 characters maximum.\ne.g /Lorem",
            reply_markup=InlineKeyboardMarkup(backBtn)
        )
        return

    g_UserStatus[userId]['advertise']['content'] = content

    keyboard = [
        [
            InlineKeyboardButton("Confirm", callback_data="adsConfirm"),
            InlineKeyboardButton("Cancel", callback_data="Cancel"),
        ]
    ]
    await update.message.reply_text(
        f"Your ad will be showed on leaderboard, like this\n\n{g_UserStatus[userId]['advertise']['url']}\n{content}\n\nPlease confirm your ad before payment",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ADSCONFIRM


async def adsUrl(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    global g_UserStatus
    userId = update.message.from_user['id']
    text = update.message.text

    keyboard = [
        [
            InlineKeyboardButton("Back", callback_data="Cancel"),
        ]
    ]

    if text[0] != '/':
        await update.message.reply_text(
            f"Incorrect form field.\ne.g /https://t.me/AleekkCalls",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # If url ...
    url = text[1:]

    if not isValidUrl(url):
        await update.message.reply_text(
            f"URL is invalid.\nPlease check url again.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    if not isOpenedUrl(url):
        await update.message.reply_text(
            f"Can not open the url.\nPlease check url again.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    g_UserStatus[userId]['advertise']['url'] = url

    keyboard = [
        [
            InlineKeyboardButton("Back", callback_data="Cancel"),
        ]
    ]
    await update.message.reply_text(
        f"Your ad URL is\n{url}\n👉📖Kindly submit your ad text\n    Limited to 30 characters maximum.\n   e.g /Lorem spreum..",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return ADSDESC


async def _adsTime(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    global g_UserStatus
    query = update.callback_query
    userId = query.from_user.id
    param = query.data.split(":")[1]

    g_UserStatus[userId]['advertise']['time'] = int(param) + 1
    keyboard = [
        [
            InlineKeyboardButton("Home", callback_data="Cancel")
        ]
    ]

    await query.message.edit_text(
        f"👉🔗 Please submit the URL to be featured in the ad.\n    e.g /https://t.me/AleekkCalls",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ADSURL


async def _adsPayConfirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    global g_UserStatus
    query = update.callback_query
    userId = query.from_user.id

    url = g_UserStatus[userId]['advertise']['url']
    content = g_UserStatus[userId]['advertise']['content']
    time = g_UserStatus[userId]['advertise']['time']
    durationIndex = g_UserStatus[userId]['advertise']['duration']
    duration = int(g_duration[durationIndex])
    tokenMode = g_UserStatus[userId]['advertise']['adsPayTokenType']
    amount = g_UserStatus[userId]['advertise']['adsPayTokenAmount']

    await createAds(userId, url, content, time, duration, tokenMode, amount)

    g_UserStatus[userId]["advertise"] = {
        "time": int(0),
        "duration": int(0),
        "url": "",
        "content": "",
        "adsPayTokenType": ETH,
        "adsPayTokenAmount": float(0)
    }
    keyboard = [
        [
            InlineKeyboardButton("Home", callback_data="Cancel")
        ]
    ]
    await query.message.edit_text(
        f"👉 You payment accepted",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return CANCEL


async def _adsPay(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    userId = query.from_user.id
    param = query.data.split(":")[1]

    global g_UserStatus
    g_UserStatus[userId]['status'] = ST_ADS_PAY
    g_UserStatus[userId]['advertise']['duration'] = int(param)

    str_Guide = "Which token do you wanna pay?\n"
    return await _eth_bnb_dlg(update, str_Guide)

########################################################################
#                               +board                                 #
########################################################################


async def board(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    topWagers = "📈 Top 5 Wagers 📉"
    topWinners = "🏆 Top 5 Winners 🎊"

    # get all adsContent from database
    adsContent = "All ads will be showed here..."

    ethPrice = await readFieldsWhereStr('tbl_cryptos', 'Price', 'Symbol=\'eth\'')
    ethPrice = ethPrice[0][0]

    bnbPrice = await readFieldsWhereStr('tbl_cryptos', 'Price', 'Symbol=\'bnb\'')
    bnbPrice = bnbPrice[0][0]

    topWagered = await getTopFieldsByLimit('tbl_users', f'UserName, {ethPrice} * ETH_Wagered + {bnbPrice} * BNB_Wagered AS Total_Wagered', 'Total_Wagered', 5)
    topWins = await getTopFieldsByLimit('tbl_users', f'UserName, {ethPrice} * ETH_Wins + {bnbPrice} * BNB_Wins AS Total_Wins', 'Total_Wins', 5)

    i = 0
    while i < len(topWagered):
        topWagers += "\n" + "@" + \
            topWagered[i][0] + ": " + \
            "{:.2f}".format(topWagered[i][1]) + " USD"
        topWinners += "\n" + "@" + \
            topWins[i][0] + ": " + "{:.2f}".format(topWins[i][1]) + " USD"

        i += 1

    keyboard = [
        [
            InlineKeyboardButton("Home", callback_data="Cancel")
        ]
    ]

    current_time = datetime.datetime.now()
    current_time = current_time.replace(hour=current_time.hour + 1)
    formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
    adsField = "Url, Content"
    adsKind = f"'{formatted_time}' BETWEEN StartTime AND ExpiredAt"
    # adsKind = "NOW() BETWEEN CreatedAt AND StartTime"

    adsResult = await readFieldsWhereStr('tbl_ads', adsField, adsKind)

    for ad in adsResult:
        adsContent += "\n👉 ------------------\n"
        adsContent += ad[0] + "\n"
        adsContent += ad[1] + "\n\n"

    # await context.bot.send_chat_action(query.message.chat_id, telegram.ChatAction.TYPING)
    await update.message.reply_text(
        f"---📜 Leaderboards 🧮---\n\n{topWinners}\n\n{topWagers}\n\n\n{adsContent}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return CANCEL


async def _board(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    topWagers = "📈 Top 5 Wagers 📉"
    topWinners = "🏆 Top 5 Winners 🎊"

    # get all adsContent from database
    adsContent = "All ads will be showed here...\n"

    ethPrice = await readFieldsWhereStr('tbl_cryptos', 'Price', 'Symbol=\'eth\'')
    ethPrice = ethPrice[0][0]

    bnbPrice = await readFieldsWhereStr('tbl_cryptos', 'Price', 'Symbol=\'bnb\'')
    bnbPrice = bnbPrice[0][0]

    topWagered = await getTopFieldsByLimit('tbl_users', f'UserName, {ethPrice} * ETH_Wagered + {bnbPrice} * BNB_Wagered AS Total_Wagered', 'Total_Wagered', 5)
    topWins = await getTopFieldsByLimit('tbl_users', f'UserName, {ethPrice} * ETH_Wins + {bnbPrice} * BNB_Wins AS Total_Wins', 'Total_Wins', 5)

    i = 0
    while i < len(topWagered):
        topWagers += "\n" + "@" + \
            topWagered[i][0] + ": " + \
            "{:.2f}".format(topWagered[i][1]) + " USD"
        topWinners += "\n" + "@" + \
            topWins[i][0] + ": " + "{:.2f}".format(topWins[i][1]) + " USD"

        i += 1

    keyboard = [
        [
            InlineKeyboardButton("Home", callback_data="Cancel")
        ]
    ]

    current_time = datetime.datetime.now()
    current_time = current_time.replace(hour=current_time.hour + 1)
    formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
    adsField = "Url, Content"
    adsKind = f"'{formatted_time}' BETWEEN StartTime AND ExpiredAt"

    adsResult = await readFieldsWhereStr('tbl_ads', adsField, adsKind)

    for ad in adsResult:
        adsContent += "\n👉 ------------------\n"
        adsContent += ad[0] + "\n"
        adsContent += ad[1] + "\n\n"

    query = update.callback_query
    # await context.bot.send_chat_action(query.message.chat_id, telegram.ChatAction.TYPING)
    await query.message.edit_text(
        f"---📜 Leaderboards 🧮---\n\n{topWinners}\n\n{topWagers}\n\n\n{adsContent}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return CANCEL


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    userId = query.from_user.id
    init(userId)

    await start(g_UserStatus[userId]['update'], g_UserStatus[userId]['context'])
    return MAIN


async def end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text(
        "Bye! I hope we can talk again some day.", reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


def init(userId: str):  # TODO
    global g_UserStatus
    g_UserStatus[userId]['cardHistory'] = ""
    g_UserStatus[userId]['prevCard'] = None
    g_UserStatus[userId]['nextCard'] = None
    g_UserStatus[userId]['curTokenAmount'] = float(0)
    g_UserStatus[userId]['tokenMode'] = ETH
    g_UserStatus[userId]['cashOutHiloCnt'] = int(0)
    g_UserStatus[userId]['finalCoin'] = None
    g_UserStatus[userId]['coinHistory'] = ""
    g_UserStatus[userId]['cashOutCoinFlipCnt'] = int(0)

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
    clipboard_text = pyperclip.paste()

############################################################################
#                       complete(1st edition)                              #
############################################################################


def setInterval(func: any, sec: int) -> None:
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
    g_ETH_Contract = g_ETH_Web3.eth.contract(
        address=ETH_CONTRACT_ADDRESS, abi=abi)

    global g_BSC_Contract
    g_BSC_Contract = g_BSC_Web3.eth.contract(
        address=BSC_CONTRACT_ADDRESS, abi=abi)


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
                      CommandHandler("deposit", deposit),
                      CommandHandler("advertise", adsBoard)],
        states={
            MAIN:           [CallbackQueryHandler(_deposit, pattern="Deposit"),
                             CallbackQueryHandler(
                                 _withdraw, pattern="Withdraw"),
                             CallbackQueryHandler(_wallet, pattern="Balance"),
                             CallbackQueryHandler(
                                 _playHilo, pattern="Play Hilo"),
                             CallbackQueryHandler(
                                 _playSlot, pattern="Play Slot"),
                             CallbackQueryHandler(
                                 _playCoinFlip, pattern="Play CoinFlip"),
                             CallbackQueryHandler(_board, pattern="Board"),
                             CallbackQueryHandler(
                                 _adsBoard, pattern="advertise"),
                             CallbackQueryHandler(_help, pattern="Help")],
            WALLET:         [MessageHandler("wallet", wallet)],
            DEPOSIT:        [MessageHandler(filters.TEXT, deposit)],
            SELECT:         [CallbackQueryHandler(funcETH, pattern="funcETH"),
                             CallbackQueryHandler(funcBNB, pattern="funcBNB"),
                             CallbackQueryHandler(cancel, pattern="Cancel")],
            LASTSELECT:    [CallbackQueryHandler(_changeBetAmount, pattern="^changeBetAmount:"),
                            CallbackQueryHandler(cancel, pattern="Cancel"),
                            CallbackQueryHandler(_panelHiloOrCoinFlip, pattern="Play"),
                            CallbackQueryHandler(_panelSlot, pattern="Roll")],
            AGAINSLOT:      [CallbackQueryHandler(cancel, pattern="Cancel"),
                             CallbackQueryHandler(
                                 _panelSlot, pattern="againSlot"),
                             CallbackQueryHandler(_playSlot, pattern="changeBet"),],
            AGAINHILO:      [CallbackQueryHandler(cancel, pattern="Cancel"),
                             CallbackQueryHandler(
                                 _panelHiloOrCoinFlip, pattern="againHilo"),
                             CallbackQueryHandler(_playHilo, pattern="changeBet")],
            AGAINCOINFLIP:      [CallbackQueryHandler(cancel, pattern="Cancel"),
                             CallbackQueryHandler(
                                 _panelHiloOrCoinFlip, pattern="againCoinFlip"),
                             CallbackQueryHandler(_playCoinFlip, pattern="changeBet")],
            PANELDEPOSIT:   [MessageHandler(filters.TEXT, panelDeposit)],
            CANCEL:         [CallbackQueryHandler(cancel, pattern="Cancel")],
            ADSTIME:        [CallbackQueryHandler(_adsTime, pattern="^adsTime:"),
                             CallbackQueryHandler(cancel, pattern="Cancel")],
            ADSURL:         [MessageHandler(filters.TEXT, adsUrl),
                             CallbackQueryHandler(cancel, pattern="Cancel")],
            ADSDESC:        [MessageHandler(filters.TEXT, adsDesc),
                             CallbackQueryHandler(cancel, pattern="Cancel")],
            ADSCONFIRM:     [CallbackQueryHandler(_adsConfirm, pattern="adsConfirm"),
                             CallbackQueryHandler(cancel, pattern="Cancel")],
            ADSPAY:         [CallbackQueryHandler(_adsPay, pattern="^adsPay:"),
                             CallbackQueryHandler(cancel, pattern="Cancel")],
            ADSPAYCONFIRM:  [CallbackQueryHandler(_adsPayConfirm, pattern="ConfirmPayAds"),
                             CallbackQueryHandler(cancel, pattern="Cancel")],
            PANELWITHDRAWADDRESS: [MessageHandler(filters.TEXT, panelWithdrawAddress),
                                   CallbackQueryHandler(cancel, pattern="Cancel")],
            PANELWITHDRAW: [MessageHandler(filters.TEXT, panelWithdraw),
                            CallbackQueryHandler(cancel, pattern="Cancel")],
            BETTINGHILO:    [CallbackQueryHandler(_cashoutHilo, pattern="cashOutHilo"),
                             CallbackQueryHandler(_high, pattern="High"),
                             CallbackQueryHandler(_low, pattern="Low"),],
            BETTINGCOINFLIP:    [CallbackQueryHandler(_cashoutCoinFlip, pattern="cashOutCoinFlip"),
                             CallbackQueryHandler(_heads, pattern="Heads"),
                             CallbackQueryHandler(_tails, pattern="Tails"),],
            COPY:           [CallbackQueryHandler(copyToClipboard, pattern="^copyToClipboard:"),
                             CallbackQueryHandler(cancel, pattern="Cancel")]
        },
        fallbacks=[CommandHandler("end", end)],
        allow_reentry=True,
    )

    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()
