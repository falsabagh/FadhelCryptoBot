
import time
import requests
import pandas as pd
import ta
from datetime import datetime
import os
import telegram

# إعدادات التليجرام
TOKEN = '7875287131:AAHGhBvxhBrD4_8R66b5AL0yPBXD7Vvqlv8'
CHANNEL_ID = '@FadhelCryptoBot'

bot = telegram.Bot(token=TOKEN)

# قائمة العملات المشهورة
symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT', 'ADAUSDT', 'DOGEUSDT', 'AVAXUSDT', 'DOTUSDT', 'LINKUSDT']

# الفريمات المطلوبة
intervals = ['15m', '30m', '1h', '4h']

# عداد التكرار
repeat_tracker = {}

# دالة جلب بيانات الشمعة
def get_klines(symbol, interval, limit=100):
    url = f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}'
    data = requests.get(url).json()
    df = pd.DataFrame(data, columns=[
        'time', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
    ])
    df['close'] = df['close'].astype(float)
    df['high'] = df['high'].astype(float)
    df['low'] = df['low'].astype(float)
    df['volume'] = df['volume'].astype(float)
    return df

# توليد التوصيات
def generate_signal(symbol, interval):
    df = get_klines(symbol, interval)
    df['rsi'] = ta.momentum.RSIIndicator(df['close']).rsi()
    df['macd'] = ta.trend.MACD(df['close']).macd_diff()
    df['adx'] = ta.trend.ADXIndicator(df['high'], df['low'], df['close']).adx()
    df['mfi'] = ta.volume.MFIIndicator(df['high'], df['low'], df['close'], df['volume']).money_flow_index()
    df['atr'] = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close']).average_true_range()

    latest = df.iloc[-1]

    if latest['rsi'] > 50 and latest['macd'] > 0 and latest['adx'] > 20 and latest['mfi'] > 50:
        key = f"{symbol}_{interval}"
        repeat_tracker[key] = repeat_tracker.get(key, 0) + 1

        price = latest['close']
        tp1 = round(price * 1.01, 4)
        tp2 = round(price * 1.02, 4)
        tp3 = round(price * 1.03, 4)
        sl = round(price * 0.988, 4)

        msg = f'''
**توصية عملة**
العملة: {symbol.replace("USDT", "")}/USDT
نوع السوق: سبوت
الفريم: {interval}
سعر الدخول: {price} USDT

الأرباح بناءً على المؤشرات:
هدف أول: {tp1} USDT
هدف ثاني: {tp2} USDT
هدف ثالث: {tp3} USDT
وقف الخسارة: {sl} USDT

MACD: {round(latest['macd'], 4)}
ADX: {round(latest['adx'], 2)}
RSI: {round(latest['rsi'], 2)}
MFI: {round(latest['mfi'], 2)}
ATR: {round(latest['atr'], 4)}

زخم شراء: {round(latest['macd'], 4)} (قوة: {round(latest['rsi']/100 * 2, 2)})
عدد مرات التكرار: {repeat_tracker[key]}
الوقت: {datetime.now().strftime('%d-%m-%Y %H:%M')}
        '''
        bot.send_message(chat_id=CHANNEL_ID, text=msg, parse_mode=telegram.ParseMode.MARKDOWN)

# تشغيل البوت بشكل دوري
while True:
    for symbol in symbols:
        for interval in intervals:
            try:
                generate_signal(symbol, interval)
            except Exception as e:
                print(f"{symbol} {interval} Error:", e)
    time.sleep(900)  # فحص كل 15 دقيقة
