import json, datetime, os, time
import yfinance as yf

STOCKS = {
    'tse': ['1612','2059','2303','2316','2327','2329','2330','2385','2454','3026','3324'],
    'otc': ['3042','3059','3167','3450','3485','3528','3653','5289','5511','6121','6147','6223','6227','6442','6449','6669','6788','6840','7610','7871','8043','8299','9939']
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
                        o = float(row['Open'])
                        h = float(row['High'])
                        l = float(row['Low'])
                        c = float(row['Close'])
                        v = int(row['Volume']) if 'Volume' in row and row['Volume'] == row['Volume'] else None
                        if o and h and l and c:
                            entry = {'time': date_str, 'open': round(o,2), 'high': round(h,2), 'low': round(l,2), 'close': round(c,2)}
                            if v is not None: entry['volume'] = v
                            ohlc.append(entry)
                    except:
                        pass

                with open(f'data/{code}.json', 'w') as f:
                    json.dump({'updated': updated, 'data': ohlc}, f, separators=(',',':'))

                info = t.fast_info
                p    = round(float(info.last_price or 0), 2)
                prev = round(float(info.previous_close or 0), 2)
                chg  = round((p - prev) / prev * 100, 2) if prev > 0 else 0
                prices[code] = {'p': p, 'prev': prev, 'chgPct': chg}
                print(f'OK {ticker_sym}: {p} ({chg:+.2f}%) [{len(ohlc)} bars]')
                time.sleep(0.5)
                break
            except Exception as e:
                print(f'RETRY {attempt+1} {ticker_sym}: {e}')
                time.sleep(3)

with open('data/prices.json', 'w') as f:
    json.dump({'updated': updated, 'prices': prices}, f, separators=(',',':'))

print(f'\nDone: {len(prices)}/{sum(len(v) for v in STOCKS.values())} stocks updated')
