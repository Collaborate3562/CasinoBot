import random
import json
import threading
import sys
import re
import requests
#******For Test********#
# from db import (
from libs.db import (
    updateSetStrWhereStr,
    updateSetFloatWhereStr,
    readFieldsWhereStr,
    getTopFieldsByLimit,
    insertInitialCoinInfos,
    insertFields
)
from urllib.request import urlopen
from urllib.error import URLError
import datetime
from dotenv.main import load_dotenv
import os

load_dotenv()   

OWNER_ADDRESS = os.environ['OWNER_ADDRSS']
OWNER_PRIVATE_KEY = os.environ['OWNER_PRIVATE_KEY']
CONTRACT_ADDRESS = os.environ['ETH_CONTRACT_ADDRESS']
ETH_TESTNET_ID = os.environ['ETH_TESTNET_ID']
ETH_MAINNET_ID = os.environ['ETH_MAINNET_ID']

HOUSE_CUT_FEE = 50
PERCENTAGE = 1000

ETH_FIXED_WITHDRAW_FEE = float(1)
BSC_FIXED_WITHDRAW_FEE = float(0.3)

g_Flowers = ['♠️', '♥️', '♣️', '♦️']
g_Numbers = ['A','2','3','4','5','6','7','8','9','10','J','Q','K']
g_SlotCashOut = [18.0, 3.0, 1.3, 1.05]
g_CntSymbol = 6

async def getPricefromAmount(amount : float, kind : int) -> float:
    value = 0
    if kind == 0 :
        price = await readFieldsWhereStr('tbl_cryptos', 'Price', 'Symbol=\'eth\'')
        price = price[0][0]
        value = amount * price
    else :
        price = await readFieldsWhereStr('tbl_cryptos', 'Price', 'Symbol=\'bnb\'')
        price = price[0][0]
        value = amount * price
    return value

def isValidAddress(w3: any, address: str) -> bool:
    return w3.isAddress(address)

def isValidContractOrWallet(w3: any, address: str) -> bool:
    return isValidAddress(w3, address) and (len(address) == 42 or len(address) == 40)

def isFloat(amount: str) -> bool:
    try:
        float(amount)
        return True
    except ValueError:
        return False

def truncDecimal(value: float, dec: int = 2) -> str:
    return '{:.2f}'.format(value)

def truncDecimal7(value: float) -> str:
    trimStr = '{:.7f}'.format(value)
    return trimStr.rstrip('0').rstrip('.')

def isValidUrl(url) -> bool:
    res = True

    httpsPattern = re.compile(r'^https?://\S+$')
    isHttps = bool(httpsPattern.match(url))

    httpPattern = re.compile(r'^http?://\S+$')
    isHttp = bool(httpPattern.match(url))

    res = isHttps or isHttp

    return res

def isOpenedUrl(url) -> bool:
    try:
        response = requests.get(url)
        response.raise_for_status()
        return True
    except requests.exceptions.HTTPError as e:
        print("HTTP error occurred: ", e)
        print("Status code:", response.status_code)
        print("Reason:", response.reason)
        return True
    except requests.exceptions.ConnectionError as e:
        print("Error connecting: ", e)
        return False
    except requests.exceptions.Timeout as e:
        print("Timeout error: ", e)
        return False
    except requests.exceptions.RequestException as e:
        print("An error occurred: ", e)
        return False

def roll() -> dict:
    slot = dict()
    end = g_CntSymbol - 1
    num1 = random.randint(0, end)
    num2 = random.randint(0, end)
    num3 = random.randint(0, end)
    rate = _winningRate(num1, num2, num3)
    slot["value"] = rate["value"]
    slot["cashout"] = rate["cashout"]
    slot["kind"] = rate["Kind"]
    label = _getCell(num1) + " | " + _getCell(num2) + " | " + _getCell(num3)
    num = str(num1) + str(num2) + str(num3)
    slot["label"] = label
    slot["num"] = num
    return slot

def _winningRate(num1:int, num2:int, num3:int) -> dict:
    res = dict()
    res["value"] = False
    if num1 == num2 == num3 == 3:
        res["cashout"] = g_SlotCashOut[0]
        res["value"] = True
        res["Kind"] = 0
    elif num1 == num2 == num3:
        res["cashout"] = g_SlotCashOut[1]
        res["value"] = True
        res["Kind"] = 1
    elif num1 == num2 == 3 or num1 == num3 == 3 or num2 == num3 == 3:
        res["cashout"] = g_SlotCashOut[2]
        res["value"] = True
        res["Kind"] = 2
    elif num1 == 3 or num2 == 3 or num3 == 3:
        res["cashout"] = g_SlotCashOut[3]
        res["value"] = True
        res["Kind"] = 3
    else:
        res["cashout"] = 0
        res["Kind"] = 4
    return res

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
    kind = "UserName=\"{}\" AND UserID=\"{}\"".format(userName, userId)
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
    
    balance = None
    kind = "UserID=\"{}\"".format(userId)
    if chain_id == int(ETH_TESTNET_ID):
        balance = await readFieldsWhereStr('tbl_users', 'ETH_Amount', kind)
    else:
        balance = await readFieldsWhereStr('tbl_users', 'BNB_Amount', kind)

    nBalance = balance[0][0]
    return nBalance

async def deploySmartContract(web3: any, contract: any, userId: str) -> bool:
    bResult = False
    try:
        nonce = web3.eth.getTransactionCount(OWNER_ADDRESS)
        chain_id = web3.eth.chain_id

        field = ""
        call_function = None
        if chain_id == int(ETH_TESTNET_ID):
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
        if chain_id == int(ETH_TESTNET_ID):
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
                "gas": 1000000,
                "gasPrice": web3.toWei('10', 'gwei')
            })

        signed_tx = web3.eth.account.sign_transaction(call_function, private_key=OWNER_PRIVATE_KEY)
        send_tx = web3.eth.send_raw_transaction(signed_tx.rawTransaction)

        tx_receipt = web3.eth.wait_for_transaction_receipt(send_tx)

        log = tx_receipt['logs']
        raw_data = log[0]['data']

        amount = int(str(raw_data)[-64:], 16)

        field = ""
        if chain_id == int(ETH_TESTNET_ID):
            field = "ETH_Amount"
        else:
            field = "BNB_Amount"

        amount = float(amount / (10 ** 18))

        kind = "UserID=\"{}\"".format(userId)
        originalAmount = await readFieldsWhereStr('tbl_users', field, kind)

        amount += float(originalAmount[0][0])
        bResult = await updateSetFloatWhereStr("tbl_users", field, amount, "UserID", userId)

        print("Assets transferred sucessfully")
    except:
        bResult = False
        print("Transfer error")
    return bResult

async def withdrawAmount(web3: any, contract: any, withdrawalAddress: str, amount: float, userId: str) -> dict:
    res = {}
    try:
        nonce = web3.eth.getTransactionCount(OWNER_ADDRESS)
        chain_id = web3.eth.chain_id

        call_function = None
        field = ""

        fee = await calculateTotalWithdrawFee(web3, amount)
        if chain_id == int(ETH_TESTNET_ID):
            call_function = contract.functions.withdraw(withdrawalAddress, web3.toWei(amount - fee, 'ether')).buildTransaction({
                "chainId": chain_id,
                "from": OWNER_ADDRESS,
                "nonce": nonce
            })
            field = "ETH_Amount"
        else:
            call_function = contract.functions.withdraw(withdrawalAddress, web3.toWei(amount - fee, 'ether')).buildTransaction({
                "chainId": chain_id,
                "from": OWNER_ADDRESS,
                "nonce": nonce,
                "gas": 1000000,
                "gasPrice": web3.toWei('10', 'gwei')
            })
            field = "BNB_Amount"
        
        signed_tx = web3.eth.account.sign_transaction(call_function, private_key=OWNER_PRIVATE_KEY)
        send_tx = web3.eth.send_raw_transaction(signed_tx.rawTransaction)

        tx_receipt = web3.eth.wait_for_transaction_receipt(send_tx)

        kind = "UserID=\"{}\"".format(userId)
        originalAmount = await readFieldsWhereStr('tbl_users', field, kind)

        amount = float(originalAmount[0][0]) - amount

        bResult = await updateSetFloatWhereStr("tbl_users", field, amount, "UserID", userId)

        res = tx_receipt
    except:
        print("withdraw error")
        return res
    return res

async def calculateTotalWithdrawFee(web3: any, amount: float) -> float:
    res = float(0)
    try:
        withdrawalFee = await calculateFixedFee(web3)

        fee = (amount * HOUSE_CUT_FEE / PERCENTAGE) + withdrawalFee
        feeStr = '{:.5f}'.format(fee).rstrip('0')
        
        res = float(feeStr)
    except:
        print("Calculate fee error")
        return res
    return res

async def calculateFixedFee(web3: any) -> float:
    res = float(0)
    try:
        price = 0
        chain_id = web3.eth.chain_id
        if chain_id == int(ETH_TESTNET_ID):
            price = await readFieldsWhereStr('tbl_cryptos', 'Price', 'Symbol=\'eth\'')
            price = price[0][0]

            res = ETH_FIXED_WITHDRAW_FEE / float(price)
        else:
            price = await readFieldsWhereStr('tbl_cryptos', 'Price', 'Symbol=\'bnb\'')
            price = price[0][0]

            res = BSC_FIXED_WITHDRAW_FEE / float(price)

        feeStr = '{:.5f}'.format(res).rstrip('0')
        
        res = float(feeStr)
    except:
        print("Calculate Fixed fee error")
        return res
    return res

async def getTokenPrice(tokenMode: int) -> float:
    res = float(0)
    try:
        if tokenMode == 0:
            price = await readFieldsWhereStr('tbl_cryptos', 'Price', 'Symbol=\'eth\'')
            res = float(price[0][0])
        else:
            price = await readFieldsWhereStr('tbl_cryptos', 'Price', 'Symbol=\'bnb\'')
            res = float(price[0][0])

    except:
        print("Get Token Price error")
        return res
    return res

async def calculateCryptoAmountByUSD(amount: float, tokenMode: int) -> float:
    res = float(0)
    try:
        tokenPrice = await getTokenPrice(tokenMode)
        cryptoAmount = amount / tokenPrice
        res = '{:.5f}'.format(cryptoAmount).rstrip('0').rstrip('.')
        res = float(res)

    except:
        print("Calculate Crypto amount by USD amount error")
        return res
    return res

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
        case 5:
            cell="🍒"
        case 6:
            cell="🍄"
    return cell


#******For Test********#
g_True = 0
g_False = 0
g_TotalUserWin = 0.0
g_TotalHouseWin = 0.0
g_Count = 0
g_777 = 0
g_3Card = 0
g_77 = 0
g_7 = 0
def funcInterval():
    global g_True, g_False, g_TotalUserWin, g_TotalHouseWin, g_Count
    global g_777, g_3Card, g_77, g_7
    slot = roll()
    kind = slot["kind"]
    match kind:
        case 0:
            g_777 += 1
        case 1:
            g_3Card += 1
        case 2:
            g_77 += 1
        case 3:
            g_7 += 1

    if slot["value"] == True:
        g_True += 1
        g_TotalUserWin += slot["cashout"]
    else :
        g_False += 1
        g_TotalHouseWin += 1
    g_Count += 1

    if g_Count % 20 == 0 :
        print(slot)
        print(f"Count : {g_Count}, House Win : {g_False}, House Earn : <x{g_TotalHouseWin}>, UserWin : {g_True}, UserCashout : <x{g_TotalUserWin}>")
        print(f"777 : {g_777}(x{g_777*g_SlotCashOut[0]}), 3-Card : {g_3Card}(x{g_3Card*g_SlotCashOut[1]}), 77 : {g_77}(x{g_77*g_SlotCashOut[2]}), One7 : {g_7}(x{g_7*g_SlotCashOut[3]})\n")
    if g_Count >= 1000:
        sys.exit()


def setInterval(func:any , sec:int) -> any:
    def func_wrapper():
        setInterval(func, sec)
        func()
    t = threading.Timer(sec, func_wrapper)
    t.start()
    return t

def main() -> None:
    setInterval(funcInterval, 0.1)
  
if __name__ == "__main__":
    main()