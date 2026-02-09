import requests

def coin_parser(symbol, amount):
    """
    symbol: Gelen birim (BTC, TRON, ETH, USDT vb.)
    amount: Gelen miktar (String veya Float)
    """
    # 1. Verileri temizle
    symbol = str(symbol).upper().strip()
    amount = float(amount)
    
    # Varsayılan değerler
    usd_amount = amount 
    
    # 2. Eğer zaten USDT ise API'ye gitmeye gerek yok
    if symbol == "USDT":
        usd_amount = amount
    else:
        try:
            # --- KRİTİK DÜZELTME ---
            # Cobo 'TRON' diyor, Binance 'TRX' diyor. 
            # Eğer symbol TRON ise onu TRX'e çevirip Binance'e öyle soralım.
            binance_symbol = "TRX" if symbol == "TRON" else symbol
            
            # Binance API'den sembol + USDT çiftini sorgula
            url = f"https://api.binance.com/api/v3/ticker/price?symbol={binance_symbol}USDT"
            response = requests.get(url, timeout=5)
            response.raise_for_status() 
            
            data = response.json()
            price = float(data['price'])
            
            # Kurla çarpımı yap
            usd_amount = amount * price
            
        except Exception as e:
            print(f"Kur çekilirken hata oluştu ({symbol}): {e}")
            # Hata durumunda usd_amount ham miktar olarak kalır
            usd_amount = amount 

    # 3. İkili Return formatı
    return [
        {"currency": symbol, "amount": amount},
        {"currency": "USD", "amount": round(usd_amount, 2)}
    ]