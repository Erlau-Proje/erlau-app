"""8D Raporu PDF üretici — ReportLab"""
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Spacer, Paragraph
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import mm
import io

YESIL = colors.HexColor('#16a34a')
KOYU = colors.HexColor('#1e293b')
GRI = colors.HexColor('#f8fafc')
KIRMIZI = colors.HexColor('#dc2626')
MAVI = colors.HexColor('#1d4ed8')

def _stil(font='Helvetica', size=9, bold=False, color=KOYU):
    return ParagraphStyle(
        'x',
        fontName='Helvetica-Bold' if bold else font,
        fontSize=size,
        textColor=color,
        leading=size + 3,
    )


def _bolum_baslik(baslik, renk=YESIL):
    return [[Paragraph(f'<b>{baslik}</b>', _stil(size=10, bold=True, color=colors.white))]]


def _bolum_tablo(baslik, satirlar, renk=YESIL):
    """Başlıklı, iki sütunlu label/value tablosu."""
    data = _bolum_baslik(baslik, renk)
    for label, val in satirlar:
        data.append([
            Paragraph(f'<b>{label}</b>', _stil(size=8, bold=True)),
            Paragraph(str(val or '—'), _stil(size=8)),
        ])
    t = Table(data, colWidths=[50*mm, 120*mm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), renk),
        ('SPAN', (0, 0), (1, 0)),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, GRI]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    return t


def build_sekizd_pdf(s) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                             leftMargin=15*mm, rightMargin=15*mm,
                             topMargin=15*mm, bottomMargin=15*mm)
    story = []
    styles = getSampleStyleSheet()

    # Başlık
    baslik_data = [
        [Paragraph('<b>8D — DÜZELTICI FAALİYET RAPORU</b>', _stil(size=14, bold=True, color=colors.white)),
         Paragraph(f'<b>{s.sekizd_no}</b>', _stil(size=12, bold=True, color=colors.white))],
    ]
    baslik_t = Table(baslik_data, colWidths=[120*mm, 60*mm])
    baslik_t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), KOYU),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(baslik_t)
    story.append(Spacer(1, 4*mm))

    # Header bilgileri
    story.append(_bolum_tablo('RAPOR BİLGİLERİ', [
        ('Tedarikçi', s.tedarikci.name if s.tedarikci else ''),
        ('Ürün Kodu / Adı', f"{s.urun_kodu or ''} / {s.urun_adi or ''}"),
        ('Tarih', s.tarih.strftime('%d.%m.%Y') if s.tarih else ''),
        ('Revizyon', s.revizyon_no or '1'),
        ('Durum', {'taslak': 'Taslak', 'gonderildi': 'Gönderildi', 'kapali': 'Kapalı'}.get(s.durum, s.durum)),
    ], renk=KOYU))
    story.append(Spacer(1, 3*mm))

    # D1
    story.append(_bolum_tablo('D1 — EKİP OLUŞTURMA', [
        ('Ekip Lideri', s.d1_ekip_lideri),
        ('Ekip Üyeleri', s.d1_ekip_uyeleri),
    ]))
    story.append(Spacer(1, 3*mm))

    # D2
    story.append(_bolum_tablo('D2 — PROBLEM TANIMI (5W2H)', [
        ('Problem Özeti', s.d2_problem_ozeti),
        ('Kim?', s.d2_kim),
        ('Ne?', s.d2_ne),
        ('Nerede?', s.d2_nerede),
        ('Ne Zaman?', s.d2_ne_zaman),
        ('Neden?', s.d2_neden),
        ('Nasıl?', s.d2_nasil),
        ('Ne Kadar?', s.d2_ne_kadar),
        ('İlk Tespit', s.d2_ilk_tespit),
    ], renk=MAVI))
    story.append(Spacer(1, 3*mm))

    # D3
    story.append(_bolum_tablo('D3 — GEÇİCİ ÖNLEMLER', [
        ('Önlem', s.d3_onlem),
        ('Sorumlu', s.d3_sorumlu),
        ('Tarih', s.d3_tarih.strftime('%d.%m.%Y') if s.d3_tarih else None),
        ('Etkinlik Doğrulama', s.d3_etkinlik),
    ]))
    story.append(Spacer(1, 3*mm))

    # D4
    story.append(_bolum_tablo('D4 — KÖK NEDEN ANALİZİ', [
        ('Kök Neden', s.d4_kok_neden),
        ('Analiz Metodu', {'5why': '5 Why', 'balik_kilcigi': 'Balık Kılçığı', 'diger': 'Diğer'}.get(s.d4_analiz_metod or '', s.d4_analiz_metod)),
    ], renk=KIRMIZI))
    story.append(Spacer(1, 3*mm))

    # D5
    story.append(_bolum_tablo('D5 — KALICI DÜZELTİCİ AKSİYON', [
        ('Aksiyon', s.d5_aksiyon),
    ]))
    story.append(Spacer(1, 3*mm))

    # D6
    story.append(_bolum_tablo('D6 — UYGULANMASI', [
        ('Uygulama', s.d6_uygulama),
        ('Tarih', s.d6_tarih.strftime('%d.%m.%Y') if s.d6_tarih else None),
        ('Doğrulama', s.d6_dogrulama),
    ]))
    story.append(Spacer(1, 3*mm))

    # D7
    story.append(_bolum_tablo('D7 — TEKRARı ÖNLEYİCİ TEDBİRLER', [
        ('Tedbirler', s.d7_onleyici),
    ]))
    story.append(Spacer(1, 3*mm))

    # D8
    story.append(_bolum_tablo('D8 — EKİP TAKDİRİ', [
        ('Takdir Notu', s.d8_tadir),
    ], renk=YESIL))

    # İmza alanı
    story.append(Spacer(1, 8*mm))
    imza_data = [
        ['Hazırlayan', 'Onaylayan', 'Tedarikçi'],
        ['\n\n\n', '\n\n\n', '\n\n\n'],
        ['İmza / Tarih', 'İmza / Tarih', 'İmza / Tarih'],
    ]
    imza_t = Table(imza_data, colWidths=[60*mm, 60*mm, 60*mm])
    imza_t.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(imza_t)

    doc.build(story)
    return buf.getvalue()
