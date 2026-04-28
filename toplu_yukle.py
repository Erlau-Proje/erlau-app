"""
Teknik Resim Toplu Yükleme Scripti
Kullanım: python toplu_yukle.py
Gereksinim: pip install requests
"""

import os
import requests
from pathlib import Path

# ─── AYARLAR ──────────────────────────────────────────────────────────────────
SERVER_URL = "http://178.104.49.105:5000"               # Sunucu adresi
EMAIL      = "admin@erlau.com"                          # Giriş e-postanız
PASSWORD   = "123456*"                             # ← Şifreni buraya yaz
KLASOR     = r"C:\Users\can.otu\Desktop\ürünler"        # Ana klasör yolu
# ──────────────────────────────────────────────────────────────────────────────

def main():
    ana_klasor = Path(KLASOR)
    if not ana_klasor.exists():
        print(f"HATA: Klasör bulunamadı → {KLASOR}")
        return

    # Tüm PDF'leri tara
    pdf_listesi = list(ana_klasor.rglob("*.pdf"))
    if not pdf_listesi:
        print("Hiç PDF dosyası bulunamadı.")
        return
    print(f"{len(pdf_listesi)} PDF bulundu.\n")

    # Sisteme giriş
    session = requests.Session()
    print("Giriş yapılıyor...")
    try:
        r = session.post(f"{SERVER_URL}/login",
                         data={"email": EMAIL, "password": PASSWORD},
                         allow_redirects=True, timeout=15)
    except requests.exceptions.ConnectionError:
        print(f"HATA: Sunucuya bağlanılamadı → {SERVER_URL}")
        return

    if "/login" in r.url:
        print("HATA: Giriş başarısız. E-posta/şifre kontrol edin.")
        return
    print("Giriş başarılı.\n")

    yuklenen = 0
    hata = 0

    for pdf in pdf_listesi:
        # Klasör yolunu ana klasöre göre relative hesapla
        relative = pdf.relative_to(ana_klasor)
        # parts[:-1] = klasör kısımları, parts[-1] = dosya adı
        klasor_yolu = "/".join(relative.parts[:-1])   # örn: "MakineA" veya "MakineA/Alt"
        dosya_gosterim = pdf.stem                      # dosya adı .pdf olmadan

        print(f"  {'[' + klasor_yolu + '] ' if klasor_yolu else ''}{dosya_gosterim}.pdf", end=" ... ")

        try:
            with open(pdf, "rb") as f:
                r = session.post(
                    f"{SERVER_URL}/teknik-resim/yukle",
                    data={
                        "klasor": klasor_yolu,
                        "dosya_adi_gosterim": dosya_gosterim,
                    },
                    files={"pdf_dosya": (pdf.name, f, "application/pdf")},
                    headers={"X-Requested-With": "XMLHttpRequest"},
                    allow_redirects=True,
                    timeout=60
                )
            if r.status_code == 200:
                print("OK")
                yuklenen += 1
            else:
                print(f"HATA (HTTP {r.status_code})")
                hata += 1
        except Exception as e:
            print(f"HATA: {e}")
            hata += 1

    print(f"\n{'─'*60}")
    print(f"Tamamlandı: {yuklenen} başarılı, {hata} hatalı.")

if __name__ == "__main__":
    main()
