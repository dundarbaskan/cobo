import requests

def coin_parser(symbol, amount):
    """
    CryptoCompare API kullanarak kripto parayı USD'ye çevirir.
    symbol: Cobo'dan gelen asset_id (BTC, TRON, ETH, USDT vb.)
    amount: Gelen miktar
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
            # CryptoCompare de Binance gibi TRX kısaltmasını kullanır.
            # Cobo'dan gelen 'TRON' verisini 'TRX' yapıyoruz.
            clean_symbol = "TRX" if symbol == "TRON" else symbol
            
            # CryptoCompare Single Price API Endpoint
            # fsym: Hangi coin, tsyms: Hangi para birimi
            url = f"https://min-api.cryptocompare.com/data/price?fsym={clean_symbol}&tsyms=USD"
            
            response = requests.get(url, timeout=5)
            response.raise_for_status() 
            
            data = response.json()
            
            # CryptoCompare cevabı: {"USD": 0.1234} formatındadır.
            if "USD" in data:
                price = float(data['USD'])
                usd_amount = amount * price
            else:
                print(f"Hata: {clean_symbol} için USD fiyatı bulunamadı.")
            
        except Exception as e:
            print(f"Kur çekilirken hata oluştu ({symbol}): {e}")
            # Hata durumunda usd_amount ham miktar olarak kalır
            usd_amount = amount 

    # 3. İkili Return formatı (Senin istediğin liste yapısı)
    return [
        {"currency": symbol, "amount": amount},
        {"currency": "USD", "amount": round(usd_amount, 2)}
    ]