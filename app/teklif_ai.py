import os, json, base64
import anthropic

client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))

SISTEM_PROMPT = """Sen bir teklif/fiyat teklifi analiz uzmanısın. Sana verilen PDF veya belgedeki fiyat teklifinden aşağıdaki bilgileri çıkar ve SADECE geçerli JSON döndür, başka hiçbir şey yazma.

Çıkarılacak JSON formatı:
{
  "tedarikci_adi": "string veya null",
  "birim_fiyat": number veya null,
  "para_birimi": "TL veya EUR veya USD",
  "vade_gun": number veya null,
  "termin_gun": number veya null,
  "notlar": "teslim koşulları, garanti, ek bilgiler vb. — string veya null",
  "guven_skoru": 0.0-1.0
}

Kurallar:
- birim_fiyat: KDV hariç birim fiyat (birden fazla kalem varsa en uygun/toplam teklifin birim fiyatını al)
- Sayıları virgüllü Türk formatından (1.234,56) float'a çevir (1234.56)
- vade_gun: ödeme vadesi gün sayısı (örn. "30 gün" → 30)
- termin_gun: teslimat süresi gün sayısı
- para_birimi: belirtilmemişse "TL" varsay
- guven_skoru: verinin ne kadar net okunabildiği (0=çok belirsiz, 1=çok net)
- Bulamadığın alanlar için null kullan"""


def teklif_oku(dosya_yolu: str, malzeme_adi: str = None) -> dict:
    """PDF teklif dosyasını okur, AI ile analiz eder, dict döndürür."""
    with open(dosya_yolu, 'rb') as f:
        pdf_data = base64.standard_b64encode(f.read()).decode('utf-8')

    ek_bilgi = ''
    if malzeme_adi:
        ek_bilgi = f' Aranan malzeme: "{malzeme_adi}".'

    response = client.messages.create(
        model='claude-haiku-4-5-20251001',
        max_tokens=800,
        system=SISTEM_PROMPT,
        messages=[{
            'role': 'user',
            'content': [
                {
                    'type': 'document',
                    'source': {
                        'type': 'base64',
                        'media_type': 'application/pdf',
                        'data': pdf_data,
                    }
                },
                {
                    'type': 'text',
                    'text': f'Bu fiyat teklifini analiz et ve istenen JSON formatında çıktı ver.{ek_bilgi}'
                }
            ]
        }]
    )

    metin = response.content[0].text.strip()
    if '```' in metin:
        metin = metin.split('```')[1]
        if metin.startswith('json'):
            metin = metin[4:]
    return json.loads(metin)
