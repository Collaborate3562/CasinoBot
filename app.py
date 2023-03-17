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


TOKEN = "6282215563:AAFiWA4Owjxl0n9gfelo2jejlYScz7-UeJI"
g_Greetings = f"/start - Enter the casino\n"
g_Help = f"/help - Describe all guide\n"
g_Wallet = f"/wallet - Show all balances in your wallet\n"
g_Deposit = f"/deposit - Deposit ETH or BNB into your wallet\n"
g_Withdraw = f"/withdraw - Withdraw ETH or BNB from your wallet\n"
g_Hilo = f"/hilo - Play hilo casino game\n"
g_Slot = f"/slot - Play slot casino game\n"

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

CHOOSE, WALLET, SELECT, ROOMTYPE, CHECKIN, SELECTDATE, CHOOSEBOOKINGSOURCE, STATUS, PAYMENT, PARTIAL, DEPOSIT, DISPLAY, CONFIRM, CHECKOUTDATETOCHECK, DATECHECKED, CHECKROOMTYPE, CONFIRMSELECTION, SELECTADJUST, CONFIRMDELETE, VIEWDELETE, REMINDER, SELECTMARK, MARKANDPAY = range(
    23)
# DATECHECKED, CHECKROOMTYPE, DISPLAYCHECKED, CONFIRMSELECTION = range(4)
# DATECHECKED, CHECKROOMTYPE = range(2)
guestinformation = {}
g_Game = 0
def getGame(game):
    sGame = ""
    match game:
        case 1:
            sGames = "Hilo"
        case 2:
            sGames = "Slot"        
    return sGame

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Start the bot and ask what to do when the command /start is issued.
    user = update.effective_user
    userInfo = update.message.from_user
    str_Greetings = f"🙋‍♀️Hi @{userInfo['username']}\nWelcome to Aleekk Casino!\n"
    str_Intro = f"Please enjoy High-Low & Slot machine games here.\n"
    print('You talk with user {} and his user ID: {} '.format(userInfo['username'], userInfo['id']))
    guestinformation = {}
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
    user = update.message.from_user
    address = "0x123456abcd"
    eth_amount = 50
    bnb_amount = 10
    await update.message.reply_text(
        f"{user['username']}'s wallet\nAddress : {address}\nETH : {eth_amount}\nBNB : {bnb_amount}"
    )

async def playHilo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    g_Game = 1
    str_Guide = f"Hilo!🧑‍🤝‍🧑\nWhich token do you wanna bet?\n"
    await eth_bnb_dlg(update, str_Guide)

async def playSlot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    g_Game = 2
    str_Guide = f"Slot!🌺🌺🌺\nWhich token do you wanna bet?\n"
    await eth_bnb_dlg(update, str_Guide)
 
async def betETH(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    n_Balance = 23
    str_Guide = f"How much do you wanna bet?\nCurrent Balance : {n_Balance} ETH\n"
    keyboard = [
        [
            InlineKeyboardButton("Cancel", callback_data="Cancel"),
        ]
    ]
    await query.message.edit_text(
        str_Guide,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
 
async def betBNB(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    n_Balance = 233
    str_Guide = f"How much do you wanna bet?\nCurrent Balance : {n_Balance} BNB\n"
    keyboard = [
        [
            InlineKeyboardButton("Cancel", callback_data="Cancel"),
        ]
    ]
    await query.message.edit_text(
        str_Guide,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
 
async def deposit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    str_Guide = f"💰 Please select token to deposit\n"
    await eth_bnb_dlg(update, str_Guide)

async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    str_Guide = f"💰 Please select token to withdraw\n"
    await eth_bnb_dlg(update, str_Guide)

async def eth_bnb_dlg(update: Update, msg : str) -> int:
    keyboard = [
        [
            InlineKeyboardButton("ETH", callback_data="betETH"),
            InlineKeyboardButton("BNB", callback_data="betBNB"),
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
            CHOOSE: [CallbackQueryHandler(deposit, pattern="Deposit"),
                     CallbackQueryHandler(withdraw, pattern="Withdraw"),
                     CallbackQueryHandler(wallet, pattern="Balance"),
                     CallbackQueryHandler(playHilo, pattern="Play Hilo"),
                     CallbackQueryHandler(playSlot, pattern="Play Slot"),
                     CallbackQueryHandler(_help, pattern="Help")],
            DEPOSIT: [MessageHandler(filters.TEXT, deposit)],
            SELECT: [CallbackQueryHandler(betETH, pattern="betETH"),
                     CallbackQueryHandler(betBNB, pattern="betBNB"),
                     CallbackQueryHandler(cancel, pattern="Cancel")],
        },
        fallbacks=[CommandHandler("end", end)],
        allow_reentry=True,
    )

    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()

