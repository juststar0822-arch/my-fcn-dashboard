import csv
import json
import time
from pathlib import Path

import yfinance as yf

ROOT = Path(__file__).resolve().parent
CSV_FILE = ROOT / "data.csv"
PRICE_FILE = ROOT / "prices.json"


def get_symbols():
    symbols = set()

    if not CSV_FILE.exists():
        print("找不到 data.csv")
        return []

    with open(CSV_FILE, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        for row in reader:
            for i in range(1, 6):
                code = row.get(f"s{i}_code", "")
                code = code.strip().upper()

                if code:
                    symbols.add(code)

    return sorted(symbols)


def get_prices():
    if PRICE_FILE.exists():
        with open(PRICE_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                pass

    return {
        "updated": 0,
        "prices": {}
    }


def update_prices():
    symbols = get_symbols()
    data = get_prices()

    if not isinstance(data.get("prices"), dict):
        data["prices"] = {}

    if not symbols:
        print("沒有股票代號，略過更新")
        return

    success = 0

    for symbol in symbols:
        try:
            print(f"正在更新：{symbol}")

            stock = yf.Ticker(symbol)

            history = stock.history(
                period="2y",
                interval="1d",
                auto_adjust=False
            )

            if history.empty:
                print(f"找不到報價：{symbol}")
                continue

            history = history.dropna(subset=["Close"])

            timestamps = [
                int(t.timestamp())
                for t in history.index
            ]

            closes = [
                round(float(v), 5)
                for v in history["Close"]
            ]

            highs = [
                round(float(v), 5)
                if v == v else None
                for v in history["High"]
            ]

            lows = [
                round(float(v), 5)
                if v == v else None
                for v in history["Low"]
            ]

            data["prices"][symbol] = {
                "current": closes[-1],
                "timestamp": timestamps,
                "high": highs,
                "low": lows,
                "close": closes
            }

            success += 1
            print(f"{symbol} 更新成功：{closes[-1]}")

        except Exception as e:
            print(f"{symbol} 更新失敗：{e}")

    if success == 0:
        raise RuntimeError("所有股票報價更新失敗")

    data["updated"] = int(time.time())

    with open(PRICE_FILE, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2,
            allow_nan=False
        )

    print(f"更新完成，共 {success} 檔股票")


if __name__ == "__main__":
    update_prices()