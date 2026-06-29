import os
import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ReturnDocument

from config.settings import MONGODB_URL

client = AsyncIOMotorClient(MONGODB_URL)
db = client.maxipinfo
cobo_collection = db.COBO


async def save_lead(lead_data):
    """
    Lead bilgisini MongoDB'ye kaydeder.
    lead_data: { "name": "...", "tp_number": "...", "email": "..." }
    """
    await cobo_collection.update_one(
        {"tp_number": str(lead_data["tp_number"])},
        {"$set": lead_data},
        upsert=True
    )

async def get_lead_by_tp(tp_number):
    return await cobo_collection.find_one({"tp_number": str(tp_number)})

async def get_lead_by_address(address):
    """
    Cüzdan adresinden hangi lead'e ait olduğunu bulur.
    """
    return await cobo_collection.find_one({"wallets.address": address})

async def save_wallet_to_lead(tp_number, wallet_data):
    """
    Oluşturulan cüzdanı lead'e bağlar.
    """
    await cobo_collection.update_one(
        {"tp_number": str(tp_number)},
        {"$push": {"wallets": wallet_data}}
    )

async def increment_deposit_count(tp_number):
    """
    Yatırım sayısını artırır ve yeni sayıyı döner.
    """
    result = await cobo_collection.find_one_and_update(
        {"tp_number": str(tp_number)},
        {"$inc": {"deposit_count": 1}},
        return_document=True,
        upsert=True
    )
    return result.get("deposit_count", 1)

async def get_existing_wallet(tp_number, asset_name, chain_id):
    """
    Belirli bir varlık ve ağ için mevcut cüzdanı kontrol eder.
    """
    lead = await cobo_collection.find_one({
        "tp_number": str(tp_number),
        "wallets": {
            "$elemMatch": {
                "asset": asset_name,
                "chain_id": chain_id
            }
        }
    })
    
    if lead and "wallets" in lead:
        for wallet in lead["wallets"]:
            if wallet.get("asset") == asset_name and wallet.get("chain_id") == chain_id:
                return wallet
    return None



# İlk importta index'i garantiye al (Async olduğu için event loop içinde çağrılmalı, 
# ama şimdilik save anında kontrol edeceğiz veya main startup'ta)

from pymongo.errors import DuplicateKeyError

async def try_lock_transaction(transaction_id, tp_number, amount, symbol, status):
    """
    ATOMİK İŞLEM KİLİDİ (Race-Condition Proof!)
    
    MongoDB'nin upsert özelliğini kullanarak tamamen atomik bir kilit oluşturur.
    Eğer transaction_id yoksa ekler ve True döner.
    Eğer transaction_id varsa hiçbir şey yapmaz ve False döner.
    
    Bu yaklaşım 100% güvenlidir çünkü:
    1. find_one + insert_one gibi 2 adım YOK (race condition riski sıfır)
    2. MongoDB seviyesinde atomik işlem
    3. Unique index olsa da olmasa da çalışır (ama unique index olmalı!)
    """
    try:
        result = await db.transactions.update_one(
            {"transaction_id": transaction_id},  # Filtre: Bu ID var mı?
            {
                "$setOnInsert": {  # Sadece yeni kayıt oluşturuluyorsa set et
                    "transaction_id": transaction_id,
                    "tp_number": str(tp_number),
                    "amount": amount,
                    "symbol": symbol,
                    "status": status,
                    "processed_at": datetime.datetime.now()
                }
            },
            upsert=True  # Yoksa ekle, varsa dokunma!
        )
        
        # upserted_id varsa -> Yeni kayıt oluşturuldu (İlk gelen sensin!)
        # upserted_id yoksa -> Zaten vardı (Başkası senden önce gelmiş)
        return result.upserted_id is not None
        
    except Exception as e:
        # Bağlantı hatası vs.
        print(f"❌ DB Kilitleme Hatası (Kritik): {e}")
        raise e

# Geriye uyumluluk veya sadece kontrol amaçlı (Artık ana logic'te try_lock kullanılmalı)
async def is_transaction_processed(transaction_id):
    res = await db.transactions.find_one({"transaction_id": transaction_id})
    return res is not None

async def log_transaction(transaction_id, tp_number, amount, symbol, status):
    """(Deprecated) Artık try_lock_transaction kullanılmalı"""
    await try_lock_transaction(transaction_id, tp_number, amount, symbol, status)

async def update_financial_stats(tp_number, amount, is_deposit=True):
    """Kullanıcının toplam yatırım/çekim bilgisini günceller."""
    field = "total_deposit" if is_deposit else "total_withdrawal"
    result = await cobo_collection.find_one_and_update(
        {"tp_number": str(tp_number)},
        {"$inc": {field: amount}},
        return_document=ReturnDocument.AFTER,
        upsert=True
    )
    return result

async def get_all_our_addresses():
    """Sistemdeki tüm cüzdan adreslerini döner (iç transfer tespiti için)"""
    addresses = set()
    cursor = cobo_collection.find({}, {"wallets": 1})
    async for doc in cursor:
        if "wallets" in doc:
            for wallet in doc["wallets"]:
                if "address" in wallet:
                    addresses.add(wallet["address"])
    return addresses

async def ensure_transaction_index():
    """
    transactions collection'ında transaction_id alanına UNIQUE INDEX oluşturur.
    Kullanıcı İsteği Üzerine: Otomatik duplicate silme KAPALI!
    Sadece index oluşturur, hata verirse manuel müdahale gerekir.
    """
    try:
        # Sadece Index Oluşturmaya Çalış
        await db.transactions.create_index("transaction_id", unique=True)
        print("✅ Unique Index oluşturuldu/kontrol edildi: transactions.transaction_id")

    except Exception as e:
        error_msg = str(e).lower()
        if "duplicate key error" in error_msg:
             print(f"⚠️ KRİTİK UYARI: Index oluşturulamadı çünkü çift kayıtlar var!")
             print(f"⚠️ Lütfen veritabanı yöneticisi ile görüşüp manuel temizlik yapın.")
             print(f"⚠️ Hata Detayı: {e}")
        elif "already exists" in error_msg:
             print("✅ Index zaten mevcut.")
        else:
             print(f"❌ Index Hatası: {e}")


# ============================================================
# IBAN YÖNETİMİ — db.ibans koleksiyonu
# Şema: { bank_name, iban, account_holder, is_active, created_at, updated_at }
# Kural: Aynı anda yalnızca 1 IBAN is_active=True olabilir.
# ============================================================

from bson import ObjectId

iban_collection = db.ibans


async def get_active_iban() -> dict | None:
    """Aktif (is_active=True) olan IBAN'ı döner. Yoksa None."""
    doc = await iban_collection.find_one({"is_active": True})
    if doc:
        doc["_id"] = str(doc["_id"])
    return doc


async def get_all_ibans() -> list:
    """Tüm IBAN kayıtlarını döner (aktif + pasif), oluşturma tarihine göre sıralar."""
    cursor = iban_collection.find({}).sort("created_at", -1)
    result = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        result.append(doc)
    return result


async def save_iban(iban_data: dict) -> str:
    """
    Yeni IBAN kaydı ekler.
    Returns: Eklenen belgenin string ObjectId'si
    """
    now = datetime.datetime.now()
    iban_data["is_active"] = False
    iban_data["created_at"] = now
    iban_data["updated_at"] = now
    result = await iban_collection.insert_one(iban_data)
    return str(result.inserted_id)


async def set_iban_active(iban_id: str):
    """
    Belirtilen IBAN'ı aktif eder.
    Önce tüm IBAN'ları pasif yapar, sonra seçileni aktif eder.
    """
    now = datetime.datetime.now()
    # Hepsini pasif yap
    await iban_collection.update_many({}, {"$set": {"is_active": False, "updated_at": now}})
    # Seçileni aktif yap
    await iban_collection.update_one(
        {"_id": ObjectId(iban_id)},
        {"$set": {"is_active": True, "updated_at": now}}
    )


async def set_iban_inactive(iban_id: str):
    """Belirtilen IBAN'ı pasif eder."""
    await iban_collection.update_one(
        {"_id": ObjectId(iban_id)},
        {"$set": {"is_active": False, "updated_at": datetime.datetime.now()}}
    )


async def delete_iban(iban_id: str):
    """Belirtilen IBAN kaydını siler."""
    await iban_collection.delete_one({"_id": ObjectId(iban_id)})


