from pycoingecko import CoinGeckoAPI
import asyncio
import threading

from libs.util import (
    updateSetFloatWhereStr,
    readFieldsWhereStr,
    insertInitialCoinInfos,
)

cg = CoinGeckoAPI()

async def get_coin_price():
    print('Fetch Coin Price')
    coinIds = await readFieldsWhereStr('tbl_cryptos', 'CoinId', 'id > 0')

    if len(coinIds) <= 0:
        await insertInitialCoinInfos()
        coinIds = await readFieldsWhereStr('tbl_cryptos', 'CoinId', 'id > 0')
    for coinId in coinIds:
        price = cg.get_price(ids=coinId[0], vs_currencies='usd')
        print(price[coinId[0]]['usd'])
        await updateSetFloatWhereStr('tbl_cryptos', 'Price', price[coinId[0]]['usd'], 'CoinId', coinId[0])
            
def funcInterval():
    asyncio.run(get_coin_price())
 
def setInterval(func:any , sec:int) -> any:
    def func_wrapper():
        setInterval(func, sec)
        func()
    t = threading.Timer(sec, func_wrapper)
    t.start()
    return t

def main() -> None:
    print("Price")
    setInterval(funcInterval, 70)
  
if __name__ == "__main__":
    main()