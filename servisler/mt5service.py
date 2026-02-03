# -*- coding: utf-8 -*-
"""
MT5 User Management Module
Kullanıcı bilgilerini çekme ve bakiye ekleme fonksiyonları
"""

import sys
from MT5Manager import ManagerAPI

class MT5UserManager:
    """MT5 kullanıcı yönetimi için sınıf"""
    
    def __init__(self, server, login, password):
        self.server = server
        self.login = int(login)
        self.password = password
        self.manager = None
    
    def connect(self):
        """MT5'e bağlan"""
        try:
            self.manager = ManagerAPI()
            result = self.manager.Connect(self.server, self.login, self.password, timeout=30000)
            
            if result:
                print(f"✅ MT5'e bağlanıldı: {self.server}")
                return True
            else:
                print(f"❌ MT5 bağlantı hatası!")
                return False
        except Exception as e:
            print(f"❌ Bağlantı hatası: {e}")
            return False
    
    def disconnect(self):
        """MT5 bağlantısını kes"""
        if self.manager:
            try:
                self.manager.Disconnect()
                print("🔌 MT5 bağlantısı kesildi")
            except: pass
    
    def get_user_info(self, user_login):
        """Kullanıcı bilgilerini çek"""
        if not self.manager:
            return None
        
        try:
            user = self.manager.UserRequest(int(user_login))
            if not user:
                return None
            
            account = self.manager.UserAccountRequest(int(user_login))
            if isinstance(account, list) and len(account) > 0:
                account = account[0]
            
            return {
                'login': user_login,
                'name': getattr(user, 'Name', 'N/A'),
                'group': getattr(user, 'Group', 'N/A'),
                'email': getattr(user, 'Email', 'N/A'),
                'balance': getattr(account, 'Balance', 0) if account else 0,
                'credit': getattr(account, 'Credit', 0) if account else 0,
                'equity': getattr(account, 'Equity', 0) if account else 0
            }
        except Exception as e:
            print(f"❌ Bilgi alma hatası: {e}")
            return None

    def get_all_logins(self, group_mask="*"):
        """Tüm kullanıcı loginlerini çek"""
        if not self.manager:
            return []
        try:
            logins = self.manager.UserLogins(group_mask)
            return logins if logins else []
        except Exception as e:
            print(f"❌ Login listesi hatası: {e}")
            return []
    
    def add_balance(self, user_login, amount, comment="Balance adjustment"):
        """Kullanıcıya bakiye ekle"""
        if not self.manager:
            return False
        
        try:
            # ÖNEMLİ: Bu MT5Manager versiyonunda (5.0.4288) DealerBalance parametre sırası:
            # DealerBalance(login, value/amount, type/action, comment)
            # Action: 2 = DEAL_BALANCE (veya DEAL_CHARGE/ADJUSTMENT)
            # Testlerimizde Action 2 başarılı (True), Action 0 "Invalid parameters" dönüyor.
            result = self.manager.DealerBalance(int(user_login), float(amount), 2, comment)
            
            # Başarı kontrolü: Versiyon 5.0.4288 işlem başarılıysa Ticket numarası (pozitif int) döner.
            if isinstance(result, bool):
                success = result
            elif isinstance(result, (int, float)):
                # Ticket numarası döndüyse (örn: 17332670) başarılı demektir.
                success = result > 0
            else:
                success = False
                
            if success:
                print(f"✅ Bakiye başarıyla eklendi: {user_login} - {amount} ({comment})")
            else:
                # Hata detayını alalım
                try:
                    import MT5Manager
                    _, _, err_msg = MT5Manager.LastError()
                    print(f"❌ Bakiye ekleme başarısız! Hata: {err_msg} (TP: {user_login}, Result: {result})")
                except:
                    print(f"❌ Bakiye ekleme başarısız! Result: {result} (TP: {user_login})")
                    
            return success
        except Exception as e:
            print(f"❌ Bakiye ekleme hatası: {e}")
            return False

    def get_financial_summary(self, user_login):
        """Kullanıcının geçmiş işlemlerinden toplam yatırım ve çekimi hesaplar"""
        if not self.manager:
            return 0, 0
        
        import time
        try:
            # Hesabın tüm geçmişine bakabilmek için başlangıç zamanını çok eskiye alıyoruz
            from_time = 0 
            to_time = int(time.time()) + 86400
            
            deals = self.manager.DealRequest(int(user_login), from_time, to_time)
            
            total_dep = 0.0
            total_with = 0.0
            
            if deals:
                for deal in deals:
                    # Action 2 = DEAL_BALANCE (Bakiye işlemleri)
                    action = getattr(deal, 'Action', None)
                    profit = getattr(deal, 'Profit', 0.0)
                    comment = str(getattr(deal, 'Comment', '')).upper()
                    
                    if action == 2:
                        # Kullanıcının istediği özel yorumları ve standart bakiye hareketlerini kontrol et
                        if "DEPOSIT" in comment:
                            total_dep += profit
                        elif "WITHDRAW" in comment:
                            total_with += abs(profit)
                        else:
                            # Eğer yorumda bir şey yazmıyorsa ama bakiye işlemiyse:
                            if profit > 0:
                                total_dep += profit
                            elif profit < 0:
                                total_with += abs(profit)
                            
            return round(total_dep, 2), round(total_with, 2)
        except Exception as e:
            print(f"❌ Finansal özet hatası ({user_login}): {e}")
            return 0, 0
