import requests

def coin_parser(symbol, amount):
    """
    CryptoCompare API kullanarak kripto parayı USD'ye çevirir.
    symbol: Cobo'dan gelen asset_id (BTC, TRON, ETH, USDT vb.)
    amount: Gelen miktar
    """
    # CryptoCompare API kullanarak kripto parayı USD'ye çevirir.
    # 1. Verileri temizle (Örn: "1.5e-06" gibi bilimsel sayıları anlar)
    symbol = str(symbol).upper().strip()
    try:
        amount = float(amount)
    except Exception:
        amount = 0.0

    # 2. Gerçek coin adını ayıkla (Örn: "ERC20_ETH" geldiğinde "ETH"yi çeker)
    clean_symbol = symbol
    for coin in ["USDT", "USDC", "TRX", "TRON", "ETH", "BTC", "LTC", "SOL", "MATIC", "BNB", "XRP", "ADA", "DOT"]:
        if coin in symbol:
            clean_symbol = coin
            break

    # CryptoCompare TRON'u TRX olarak tanır
    if clean_symbol == "TRON":
        clean_symbol = "TRX"
        
    usd_amount = amount 
    
    # 3. Zaten Stabil coin ise API'yi yorma, 1:1 geçir
    if clean_symbol in ["USDT", "USDC"]:
        usd_amount = amount
    else:
        try:
            # CryptoCompare Single Price API Endpoint
            url = f"https://min-api.cryptocompare.com/data/price?fsym={clean_symbol}&tsyms=USD"
            
            response = requests.get(url, timeout=5)
            response.raise_for_status() 
            
            data = response.json()
            
            if "USD" in data:
                price = float(data['USD'])
                usd_amount = amount * price
            else:
                print(f"Hata: {clean_symbol} için USD fiyatı bulunamadı.")
            
        except Exception as e:
            print(f"Kur çekilirken hata oluştu ({symbol}): {e}")
            usd_amount = amount 

    # 3. İkili Return formatı (Senin istediğin liste yapısı)
    return [
        {"currency": symbol, "amount": amount},
        {"currency": "USD", "amount": round(usd_amount, 2)}
    ]