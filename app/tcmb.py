import requests
import defusedxml.ElementTree as ET
from datetime import date
import json
import os

CACHE_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'tcmb_kur_cache.json')


def get_kurlar() -> dict:
    """TCMB'den günlük döviz kurlarını çeker. Gün içinde cache kullanır."""
    today = date.today().isoformat()

    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE) as f:
                cache = json.load(f)
            if cache.get('tarih') == today:
                return cache.get('kurlar', {})
        except Exception:
            pass

    try:
        resp = requests.get('https://www.tcmb.gov.tr/kurlar/today.xml', timeout=8)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        kurlar = {}
        for cur in root.findall('Currency'):
            kod  = cur.get('CurrencyCode')
            birim = cur.findtext('Unit') or '1'
            satis = cur.findtext('ForexSelling')
            if kod and satis:
                try:
                    kurlar[kod] = round(float(satis) / int(birim), 4)
                except Exception:
                    pass
        with open(CACHE_FILE, 'w') as f:
            json.dump({'tarih': today, 'kurlar': kurlar}, f)
        return kurlar
    except Exception:
        return {}


def get_kur(para_birimi: str) -> float | None:
    """Belirtilen para birimi için günlük TCMB satış kurunu döndürür."""
    if not para_birimi or para_birimi.upper() == 'TL':
        return 1.0
    return get_kurlar().get(para_birimi.upper())


def kur_listesi() -> dict:
    """Sadece EUR ve USD kurlarını döndürür — UI için."""
    kurlar = get_kurlar()
    return {k: kurlar[k] for k in ('EUR', 'USD', 'GBP') if k in kurlar}
