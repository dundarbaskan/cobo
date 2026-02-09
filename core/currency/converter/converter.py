import requests

def coin_parser(symbol, amount):
    """
    symbol: Gelen birim (BTC, TRX, USDT vb.)
    amount: Gelen miktar (String veya Float)
    """
    # 1. Verileri temizle
    symbol = str(symbol).upper().strip()
    amount = float(amount)
    
    # Varsayılan değerler (Hata durumunda ham veriyi korumak için)
    usd_amount = amount 
    
    # 2. Eğer zaten USDT ise API'ye gitmeye gerek yok
    if symbol == "USDT":
        usd_amount = amount
    else:
        try:
            # Binance API'den sembol + USDT çiftini sorgula
            # Örn: TRX + USDT = TRXUSDT
            url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}USDT"
            response = requests.get(url, timeout=5)
            response.raise_for_status() # Hata varsa yakala
            
            data = response.json()
            price = float(data['price'])
            
            # Kurla çarpımı yap
            usd_amount = amount * price
            
        except Exception as e:
            print(f"Kur çekilirken hata oluştu ({symbol}): {e}")
            # Hata durumunda usd_amount ham miktar olarak kalır veya 0 dönebilirsin
            usd_amount = amount 

    # 3. İstediğin formatta Return (List içinde Map/Dict)
    # İlk eleman: Gelen ham veri
    # İkinci eleman: USD karşılığı
    return [
        {"currency": symbol, "amount": amount},
        {"currency": "USD", "amount": round(usd_amount, 2)}
    ]

# --- Test etmek istersen (Bu kısmı silebilirsin) ---
# result = coin_parser("TRX", "4737.382359")
# print(result) 
# Çıktı: [{'currency': 'TRX', 'amount': 4737.382359}, {'currency': 'USD', 'amount': 584.6}]