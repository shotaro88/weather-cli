# Weather CLI (Open-Meteo)

APIキー不要の Open-Meteo を使った、都市名ベースの**日次天気予報**CLIサンプルです。  
標準ライブラリのみで動き、学習用に読みやすい構成になっています。

## 使い方

```bash
python3 weather.py --city Tokyo --days 3
python3 weather.py --city 大阪 --days 5 --tz Asia/Tokyo
