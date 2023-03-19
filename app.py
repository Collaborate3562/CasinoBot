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
from telegram import ForceReply, ReplyKeyboardRemove, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
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
g_PrevCard = None
g_NextCard = None
g_CardHistory = ""
# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

CHOOSE, WALLET, SELECT, STATUS, PAYMENT, DEPOSIT, DISPLAY, PANELHILO, PANELSLOT, BETTINGHILO = range(10)
ST_DEPOSIT, ST_WITHDRAW, ST_HILO, ST_SLOT = range(4)
ETH, BNB = range(2)
guestinformation = {}
g_STATUS = 0

def getGame(status):
    sGame = ""
    match status:
        case 0:
            sGames = "Deposit"
        case 1:
            sGames = "Withdraw"
        case 2:
            sGames = "Hilo"
        case 3:
            sGames = "Slot"        
    return sGame

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

async def wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
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

async def playHilo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    init()
    global g_STATUS
    g_STATUS = ST_HILO
    str_Guide = f"Hilo!🧑‍🤝‍🧑\nWhich token do you wanna bet?\n"
    return await eth_bnb_dlg(update, str_Guide)

async def _playHilo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    init()
    global g_STATUS
    g_STATUS = ST_HILO
    str_Guide = f"Hilo!🧑‍🤝‍🧑\nWhich token do you wanna bet?\n"
    return await _eth_bnb_dlg(update, str_Guide)

async def playSlot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    init()
    global g_STATUS
    g_STATUS = ST_SLOT
    str_Guide = f"Slot!🌺🌺🌺\nWhich token do you wanna bet?\n"
    return await eth_bnb_dlg(update, str_Guide)
 
async def _playSlot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    init()
    global g_STATUS
    g_STATUS = ST_SLOT
    str_Guide = f"Slot!🌺🌺🌺\nWhich token do you wanna bet?\n"
    return await _eth_bnb_dlg(update, str_Guide)
 
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

async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    global g_STATUS
    g_STATUS = ST_WITHDRAW
    str_Guide = f"💰 Please select token to withdraw\n"
    return await eth_bnb_dlg(update, str_Guide)

async def _withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    global g_STATUS
    g_STATUS = ST_WITHDRAW
    str_Guide = f"💰 Please select token to withdraw\n"
    return await _eth_bnb_dlg(update, str_Guide)

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
 
async def funcETH(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    address = await getWallet(UserName)
    n_Balance = await getBalance(address, ETH)
    str_Guide = f"How much do you wanna bet?\nCurrent Balance : {n_Balance} ETH\n"
    return await confirm_dlg(update, str_Guide)
 
async def funcBNB(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    address = await getWallet(UserName)
    n_Balance = await getBalance(address, BNB)
    str_Guide = f"How much do you wanna bet?\nCurrent Balance : {n_Balance} BNB\n"
    return await confirm_dlg(update, str_Guide)

async def confirm_dlg(update: Update, msg : str) -> int:
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
    match g_STATUS:
        case 0: #ST_DEPOSIT
            return PANELHILO #TODO
        case 1: #ST_WITHDRAW
            return PANELHILO #TODO
        case 2: #ST_HILO
            return PANELHILO
        case 3: #ST_SLOT
            return PANELSLOT

async def panelHilo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    global g_PrevCard
    keyboard = []
    newCard = g_NextCard #For initialize
    sGreeting = ""
    if g_Cashout > 0 :
        sGreeting = f"You Win!\n{g_CardHistory}Cashout : x{g_Cashout}\n"
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
        query = update.callback_query
        await query.message.edit_text(
            f"{sGreeting}Card   :   {str(newCard['label'])}\nWhat is your next guessing? H or L?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return BETTINGHILO
    else :
        betAmount = float(update.message.text)
        print(betAmount)
        sGreeting = "Enjoy!\n"
        newCard = getRandCard()
        g_PrevCard = newCard
        keyboard = [
            [
                InlineKeyboardButton("High", callback_data="High"),
                InlineKeyboardButton("Low", callback_data="Low"),
            ]
        ]
        await update.message.reply_text(
            f"{sGreeting}Card   :   {str(newCard['label'])}\nWhat is your next guessing? H or L?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return BETTINGHILO

async def _high(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    global g_Cashout
    global g_NextCard
    global g_CardHistory
    g_CardHistory = g_CardHistory + g_PrevCard['label'] + "\n"
    card = getRandCard()
    print(card)
    if card['value'] > g_PrevCard['value']:
        print("High=>TRUE")
        g_Cashout += 1 
        g_NextCard = card
        return await panelHilo(update, context)
    else :
        print("High=>FALSE")
        sCardHistory = g_CardHistory
        init()
        g_Cashout = 0
        query = update.callback_query
        await query.message.edit_text(
            f"{sCardHistory}😢😢😢\n{card['label']}\nYou Lose!\n/start /hilo"
        )

async def _low(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    global g_Cashout
    global g_NextCard
    global g_CardHistory
    card = getRandCard()
    g_CardHistory = g_CardHistory + g_PrevCard['label'] + "\n"
    print(card)
    if card['value'] < g_PrevCard['value']:
        print("LOW=>TRUE")
        g_NextCard = card
        g_Cashout += 1 
        await panelHilo(update, context)
    else :
        print("LOW=>FALSE")
        g_Cashout = 0
        sCardHistory = g_CardHistory
        init()
        query = update.callback_query
        await query.message.edit_text(
            f"{sCardHistory}😢😢😢\n{card['label']}\nYou Lose!\n/start /hilo"
        )

async def _cashoutHilo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.message.edit_text(
        f"🏆🏆🏆\nYou win!\nProfit : x{g_Cashout}\n/start /hilo"
    )
    
async def panelSlot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    slot = roll()
    label = slot["label"]
    res = ""
    if slot["value"] == True:
        res = "Win!"
    else :
        res = "Lose!"
    await update.message.reply_text(
        f"{label}\nYou {res}/start /slot"
    )

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        g_Greetings + g_Help + g_Wallet + g_Deposit + g_Withdraw + g_Hilo + g_Slot
    )
 
async def _help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.message.edit_text(
        g_Greetings + g_Help + g_Wallet + g_Deposit + g_Withdraw + g_Hilo + g_Slot
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
    global g_CardHistory;   g_CardHistory = ""
    global g_Cashout;       g_Cashout = 0
    global g_NextCard;      g_NextCard = None
    global g_PrevCard;      g_PrevCard = None

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
    label = getCell(num1) + getCell(num2) + getCell(num3)
    num = str(num1) + str(num2) + str(num3)
    slot["label"] = label
    slot["num"] = num
    return slot

def getRandCard() -> dict:
    d = dict()
    num = random.randint(1, 13)
    d['value'] = num
    d['label'] = random.choice(g_Flowers) + g_Numbers[num-1]
    return d

async def getWallet(userName : str) -> str:
    walletAddress = "0x1234567890abcdefghijklmnopqrstuvwxyz987"
    return walletAddress

async def getBalance(address : str, token : int) -> int:
    nBalance = 0
    match token:
        case 0: # ETH
            nBalance = 456
        case 1: # BNB
            nBalance = 123
    return nBalance

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
            SELECT: [CallbackQueryHandler(funcETH, pattern="funcETH"),
                     CallbackQueryHandler(funcBNB, pattern="funcBNB"),
                     CallbackQueryHandler(cancel, pattern="Cancel")],
            PANELHILO: [MessageHandler(filters.TEXT, panelHilo)],
            PANELSLOT: [MessageHandler(filters.TEXT, panelSlot)],
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

