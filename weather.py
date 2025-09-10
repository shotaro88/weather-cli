#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Simple Weather CLI using Open-Meteo (no API key needed)

Usage:
  python weather.py --city Tokyo --days 3 --lang ja
  python weather.py --city "Osaka" --days 5 --tz Asia/Tokyo
"""

from __future__ import annotations
import argparse
import datetime as dt
import json
import sys
import textwrap
import urllib.parse
import urllib.request


GEO_BASE = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_BASE = "https://api.open-meteo.com/v1/forecast"

# Minimal mapping for Open-Meteo weather codes
WEATHER_CODE_MAP_JA = {
    0: "快晴",
    1: "ほぼ快晴",
    2: "晴れ時々くもり",
    3: "くもり",
    45: "霧",
    48: "着氷性霧",
    51: "霧雨(弱)",
    53: "霧雨(中)",
    55: "霧雨(強)",
    56: "着氷性霧雨(弱)",
    57: "着氷性霧雨(強)",
    61: "雨(弱)",
    63: "雨(中)",
    65: "雨(強)",
    66: "着氷性雨(弱)",
    67: "着氷性雨(強)",
    71: "雪(弱)",
    73: "雪(中)",
    75: "雪(強)",
    77: "雪あられ",
    80: "にわか雨(弱)",
    81: "にわか雨(中)",
    82: "にわか雨(強)",
    85: "にわか雪(弱)",
    86: "にわか雪(強)",
    95: "雷雨",
    96: "雷雨(弱いひょう)",
    99: "雷雨(強いひょう)",
}

def http_get(url: str, params: dict[str, str] | None = None) -> dict:
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": "weather-cli/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        if resp.status != 200:
            raise RuntimeError(f"HTTP {resp.status} for {url}")
        return json.loads(resp.read().decode("utf-8"))

def geocode(city: str, lang: str = "ja", count: int = 1) -> dict:
    data = http_get(
        GEO_BASE,
        {"name": city, "count": str(count), "language": lang, "format": "json"},
    )
    results = data.get("results") or []
    if not results:
        raise ValueError(f"場所が見つかりませんでした: {city}")
    return results[0]  # 最も一致度が高いもの

def fetch_forecast(lat: float, lon: float, days: int, tz: str) -> dict:
    daily_params = ",".join([
        "weather_code",
        "temperature_2m_max",
        "temperature_2m_min",
        "precipitation_probability_max",
    ])
    data = http_get(
        FORECAST_BASE,
        {
            "latitude": f"{lat:.5f}",
            "longitude": f"{lon:.5f}",
            "timezone": tz,
            "forecast_days": str(days),
            "daily": daily_params,
        },
    )
    if "daily" not in data:
        raise RuntimeError("予報データの取得に失敗しました。")
    return data

def fmt_table(rows: list[list[str]], headers: list[str]) -> str:
    # シンプルな固定幅テーブル整形
    cols = list(zip(*([headers] + rows)))
    widths = [max(len(str(x)) for x in col) for col in cols]
    def line(parts): return " | ".join(str(p).ljust(w) for p, w in zip(parts, widths))
    sep = "-+-".join("-" * w for w in widths)
    out = [line(headers), sep]
    out += [line(r) for r in rows]
    return "\n".join(out)

def main():
    parser = argparse.ArgumentParser(
        description="Open-Meteo を使って都市名から日次天気予報を表示します。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
            例:
              python weather.py --city Tokyo --days 3
              python weather.py --city 札幌 --days 5 --tz Asia/Tokyo
        """),
    )
    parser.add_argument("--city", required=True, help="都市名（例: Tokyo, 大阪, 札幌）")
    parser.add_argument("--days", type=int, default=3, help="取得日数（1-16 推奨）")
    parser.add_argument("--lang", default="ja", help="ジオコーディングの言語（デフォルト: ja）")
    parser.add_argument("--tz", default="Asia/Tokyo", help="タイムゾーン（例: Asia/Tokyo）")
    args = parser.parse_args()

    try:
        g = geocode(args.city, lang=args.lang)
        lat, lon = float(g["latitude"]), float(g["longitude"])
        city_label = f'{g.get("name")} ({g.get("country_code")})'
        if g.get("admin1"):
            city_label = f'{g.get("name")}, {g.get("admin1")} ({g.get("country_code")})'

        data = fetch_forecast(lat, lon, args.days, args.tz)
        daily = data["daily"]

        rows = []
        for i, date_str in enumerate(daily["time"]):
            code = int(daily["weather_code"][i])
            wdesc = WEATHER_CODE_MAP_JA.get(code, f"不明({code})")
            tmax = daily["temperature_2m_max"][i]
            tmin = daily["temperature_2m_min"][i]
            pop = daily.get("precipitation_probability_max", [None]*len(daily["time"]))[i]
            # 日付フォーマット
            y, m, d = map(int, date_str.split("-"))
            day_label = dt.date(y, m, d).strftime("%Y-%m-%d (%a)")
            rows.append([
                day_label,
                wdesc,
                f"{tmin:.1f}°C",
                f"{tmax:.1f}°C",
                f"{pop}%" if pop is not None else "-",
            ])

        headers = ["日付", "天気", "最低気温", "最高気温", "降水確率(最大)"]
        print(f"場所: {city_label}  [lat={lat:.3f}, lon={lon:.3f}]  / TZ={args.tz}")
        print(fmt_table(rows, headers))

    except Exception as e:
        print(f"エラー: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
