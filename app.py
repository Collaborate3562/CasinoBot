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
import datetime
import json
import logging
import random
import pyperclip
from telegram import __version__ as TG_VER

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
    # Updater,
    # Dispatcher
)

from telebot import TeleBot

from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP

import mysql.connector

db = mysql.connector.connect(host="localhost", user="root", passwd="bluesky0812", database="DB_AleekkCasino")

cur = db.cursor()


class DateTimeEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()

CHOOSE, WALLET, SELECT, STATUS, PAYMENT, DEPOSIT, DISPLAY, COPY, LASTSELECT, AGAINSLOT, AGAINHILO, PANELHILO, PANELSLOT, BETTINGHILO, PANELDEPOSIT, PANELWITHDRAW = range(16)
ST_DEPOSIT, ST_WITHDRAW, ST_HILO, ST_SLOT = range(4)
ETH, BNB = range(2)

g_SlotMark = "🎰 SLOTS 🎰\n\n"
g_HiloMark = "♠️♥️ HILO ♦️♣️\n\n"
g_Cashout = 0
g_Flowers = ['♠️', '♥️', '♣️', '♦️']
g_Numbers = ['A','2','3','4','5','6','7','8','9','10','J','Q','K']
UserName = ""
TOKEN = "6282215563:AAFiWA4Owjxl0n9gfelo2jejlYScz7-UeJI"
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
# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

guestinformation = {}
g_STATUS = 0

# updater = Updater(token=TOKEN, use_context=True)
# dispatcher = updater.dispatcher

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Start the bot and ask what to do when the command /start is issued.
    init()
    user = update.effective_user
    userInfo = update.message.from_user
    global UserName
    UserName = userInfo['username']
    str_Greetings = f"🙋‍♀️Hi @{UserName}\nWelcome to Aleekk Casino!\n"
    str_Intro = f"Please enjoy High-Low & Slot machine games here.\n"
    print('You talk with user {} and his user ID: {} '.format(userInfo['username'], userInfo['id']))
    # guestinformation = {}
    if context.user_data.get("adjustID"):
        context.user_data["adjustID"]=""
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
    print('{} is checking wallet, his user ID: {} '.format(userInfo['username'], userInfo['id']))
    address = await getWallet(UserName)
    eth_amount = await getBalance(address, ETH)
    bnb_amount = await getBalance(address, BNB)
    await update.message.reply_text(
        f"@{UserName}'s wallet\nAddress : {address}\nETH : {eth_amount}\nBNB : {bnb_amount}\n/start"
    )

async def _wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    address = await getWallet(UserName)
    eth_amount = await getBalance(address, ETH)
    bnb_amount = await getBalance(address, BNB)
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
        newCard = controlRandCard(True)
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
        card = controlRandCard(True)
        # card = getRandCard()
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
        card = controlRandCard(False)
        # card = getRandCard()
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
    address = await getWallet(UserName)
    n_Balance = await getBalance(address, g_TokenMode)
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
    address = await getWallet(UserName)
    n_Balance = await getBalance(address, g_TokenMode)
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
    sAmount = f"\nYou can bet {tokenAmount}" + getUnitString(g_TokenMode) + getPricefromAmount(tokenAmount)
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
    if g_TokenMode == ETH :
        UnitToken = g_Unit_ETH
    else :
        UnitToken = g_Unit_BNB
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
    str_Guide = f"How much do you wanna bet?\nCurrent Balance : " + str(await getBalance(await getWallet(UserName), g_TokenMode)) + " " + getUnitString(g_TokenMode) + "\n"
    print("debug 1")
    return await confirm_dlg_game(update, context, str_Guide, g_CurTokenAmount)

async def panelDeposit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    address = await getWallet(UserName)
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

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        g_Greetings + g_Help + g_Wallet + g_Deposit + g_Withdraw + g_Hilo + g_Slot + g_LeaderBoard
    )
 
async def _help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.message.edit_text(
        g_Greetings + g_Help + g_Wallet + g_Deposit + g_Withdraw + g_Hilo + g_Slot + g_LeaderBoard
    )

async def board(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Shows the order of the users who had won\n1. Thomas $999\n2. Thomas $999\n3. Thomas $999"
    )
 
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Cancel booking
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

def getPricefromAmount(amount : float) -> str:
    price = 0
    if g_TokenMode == 0 :
        price = amount * 1700
    else :
        price = amount * 300
    return f" (${price})"

def getUnitString(kind: int) -> str:
    str = ""
    if kind == 0 :
        str = "ETH"
    else :
        str = "BNB"
    return str

async def copyToClipboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query: CallbackQuery = update.callback_query
    query.answer()
    param = query.data.split(":")[1]  
    pyperclip.copy(param)
    print(param)
    pyperclip.paste()

def getCell(num : int) -> str:
    cell = ""
    match num:
        case 0:
            cell="🍉"
        case 1:
            cell="🍎"
        case 2:
            cell="🍌"
        case 3:
            cell="7️⃣"
        case 4:
            cell="🌺"
    return cell

def roll() -> dict:
    slot = dict()
    num1 = random.randint(0, 4)
    num2 = random.randint(0, 4)
    num3 = random.randint(0, 4)
    if num1 == num2 and num2 == num3 :
        slot["value"] = True
    else :
        slot["value"] = False
    label = getCell(num1) + " | " + getCell(num2) + " | " + getCell(num3)
    num = str(num1) + str(num2) + str(num3)
    slot["label"] = label
    slot["num"] = num
    return slot

def controlRandCard(high : bool) -> dict:
    card = None
    loop = 0
    if g_PrevCard == None or g_PrevCard['value'] == 1 or g_PrevCard['value'] == 13:
        print("Starting control")
        card = getRandCard()
    else :
        print("controlling")
        random.seed(random.randint(1000, 2000))
        num = random.randint(1, 1000)
        print(num)
        # if num > 750 and num < 250:
        limit = 700 * random.uniform(0.9, 1.1)
        print(limit)
        if num > limit:
            if high == True :
                while True :
                    loop += 1
                    card = getRandCard()
                    if card['value'] > g_PrevCard['value'] :
                        break
                    if loop > 10 :
                        break
            else :
                while True :
                    loop += 1
                    card = getRandCard()
                    if card['value'] < g_PrevCard['value'] :
                        break
                    if loop > 10 :
                        break
        else : 
            if high == True :
                while True :
                    loop += 1
                    card = getRandCard()
                    if card['value'] < g_PrevCard['value'] :
                        break
                    if loop > 10 :
                        break
            else :
                while True :
                    loop += 1
                    card = getRandCard()
                    if card['value'] > g_PrevCard['value'] :
                        break
                    if loop > 10 :
                        break
    return card

def getRandCard() -> dict:
    d = dict()
    random.seed(random.randint(1, 1000))
    if len(g_CardHistory) == 0 :
        num = random.randint(4, 10)
    else :
        num = random.randint(1, 13)
    d['value'] = num
    d['label'] = random.choice(g_Flowers) + g_Numbers[num-1]
    return d

async def getWallet(userName : str) -> str:
    walletAddress = "0x1234567890abcdefghijklmnopqrstuvwxyz987"
    return walletAddress

async def getBalance(address : str, token : int) -> float:
    nBalance = 0
    match token:
        case 0: # ETH
            nBalance = 456
        case 1: # BNB
            nBalance = 123
    return nBalance

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
    
def main() -> None:
    """Run the bot."""
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

