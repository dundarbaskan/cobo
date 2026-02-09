
from converter import coin_parser
import json

# Test Senaryosu 1: 33.5 TRON
print("\n--- TEST 1: 33.5 TRON ---")
result_tron = coin_parser("TRON", 33.5)
print(json.dumps(result_tron, indent=4))

# Test Senaryosu 2: 100 USDT (Değişmemeli)
print("\n--- TEST 2: 100 USDT ---")
result_usdt = coin_parser("USDT", 100)
print(json.dumps(result_usdt, indent=4))

# Test Senaryosu 3: 0.5 BTC
print("\n--- TEST 3: 0.5 BTC ---")
result_btc = coin_parser("BTC", 0.5)
print(json.dumps(result_btc, indent=4))
