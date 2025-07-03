import requests
from bs4 import BeautifulSoup
import os

# --- Gerekli Bilgileri GitHub Secrets'tan ve Ürün Linkinden Alacağız ---

# GitHub Actions tarafından sağlanan ortam değişkenlerinden gizli bilgileri alıyoruz
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# 3. Takip etmek istediğiniz Zara ürününün linkini buraya yapıştırın
ZARA_URUN_URL = 'https://www.zara.com/tr/tr/uzun-sisme-yelek-p03046230.html' # <-- SADECE BURAYI DEĞİŞTİRİN

# 4. Tarayıcı bilgisi
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7'
}

# Stok durumunu saklayacağımız dosyanın adı
STATUS_FILE = 'stok_durumu.txt'

def telegram_bildirim_gonder(mesaj):
    """Telegram botu aracılığıyla mesaj gönderir."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Hata: Telegram bilgileri (token/chat_id) eksik!")
        return
        
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': mesaj,
        'parse_mode': 'HTML',
        'disable_web_page_preview': 'false'
    }
    try:
        response = requests.post(url, data=payload, timeout=10)
        print("Telegram bildirimi gönderildi. Sunucu yanıtı:", response.status_code)
    except Exception as e:
        print(f"Telegram bildirimi gönderilirken hata oluştu: {e}")

def zara_stok_kontrolu():
    """Zara ürün sayfasını kontrol eder ve stok durumunu döndürür."""
    try:
        response = requests.get(ZARA_URUN_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Zara'nın sitesindeki "Tükendi" veya benzeri ifadeleri arıyoruz.
        # Bu seçiciler sitenin tasarımına göre değişebilir.
        if "tükendi" in response.text.lower() or "out of stock" in response.text.lower():
            return "Stokta Yok"
        
        # "Sepete Ekle" butonu varsa stokta demektir.
        if "add to cart" in response.text.lower() or "sepete ekle" in response.text.lower():
             return "Stokta Var"

        return "Stokta Yok" # Belirgin bir işaret bulamazsak, yok kabul edelim.

    except requests.exceptions.RequestException as e:
        print(f"Web sitesine erişirken bir hata oluştu: {e}")
        return "Hata"

# --- ANA ÇALIŞMA MANTIĞI ---

print("Stok takip betiği çalıştırıldı.")

# Önceki stok durumunu dosyadan oku
try:
    with open(STATUS_FILE, 'r') as f:
        onceki_stok_durumu = f.read().strip()
except FileNotFoundError:
    onceki_stok_durumu = "Bilinmiyor"

print(f"Önceki stok durumu: {onceki_stok_durumu}")

# Mevcut stok durumunu kontrol et
yeni_stok_durumu = zara_stok_kontrolu()
print(f"Mevcut stok durumu: {yeni_stok_durumu}")

if yeni_stok_durumu != "Hata" and yeni_stok_durumu != onceki_stok_durumu:
    # Durum değiştiyse, yeni durumu dosyaya yaz
    with open(STATUS_FILE, 'w') as f:
        f.write(yeni_stok_durumu)
    print(f"Durum değişti. Yeni durum dosyaya yazıldı: {yeni_stok_durumu}")

    # Eğer stok yokken stoğa girdiyse bildirim gönder
    if yeni_stok_durumu == "Stokta Var":
        print("STOK GELDİ! Bildirim gönderiliyor...")
        mesaj = f"🎉 <b>STOK BİLDİRİMİ</b> 🎉\n\nTakip ettiğiniz ürün artık stokta!\n\n<a href='{ZARA_URUN_URL}'>Hemen ürüne gitmek için tıklayın!</a>"
        telegram_bildirim_gonder(mesaj)
else:
    print("Stok durumunda değişiklik yok veya kontrol sırasında hata oluştu.")

print("Betiğin çalışması tamamlandı.")
