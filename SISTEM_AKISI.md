# Erlau App — Sistem Akışı

> Düzenlemek için: [mermaid.live](https://mermaid.live) adresine gidip aşağıdaki kodu yapıştır.
> GitHub bu dosyayı otomatik render eder.

---

## 0. Portal — Ana Giriş Sayfası

```mermaid
flowchart TD
    A([🌐 Kullanıcı: IP:5000]) --> B[🏠 Portal Ana Sayfa]

    B --> C[🛒 Satınalma]
    B --> D[🏭 Üretim]
    B --> E[🔧 Bakım]
    B --> F[🚚 Sevkiyat\n⚠️ Yakında]
    B --> G[📋 Planlama]

    C --> C1[Login → Satınalma Paneli]
    D --> D1[Login → Üretim Paneli]
    E --> E1[Login → Bakım Paneli]
    F --> F1[Devre Dışı]
    G --> G1[Login → Planlama Paneli]
```

---

## 1. Modüller Arası İletişim

```mermaid
flowchart LR
    PL([📋 Planlama]) -->|Haftalık Üretim Planı| UR([🏭 Üretim])
    UR -->|Malzeme İhtiyacı| SA([🛒 Satınalma])
    UR -->|Bakım Talebi| BK([🔧 Bakım])
    SA -->|Onaylanan Sipariş| MH([💰 Muhasebe])
    BK -->|Bakım Raporu| GM([👔 GM Dashboard])
    UR -->|Üretim Raporu| GM
    SA -->|Satınalma Raporu| GM
```

---

## 2. Satınalma Akışı (Güncel)

```mermaid
flowchart TD
    A([👤 Herhangi Bir Departman]) --> B[Yeni Talep Oluştur]

    B --> B1[Malzeme Adı Gir\nen az 3 harf]
    B1 --> B2{Malzeme\nListesinde var mı?}
    B2 -- Evet --> B3[Listeden Seç\nBirim otomatik gelir]
    B2 -- Hayır --> B4[Manuel Gir]
    B3 --> C
    B4 --> C

    B --> B5[Proje/Makine/Ürün Gir\nen az 3 harf]
    B5 --> B6{Ürün\nListesinde var mı?}
    B6 -- Evet --> B7[Listeden Seç]
    B6 -- Hayır --> B8[Otomatik Ürün Listesine Ekle]
    B7 --> C
    B8 --> C

    C[(Talep: bekliyor)] --> D{Satınalma Paneli}

    D -- İptal --> E[(Talep: iptal)]
    D -- Sil --> E2[(Talep Silindi)]
    D -- Onayla --> F[(Talep: onaylandi)]

    F --> G[Fiyatlandırma]
    G --> G1[Tedarikçi Seç\nyoksa Yeni Tedarikçi Ekle]
    G1 --> G2[Teklif İste Butonu]
    G2 --> G3[2-3 Tedarikçi Seç]
    G3 --> G4[Teklif No Üret\nTKL-2026-00001]

    G4 --> H{Teklif Kaynağı}
    H -- PDF/Excel Yükle --> H1[🤖 AI: Fiyat Oku\nTedarikçi, Fiyat, Vade Çıkar]
    H -- Manuel Gir --> H2[El ile Fiyat Gir]
    H1 --> I
    H2 --> I

    I[Teklifler Karşılaştır\nYan Yana Göster] --> J[En Uygun Teklifi Seç]
    J --> K[(Talep: fiyatlandirildi)]

    K --> L[Sipariş Özeti\nExcel Export → Tedarikçiye Gönder]
    L --> M[Yolda İşaretle]
    M --> N[(Talep: yolda)]
    N --> O[Teslim Alındı]
    O --> P[(Talep: teslim_alindi)]

    P --> Q[Muhasebe: Fatura Yükle]
    Q --> R[🤖 AI Fatura Analizi]
    R --> S[Talep Kalemleri ile Eşleştir]
    S --> T{Eşleşme}
    T -- OK --> U[(Fatura: onaylandi)]
    T -- Fark var --> V[Manuel Düzelt]
    V --> U
    U --> W[(Fatura: odendi)]
```

---

## 3. Üretim Akışı

```mermaid
flowchart TD
    PL([📋 Planlama]) -->|Haftalık Plan Yayınla| A

    A[Üretim Paneli] --> B[Bugünkü Plan\nİstasyon bazlı hedefler]

    B --> C[Üretim Adedi Gir\nPlanlanan gösterilir\nGerçekleşen girilir]
    C --> D[(Üretim Kaydı\nGerçekleşen Adet)]

    B --> E[Arıza Kaydı Oluştur\nİstasyon, Saat, Açıklama]
    E --> F[(Arıza Kaydı)]

    D --> G[📊 Üretim Raporu\nPlanlanan vs Gerçekleşen]
    F --> G

    G --> H{Rapor Erişimi}
    H --> H1[Üretim Personeli\nKendi girişleri]
    H --> H2[Üretim DY\nTüm kayıtlar]
    H --> H3[Tüm DY + GM\nRaporlar - Salt Okunur]

    subgraph YETKİ["👥 İstasyon Tanımlama"]
        I[Üretim DY\nİstasyon Ekle/Düzenle]
        J[Üretim DY\nPersonel Ata]
    end
```

---

## 4. Bakım Akışı

```mermaid
flowchart TD
    A[Bakım Paneli] --> B[Dashboard\nBugünkü Bakımlar\nYaklaşan Periyodikler]

    B --> C[Günlük Bakım Kaydı\nMakine, Yapılan İşler, Süre]
    C --> D[(Bakım Kaydı)]

    B --> E[Periyodik Bakım Takvimi\nMakine bazlı, gün sayısı]
    E --> F{Vade Geldi mi?}
    F -- Evet --> G[⚠️ Uyarı Göster\nBakım Yapılmalı]
    G --> C

    B --> H[Yapılacaklar Listesi\nAçık bakım talepleri]

    D --> I[📊 Bakım Raporu\nMakine geçmişi\nMTBF analizi]
    I --> J{Rapor Erişimi}
    J --> J1[Bakım Personeli\nKendi kayıtları]
    J --> J2[Tüm DY + GM\nRaporlar - Sol Menü]

    subgraph MAKİNE["🔧 Makine Yönetimi"]
        K[Makine Ekle/Düzenle\nBakım Planı Tanımla]
    end
```

---

## 5. Planlama Akışı

```mermaid
flowchart TD
    A([📋 Tedarik Zinciri / Planlama DY]) --> B[Yeni Haftalık Plan Oluştur]

    B --> C[Ürün Seç\nİş İstasyonu Seç]
    C --> D[Günlere Adet Dağıt\nPzt-Sal-Çar-Per-Cum-Cmt]
    D --> E[Plan: Taslak]
    E --> F[Aktif Et → Yayınla]
    F --> G[(Plan: Aktif)]

    G --> H[Üretim Modülü\nPlanı Görür]
    H --> I[Üretim Personeli\nGerçekleşen Girer]
    I --> J[📊 Plan vs Gerçekleşen\nGünlük Rapor]

    J --> K{Haftalık Özet}
    K --> K1[Genel Müdür Dashboard]
    K --> K2[Tüm Departman Yöneticileri]
```

---

## 6. Kullanıcı Rolleri ve Erişim (Güncel)

```mermaid
flowchart LR
    subgraph ROLLER["👥 Roller"]
        P([personel])
        DY([departman_yoneticisi])
        SA([satinalma])
        MH([muhasebe])
        BK([bakim])
        UR([uretim])
        PL([planlama])
        AD([admin])
        GM([gm])
    end

    subgraph SATINALMA["🛒 Satınalma"]
        S1[Talep oluştur]
        S2[Talep onayla/iptal/sil]
        S3[Fiyatlandır & Teklif]
        S4[Tedarikçi yönet]
        S5[Malzeme/Ürün listesi - Admin]
    end

    subgraph URETIM["🏭 Üretim"]
        U1[Üretim adedi gir]
        U2[Arıza kaydı]
        U3[İstasyon tanımla - DY]
        U4[Üretim raporu]
    end

    subgraph BAKIM["🔧 Bakım"]
        B1[Bakım kaydı gir]
        B2[Bakım planı]
        B3[Makine yönet]
        B4[Bakım raporu]
    end

    subgraph PLANLAMA["📋 Planlama"]
        L1[Üretim planı oluştur]
        L2[Plan yayınla]
    end

    P --> S1
    SA --> S1
    SA --> S2
    SA --> S3
    SA --> S4
    AD --> S5

    UR --> U1
    UR --> U2
    DY --> U3
    DY --> U4
    GM --> U4

    BK --> B1
    BK --> B2
    BK --> B3
    BK --> B4
    DY --> B4
    GM --> B4

    PL --> L1
    PL --> L2
    DY --> L1
```

---

## 7. Veri Modeli (Güncel)

```mermaid
erDiagram
    User {
        int id
        string name
        string email
        string role
        int department_id
    }
    Malzeme {
        int id
        string stok_kodu
        string malzeme_adi
        string birim
        string kategori
    }
    Urun {
        int id
        string urun_kodu
        string urun_adi
        string proje
        string makine
    }
    TeklifGrubu {
        int id
        string teklif_no
        int talep_kalem_id
        string durum
    }
    TeklifKalem {
        int id
        int grup_id
        int tedarikci_id
        float birim_fiyat
        string kaynak
        bool secildi
    }
    IsIstasyonu {
        int id
        string istasyon_kodu
        string istasyon_adi
    }
    UretimPlani {
        int id
        string plan_no
        int hafta
        int yil
        string durum
    }
    UretimPlaniSatir {
        int id
        int plan_id
        int urun_id
        int istasyon_id
        date tarih
        int planlanan_adet
    }
    UretimKaydi {
        int id
        int istasyon_id
        int urun_id
        date tarih
        int gerceklesen_adet
        int fire_adet
    }
    ArizaKaydi {
        int id
        int istasyon_id
        date tarih
        string durum
    }
    Makine {
        int id
        string makine_kodu
        string makine_adi
    }
    BakimPlani {
        int id
        int makine_id
        int periyot_gun
        date sonraki_bakim_tarihi
    }
    BakimKaydi {
        int id
        int makine_id
        string bakim_turu
        date tarih
    }

    TalepFormu ||--o{ TalepKalem : "içerir"
    TalepKalem ||--o{ TeklifGrubu : "teklifler"
    TeklifGrubu ||--o{ TeklifKalem : "tedarikçi teklifleri"
    UretimPlani ||--o{ UretimPlaniSatir : "günlük satırlar"
    UretimPlaniSatir ||--o{ UretimKaydi : "gerçekleşen"
    IsIstasyonu ||--o{ UretimKaydi : "istasyon"
    Makine ||--o{ BakimPlani : "plan"
    Makine ||--o{ BakimKaydi : "geçmiş"
    Urun ||--o{ UretimPlaniSatir : "üretilen"
```

---

## 8. Talep Durumları (Mevcut)

```mermaid
stateDiagram-v2
    [*] --> bekliyor : Talep oluşturuldu
    bekliyor --> onaylandi : Satınalma onayladı
    bekliyor --> iptal : İptal edildi
    onaylandi --> fiyatlandirildi : Teklif seçildi
    fiyatlandirildi --> yolda : Sipariş verildi
    yolda --> teslim_alindi : Teslim alındı
    onaylandi --> iptal : İptal edildi
    fiyatlandirildi --> iptal : İptal edildi
```

---

## 9. Fatura Durumları (Mevcut)

```mermaid
stateDiagram-v2
    [*] --> bekliyor : PDF yüklendi
    bekliyor --> onaylandi : Eşleşme tamam
    bekliyor --> iptal : İptal
    onaylandi --> odendi : Ödeme yapıldı
    onaylandi --> iade : İade
    odendi --> [*]
```
