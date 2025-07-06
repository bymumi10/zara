import requests
from bs4 import BeautifulSoup
import os

# --- Gerekli Bilgileri GitHub Secrets'tan ve Ürün Linkinden Alacağız ---

# GitHub Actions tarafından sağlanan ortam değişkenlerinden gizli bilgileri alıyoruz
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# !!! SADECE BU SATIRI KENDİ ÜRÜN LİNKİNİZLE DEĞİŞTİRİN !!!
ZARA_URUN_URL = 'https://www.zara.com/tr/tr/uzun-sisme-yelek-p03046230.html'

# Tarayıcı bilgisi
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7'
}

# Stok durumunu saklayacağımız dosyanın adı
STATUS_FILE = 'stok_durumu.txt'

# Kontrol edilecek anahtar kelime listeleri
TUKENDI_KELIMELERI = ["tükendi", "yakında", "out of stock", "coming soon"]
STOKTA_VAR_KELIMELERI = ["ekle", "sepete ekle", "add to cart"]


def telegram_bildirim_gonder(mesaj):
    """Telegram botu aracılığıyla mesaj gönderir."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Hata: Telegram bilgileri (token/chat_id) ortam değişkenlerinde bulunamadı!")
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
    """Zara ürün sayfasını esnek bir şekilde kontrol eder."""
    try:
        response = requests.get(ZARA_URUN_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
        
        sayfa_metni = response.text.lower()

        for kelime in TUKENDI_KELIMELERI:
            if kelime in sayfa_metni:
                print(f"Stokta yok işareti bulundu: '{kelime}'")
                return "Stokta Yok"

        for kelime in STOKTA_VAR_KELIMELERI:
            if kelime in sayfa_metni:
                print(f"Stokta var işareti bulundu: '{kelime}'")
                return "Stokta Var"

        print("Belirgin bir stok bilgisi bulunamadı. Stokta yok olarak varsayılıyor.")
        return "Stokta Yok"

    except requests.exceptions.RequestException as e:
        print(f"Web sitesine erişirken bir hata oluştu: {e}")
        return "Hata"

# --- ANA ÇALIŞMA MANTIĞI ---

print("Stok takip betiği çalıştırıldı.")

try:
    with open(STATUS_FILE, 'r') as f:
        onceki_stok_durumu = f.read().strip()
except FileNotFoundError:
    onceki_stok_durumu = "Bilinmiyor"

print(f"Önceki stok durumu: {onceki_stok_durumu}")

yeni_stok_durumu = zara_stok_kontrolu()
print(f"Mevcut stok durumu: {yeni_stok_durumu}")

if yeni_stok_durumu != "Hata" and yeni_stok_durumu != onceki_stok_durumu:
    with open(STATUS_FILE, 'w') as f:
        f.write(yeni_stok_durumu)
    print(f"Durum değişti. Yeni durum dosyaya yazıldı: {yeni_stok_durumu}")

    if yeni_stok_durumu == "Stokta Var":
        print("STOK GELDİ! Bildirim gönderiliyor...")
        mesaj = f"🎉 <b>STOK BİLDİRİMİ</b> 🎉\n\nTakip ettiğiniz ürün artık stokta!\n\n<a href='{ZARA_URUN_URL}'>Hemen ürüne gitmek için tıklayın!</a>"
        telegram_bildirim_gonder(mesaj)
else:
    print("Stok durumunda değişiklik yok veya kontrol sırasında hata oluştu.")

print("Betiğin çalışması tamamlandı.")
