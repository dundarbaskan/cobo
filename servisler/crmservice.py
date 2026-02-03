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

# Bu değerler .env'den çekilecek
CRM_BASE_URL = os.getenv("CRM_BASE_URL", "https://sales.cepportfoy.com")
CRM_EMAIL = os.getenv("CRM_EMAIL")
CRM_PASSWORD = os.getenv("CRM_PASSWORD")

logger = logging.getLogger(__name__)

def scrape_crm_simple(filter_id=5):
    """
    Kullanıcının paylaştığı karmaşık mantığı içeren CRM scraper.
    """
    results = {}
    driver = None
    
    try:
        logger.info("🚀 Starting CRM scraper...")
        
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.maximize_window()
        
        target_url = f"{CRM_BASE_URL}/#/sales/leads?filter={filter_id}"
        logger.info(f"📍 Navigating to: {target_url}")
        driver.get(target_url)
        time.sleep(10)
        
        if "/login" in driver.current_url or "auth" in driver.current_url:
            logger.info("🔐 Login required...")
            time.sleep(8)
            email = WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="email"]')))
            email.send_keys(CRM_EMAIL)
            password = driver.find_element(By.CSS_SELECTOR, 'input[type="password"]')
            password.send_keys(CRM_PASSWORD)
            password.send_keys(Keys.RETURN)
            logger.info("✓ Login submitted")
            time.sleep(20)
            driver.get(target_url)
            time.sleep(8)

        # Tablodan veri çekme mantığı
        logger.info("⏳ Waiting for TP numbers to load...")
        time.sleep(10)
        
        rows = driver.find_elements(By.CLASS_NAME, 'ant-table-row')
        headers = [h.text.trim() for h in driver.find_elements(By.CSS_SELECTOR, '.ant-table-thead th')]
        
        tp_idx = -1
        name_idx = -1
        for i, h in enumerate(headers):
            if 'TP number' in h: tp_idx = i
            if 'Name' in h: name_idx = i
            
        if tp_idx == -1: tp_idx = 1 # Fallback
        if name_idx == -1: name_idx = 2 # Fallback

        for row in rows:
            cells = row.find_elements(By.TAG_NAME, 'td')
            if len(cells) > max(tp_idx, name_idx):
                tp = cells[tp_idx].text.strip()
                name = cells[name_idx].text.strip()
                if tp.isdigit():
                    results[tp] = name
                    
        logger.info(f"✅ Scraping complete: {len(results)} records found.")
        return results
        
    except Exception as e:
        logger.error(f"❌ Scrape error: {e}")
        return results
    finally:
        if driver:
            driver.quit()
