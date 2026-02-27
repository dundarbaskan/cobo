import logging

# Logger ayarları
logger = logging.getLogger("VolumeFilter")

class BaseVolumeFilter:
    """
    Finansal işlemler için MANUEL ve HIZLI hacim filtresi.
    API çağırmaz, sabit tanımlanmış 2026-02-12 kurlarını kullanır.
    Belirlenen limitin (Varsayılan 1 USD) altındaki "Dust" (Toz) işlemleri engeller.
    """

    # 12 Şubat 2026 - Manuel Kur Listesi
    # amount_for_1_usd: 1 USD eden coin miktarı (Limit kontrolü için referans)
    # usd_rate: 1 Coinin USD karşılığı (Hesaplama ve Loglama için)
    RATES = {
        "BTC":  { "usd_rate": 67158.16, "amount_for_1_usd": 0.00001489 },
        "ETH":  { "usd_rate": 1990.28, "amount_for_1_usd": 0.00050244 },
        "BNB":  { "usd_rate": 611.28, "amount_for_1_usd": 0.00163591 },
        "XRP":  { "usd_rate": 1.398, "amount_for_1_usd": 0.715307 },
        "SOL":  { "usd_rate": 81.18, "amount_for_1_usd": 0.012318 },
        "TRX":  { "usd_rate": 0.2783, "amount_for_1_usd": 3.593244 },
        "TRON": { "usd_rate": 0.2783, "amount_for_1_usd": 3.593244 },
        "ADA":  { "usd_rate": 0.267, "amount_for_1_usd": 3.745318 },
        "LTC":  { "usd_rate": 53.57, "amount_for_1_usd": 0.018667 },
        "DOT":  { "usd_rate": 1.29, "amount_for_1_usd": 0.775193 },
        "MATIC":{ "usd_rate": 0.09, "amount_for_1_usd": 11.111111 },
        "USDT": { "usd_rate": 1.00, "amount_for_1_usd": 1.000000 },
        "USDC": { "usd_rate": 1.00, "amount_for_1_usd": 1.000000 }
    }

    @staticmethod
    async def should_block_transaction(symbol: str, amount: float, transaction_id: str = "N/A", min_usd_limit: float = 1.0) -> bool:
        """
        Bir işlemin limit altında kalıp kalmadığını MANUEL LİSTE üzerinden kontrol eder.
        
        Args:
            symbol (str): Coin sembolü (BTC, ETH, vb.)
            amount (float): İşlem miktarı
            transaction_id (str): Loglama için işlem ID'si
            min_usd_limit (float): USD cinsinden minimum kabul edilebilir değer (Default: $1)
            
        Returns:
            bool: True ise İŞLEM ENGELLENMELİDİR. False ise işlem geçerlidir.
        """
        try:
            # 1. Veri Normalizasyonu
            symbol = str(symbol).strip().upper()
            try:
                amount = float(amount)
            except ValueError:
                logger.error(f"❌ [VolumeFilter] Geçersiz miktar verisi: {amount}")
                return True # Güvenlik için blokla

            # 2. Kur Bilgisini Al
            coin_data = BaseVolumeFilter.RATES.get(symbol)
            
            # Tam eşleşme yoksa, içinde geçiyor mu diye bak (Örn: "ERC20_ETH" -> "ETH")
            if not coin_data:
                for key, data in BaseVolumeFilter.RATES.items():
                    if key in symbol:
                        coin_data = data
                        break
            
            if not coin_data:
                # Fallback: Eğer listede yoksa ve Stablecoin ise (örn BUSD) 1:1 kabul et
                if "USD" in symbol:
                     usd_rate = 1.0
                else:
                    logger.warning(f"⚠️ [VolumeFilter] Tanımsız Coin: {symbol} - Kur 0 kabul edilecek.")
                    usd_rate = 0.0
            else:
                usd_rate = coin_data["usd_rate"]

            # 3. Değer Hesaplama
            usd_value = amount * usd_rate
            
            # 4. Limit Kontrolü
            if usd_value < min_usd_limit:
                # Özel durum: Eğer oran 0 ise (bilinmeyen coin) ve biz engellemek istemiyorsak burayı revize ederiz.
                # Ancak şu an listede olmayanları da limit altı sayıp engeller (usd_value=0 < 1).
                # Main.py'de zaten allowed_tokens kontrolü var, o yüzden burada sadece o listedekiler gelir.
                
                BaseVolumeFilter._log_block(symbol, amount, usd_value, min_usd_limit, transaction_id)
                return True # BLOCK

            # İşlem limitin üzerinde, geçerli.
            return False # ALLOW

        except Exception as e:
            logger.error(f"⚠️ [VolumeFilter] Kritik Hata: {e} | Tx: {transaction_id}")
            # Hata durumunda sistemi kilitlememek adına (Fail Open)
            return False

    @staticmethod
    def _log_block(symbol, amount, usd_value, limit, tx_id):
        """Reddedilen işlemler için kurumsal log formatı"""
        amount_str = f"{amount:.10f}".rstrip('0').rstrip('.')
        if not amount_str: amount_str = "0"
        
        logger.warning(
            f"\n⛔ ------------------[ FİLTRE ENGELİ ]------------------ ⛔"
            f"\n🛑 İŞLEM REDDEDİLDİ: Minimum Tutarın Altında (Manuel Liste)"
            f"\n🆔 Tx ID        : {tx_id}"
            f"\n💎 Varlık       : {symbol}"
            f"\n💰 Gelen Miktar : {amount_str}"
            f"\n💵 USD Değeri   : {usd_value:.4f} $"
            f"\n📉 Limit (Min)  : {limit} $"
            f"\n🛡️ Aksiyon      : BLOCKED (Manuel Limit Kontrolü)"
            f"\n------------------------------------------------------------"
        )
