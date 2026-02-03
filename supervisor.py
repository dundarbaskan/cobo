import subprocess
import time
import sys
import os

# Çalıştırılacak dosyalar
scripts = [
    {"name": "API & Web", "file": "main.py"},
    {"name": "MT5 Worker", "file": "mt5_worker.py"}
]

processes = []

def start_process(script_info):
    """Bir python scriptini başlatır ve process objesini döner"""
    print(f"🚀 Başlatılıyor: {script_info['name']}...")
    # Windows'ta yeni pencerede açılması için creationflags
    # CREATE_NEW_CONSOLE = 0x10
    creation_flags = 0x10 if sys.platform == "win32" else 0
    
    p = subprocess.Popen(
        [sys.executable, script_info["file"]],
        creationflags=creation_flags, 
        cwd=os.getcwd()
    )
    return p

def main():
    print("🤖 SİSTEM SUPERVISOR BAŞLATILDI")
    print("=================================")
    print("Bu script tüm servisleri (API, MT5, CRM) yönetir ve kapanırsa yeniden başlatır.\n")

    # İlk başlatma
    for script in scripts:
        p = start_process(script)
        processes.append({"process": p, "info": script})
        time.sleep(2) # Karışmaması için az bekle

    print("\n✅ Tüm servisler aktif. İzleme başladı (Çıkış için bu pencereyi kapatın)...\n")

    try:
        while True:
            for item in processes:
                p = item["process"]
                info = item["info"]
                
                # Process durumu kontrol et (None = Çalışıyor)
                if p.poll() is not None:
                    print(f"⚠️ DİKKAT: {info['name']} kapandı/çöktü! Yeniden başlatılıyor... (Exit Code: {p.returncode})")
                    new_p = start_process(info)
                    item["process"] = new_p
                    print(f"♻️ {info['name']} tekrar aktif edildi.")
            
            time.sleep(5) # 5 saniyede bir kontrol et

    except KeyboardInterrupt:
        print("\n🛑 Supervisor durduruluyor, tüm alt processler kapatılacak...")
        for item in processes:
            item["process"].terminate()
        print("Bitti.")

if __name__ == "__main__":
    main()
