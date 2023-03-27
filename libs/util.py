import random

from libs.db import (
    updateSetStrWhereStr,
    updateSetFloatWhereStr,
    readFieldsWhereStr,
    insertFields
)
import datetime
from dotenv.main import load_dotenv
import os

load_dotenv()

OWNER_ADDRESS = os.environ['OWNER_ADDRSS']
OWNER_PRIVATE_KEY = os.environ['OWNER_PRIVATE_KEY']

g_Flowers = ['♠️', '♥️', '♣️', '♦️']
g_Numbers = ['A','2','3','4','5','6','7','8','9','10','J','Q','K']

async def getPricefromAmount(amount : float, kind : int) -> str:
    price = 0
    if kind == 0 :
        price = amount * 1700
    else :
        price = amount * 300
    return f" (${price})"

def roll() -> dict:
    slot = dict()
    num1 = random.randint(0, 4)
    num2 = random.randint(0, 4)
    num3 = random.randint(0, 4)
    if num1 == num2 and num2 == num3 :
        slot["value"] = True
    else :
        slot["value"] = False
    label = _getCell(num1) + " | " + _getCell(num2) + " | " + _getCell(num3)
    num = str(num1) + str(num2) + str(num3)
    slot["label"] = label
    slot["num"] = num
    return slot

def getUnitString(kind: int) -> str:
    str = ""
    if kind == 0 :
        str = "ETH"
    else :
        str = "BNB"
    return str

def controlRandCard(high : bool, CardHistory : str, PrevCard : dict) -> dict:
    card = None
    loop = 0
    if PrevCard == None or PrevCard['value'] == 1 or PrevCard['value'] == 13:
        print("Starting control")
        card = _getRandCard(CardHistory)
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
                    card = _getRandCard(CardHistory)
                    if card['value'] > PrevCard['value'] :
                        break
                    if loop > 10 :
                        break
            else :
                while True :
                    loop += 1
                    card = _getRandCard(CardHistory)
                    if card['value'] < PrevCard['value'] :
                        break
                    if loop > 10 :
                        break
        else : 
            if high == True :
                while True :
                    loop += 1
                    card = _getRandCard(CardHistory)
                    if card['value'] < PrevCard['value'] :
                        break
                    if loop > 10 :
                        break
            else :
                while True :
                    loop += 1
                    card = _getRandCard(CardHistory)
                    if card['value'] > PrevCard['value'] :
                        break
                    if loop > 10 :
                        break
    return card

async def getWallet(userId: str, userName: str, fullName: str, isBot: bool, ethContract: any) -> str:
    kind = "RealName=\"{}\" AND UserName=\"{}\" AND UserID=\"{}\"".format(fullName, userName, userId)
    wallet = await readFieldsWhereStr('tbl_users', 'Wallet', kind)

    # if wallet field is empty, estimate wallet address by salt
    if len(wallet) < 1:
        bytecode = ethContract.functions.getBytecode(OWNER_ADDRESS).call()
        wallet = ethContract.functions.getAddress(bytecode, int(userId)).call()
        field = {
            "RealName": fullName,
            "UserName": userName,
            "UserID": userId,
            "Wallet": wallet,
            "UserAllowed": isBot,
            "JoinDate": datetime.datetime.now()
        }
        
        await insertFields('tbl_users', field)

    return wallet[0][0]

async def getBalance(address: str, web3: any, userId: str) -> float:
    nBalance = 0
    
    chain_id = web3.eth.chain_id
    
    kind = "UserID=\"{}\"".format(userId)
    if chain_id == 5:
        balance = await readFieldsWhereStr('tbl_users', 'ETH_Amount', kind)
    else:
        balance = await readFieldsWhereStr('tbl_users', 'BNB_Amount', kind)

    onChainBalane = web3.eth.getBalance(address)
    if onChainBalane > 0:
        updateSetFloatWhereStr("tbl_Users", "ReadyTransfer", True, "UserID", userId)

    nBalance = balance[0][0]

    return nBalance

def _getRandCard(CardHistory : str) -> dict:
    d = dict()
    random.seed(random.randint(1, 1000))
    if len(CardHistory) == 0 :
        num = random.randint(4, 10)
    else :
        num = random.randint(1, 13)
    d['value'] = num
    d['label'] = random.choice(g_Flowers) + g_Numbers[num-1]
    return d

def _getCell(num : int) -> str:
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
