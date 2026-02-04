import os
import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

from pathlib import Path

# .env dosyasını ana dizinden yükle
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

MONGODB_URL = "mongodb+srv://wimcrm:edWfyiwTjpnkgAzx@data.drjzdcy.mongodb.net/maxipinfo?retryWrites=true&w=majority&appName=DATA"

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

async def ensure_transaction_index():
    """Transaction ID üzerinde benzersiz index oluşturur."""
    try:
        await db.transactions.create_index("transaction_id", unique=True)
    except Exception as e:
        print(f"Index creation error: {e}")

# İlk importta index'i garantiye al (Async olduğu için event loop içinde çağrılmalı, 
# ama şimdilik save anında kontrol edeceğiz veya main startup'ta)

from pymongo.errors import DuplicateKeyError

async def try_lock_transaction(transaction_id, tp_number, amount, symbol, status):
    """
    Atomik işlem kilidi. 
    Eğer işlem daha önce kaydedildiyse False döner (Duplicate Error).
    Eğer ilk kez geliyorsa kaydeder ve True döner.
    """
    try:
        await db.transactions.insert_one({
            "transaction_id": transaction_id,
            "tp_number": str(tp_number),
            "amount": amount,
            "symbol": symbol,
            "status": status,
            "processed_at": datetime.datetime.now()
        })
        return True
        
    except DuplicateKeyError:
        # Bu transaction_id zaten var -> Race Condition engellendi!
        return False
        
    except Exception as e:
        # Başka bir hata (Bağlantı koptu, Auth hatası vs.)
        # Bunu yutmamalıyız, loglayıp hata verelim ki ana kod bilsin!
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
        return_document=True,
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

