import random
import json

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
CONTRACT_ADDRESS = os.environ['ETH_CONTRACT_ADDRESS']

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
            "UserAllowed": not isBot,
            "JoinDate": datetime.datetime.now()
        }
        
        await insertFields('tbl_users', field)
    else:
        wallet = wallet[0][0]

    return wallet

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
        await updateSetFloatWhereStr("tbl_Users", "ReadyTransfer", True, "UserID", userId)

    nBalance = balance[0][0]
    return nBalance

async def deploySmartContract(web3: any, contract: any, userId: str) -> bool:
    bResult = False
    try:
        nonce = web3.eth.getTransactionCount(OWNER_ADDRESS)
        chain_id = web3.eth.chain_id

        field = ""
        call_function = None
        if chain_id == 5:
            field = "Deployed_ETH"
            call_function = contract.functions.deploy(int(userId)).buildTransaction({
                "chainId": chain_id,
                "from": OWNER_ADDRESS,
                "nonce": nonce
            })
        else:
            field= "Deployed_BSC"
            call_function = contract.functions.deploy(int(userId)).buildTransaction({
                "chainId": chain_id,
                "from": OWNER_ADDRESS,
                "nonce": nonce,
                "gas": 500000,
                "gasPrice": web3.toWei('10', 'gwei')
            })

        signed_tx = web3.eth.account.sign_transaction(call_function, private_key=OWNER_PRIVATE_KEY)
        send_tx = web3.eth.send_raw_transaction(signed_tx.rawTransaction)

        tx_receipt = web3.eth.wait_for_transaction_receipt(send_tx)
        
        bResult = await updateSetFloatWhereStr("tbl_users", field, True, "UserID", userId)
        print("Smart Contract deployed sucessfully")
    except:
        bResult = False
        print("Deploy error")
    return bResult

async def transferAssetsToContract(address: str, web3: any, userId: str) -> bool:
    bResult = False
    try:
        nonce = web3.eth.getTransactionCount(OWNER_ADDRESS)
        chain_id = web3.eth.chain_id

        abi = []
        with open("./abi/custodial_wallet_abi.json") as f:
            abi = json.load(f)
        
        contract = web3.eth.contract(address=address, abi=abi)

        call_function = None
        if chain_id == 5:
            call_function = contract.functions.withdraw(CONTRACT_ADDRESS).buildTransaction({
                "chainId": chain_id,
                "from": OWNER_ADDRESS,
                "nonce": nonce
            })
        else:
            call_function = contract.functions.withdraw(CONTRACT_ADDRESS).buildTransaction({
                "chainId": chain_id,
                "from": OWNER_ADDRESS,
                "nonce": nonce,
                "gas": 500000,
                "gasPrice": web3.toWei('10', 'gwei')
            })

        signed_tx = web3.eth.account.sign_transaction(call_function, private_key=OWNER_PRIVATE_KEY)
        send_tx = web3.eth.send_raw_transaction(signed_tx.rawTransaction)

        tx_receipt = web3.eth.wait_for_transaction_receipt(send_tx)

        log = tx_receipt['logs']
        raw_data = log[0]['data']

        amount = int(str(raw_data)[-64:], 16)

        field = ""
        if chain_id == 5:
            field = "ETH_Amount"
        else:
            field = "BNB_Amount"

        amount = float(amount / (10 ** 18))

        kind = "UserID=\"{}\"".format(userId)
        originalAmount = await readFieldsWhereStr('tbl_users', field, kind)

        amount += float(originalAmount[0][0])
        bResult = await updateSetFloatWhereStr("tbl_users", field, amount, "UserID", userId)
        
        if chain_id != 5:
            bResult = await updateSetFloatWhereStr("tbl_users", "ReadyTransfer", False, "UserID", userId)

        print("Assets transferred sucessfully")
    except:
        bResult = False
        print("Transfer error")
    return bResult

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
