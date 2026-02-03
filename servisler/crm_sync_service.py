import logging
import json
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import asyncio
from .db_service import save_lead

# Bu değerler .env dosyasından alınmalıdır
CRM_BASE_URL = os.getenv("CRM_BASE_URL", "https://crm.example.com")
CRM_EMAIL = os.getenv("CRM_EMAIL")
CRM_PASSWORD = os.getenv("CRM_PASSWORD")

logger = logging.getLogger(__name__)

def scrape_crm_to_db(filter_id=5):
    """
    Scrape CRM leads and save to MongoDB
    """
    results = []
    driver = None
    
    try:
        logger.info("🚀 Starting CRM scraper...")
        
        options = Options()
        options.add_argument('--headless') # Arka planda çalışsın
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        # Login ve Scrape işlemleri buraya gelecek...
        # Şimdilik örnek veri döndürelim (Geliştirme aşaması için)
        sample_data = [
            {"name": "Ahmet Yılmaz", "tp_number": "123456", "email": "ahmet@mail.com"},
            {"name": "Mehmet Demir", "tp_number": "654321", "email": "mehmet@mail.com"}
        ]
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        for lead in sample_data:
            loop.run_until_complete(save_lead(lead))
        loop.close()
        
        return len(sample_data)
        
    except Exception as e:
        logger.error(f"❌ Scrape error: {e}")
        return 0
    finally:
        if driver:
            driver.quit()
