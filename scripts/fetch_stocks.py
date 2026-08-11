import json, datetime, os, time
import yfinance as yf

# TSE = 上市 (.TW on Yahoo Finance)
# OTC = 上櫃 (.TWO on Yahoo Finance)
# 興櫃 stocks (e.g. 7902宇越, 6696仁新) are included under otc but may fail to fetch
STOCKS = {
    'tse': [
        '1612','2059','2303','2316','2327','2329','2330','2356',
        '2385','2397','2408','2423','2454','3017','3026','3042',
        '3167','3324','3528','3711','5483','6213','6669'
    ],
    'otc': [
        '3059','3374','3450','3485','3529','3595','3653',
        '4542','4554','4927','5288','5289','5511',
        '6121','6147','6182','6223','6227','6442','6449',
        '6467','6610','6683','6696','6788','6840',
        '7610','7798','7856','7861','7871','7902',
        '8043','8096','8299','8431','9939'
    ]
}

os.makedirs('data', exist_ok=True)
prices = {}
updated = datetime.datetime.now(datetime.timezone.utc).isoformat()

for ex, codes in STOCKS.items():
    suffix = '.TW' if ex == 'tse' else '.TWO'
    for code in codes:
        ticker_sym = f'{code}{suffix}'
        for attempt in range(3):
            try:
                t = yf.Ticker(ticker_sym)
                hist = t.history(period='2y', interval='1d', auto_adjust=True)
                if hist.empty:
                    raise ValueError('empty dataframe')

                ohlc = []
                for dt, row in hist.iterrows():
                    try:
                        date_str = dt.strftime('%Y-%m-%d')
                        ohlc.append([date_str,
                                     round(float(row['Open']),2),
                                     round(float(row['High']),2),
                                     round(float(row['Low']),2),
                                     round(float(row['Close']),2)])
                    except Exception:
                        pass

                with open(f'data/{code}.json','w') as fh:
                    json.dump({'code':code,'ex':ex,'ohlc':ohlc}, fh, separators=(',',':'))

                if ohlc:
                    prev_close = ohlc[-2][4] if len(ohlc) >= 2 else ohlc[-1][4]
                    last_close = ohlc[-1][4]
                    chg_pct = round((last_close - prev_close) / prev_close * 100, 2) if prev_close else 0
                    prices[code] = {'p': last_close, 'prev': prev_close, 'chgPct': chg_pct}

                print(f'OK {ticker_sym} ({len(ohlc)} bars)')
                break
            except Exception as e:
                print(f'ERR {ticker_sym} attempt {attempt+1}: {e}')
                if attempt < 2:
                    time.sleep(2)

with open('data/prices.json','w') as fh:
    json.dump({'prices': prices, 'updated': updated}, fh, separators=(',',':'))

print(f'Done. {len(prices)} stocks updated.')
