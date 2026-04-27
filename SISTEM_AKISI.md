# Erlau App — Sistem Akışı

> Düzenlemek için: [mermaid.live](https://mermaid.live) adresine gidip aşağıdaki kodu yapıştır.  
> VS Code'da canlı önizleme: `Markdown Preview Mermaid Support` eklentisini kur.  
> GitHub bu dosyayı otomatik render eder.

---

## 1. Ana İş Akışı

```mermaid
flowchart TD
    A([👤 Personel Girişi]) --> B[Yeni Talep Oluştur]
    B --> C[Talep Kalemleri Gir\nmalzeme, miktar, kullanım amacı]
    C --> D[(Durum: bekliyor)]

    D --> E{Satınalma\nPaneli}
    E -- İptal --> F[(Durum: iptal)]
    E -- Onayla --> G[(Durum: onaylandi)]

    G --> H[Fiyatlandırma\ntedarikçi, fiyat, vade, termin]
    H --> I[(Durum: fiyatlandirildi)]

    I --> J[Sipariş Özeti\nExcel Export → Tedarikçiye Gönder]
    J --> K[Yolda İşaretle]
    K --> L[(Durum: yolda)]

    L --> M[Teslim Alındı İşaretle]
    M --> N[(Durum: teslim_alindi)]

    N --> O[Muhasebe:\nFatura PDF Yükle]
    O --> P[AI Fatura Analizi\nürün, fiyat, tarih çıkar]
    P --> Q[Talep Kalemleriyle Eşle]
    Q --> R{Eşleşme\nDurumu}

    R -- Eşleşti --> S[(Fatura: onaylandi)]
    R -- Fiyat/Ürün Farkı --> T[Manuel Düzelt]
    T --> S

    S --> U{Dövizli\nFatura mı?}
    U -- Evet --> V[Kur Farkı Hesapla\nTCMB kuru ile]
    V --> W[Kur Farkı Faturası Oluştur]
    W --> X[(Fatura: odendi)]
    U -- Hayır --> X
```

---

## 2. Kullanıcı Rolleri ve Yetkileri

```mermaid
flowchart LR
    subgraph ROLLER["👥 Roller"]
        P([personel])
        DY([departman_yoneticisi])
        SA([satinalma])
        MH([muhasebe])
        AD([admin])
        GM([gm])
    end

    subgraph YETKILER["🔐 Yetkiler"]
        T1[Talep oluştur]
        T2[Kendi taleplerini gör]
        T3[Departman taleplerini gör]
        T4[Tüm talepler]
        T5[Onayla / İptal]
        T6[Fiyatlandır]
        T7[Sipariş yönet\nyolda, teslim]
        T8[Fatura yönet]
        T9[Kullanıcı yönet]
        T10[Tedarikçi yönet]
        T11[GM Dashboard\nanalitik]
        T12[Raporlar]
    end

    P --> T1
    P --> T2

    DY --> T1
    DY --> T2
    DY --> T3

    SA --> T4
    SA --> T5
    SA --> T6
    SA --> T7
    SA --> T10
    SA --> T12

    MH --> T8
    MH --> T12

    AD --> T4
    AD --> T5
    AD --> T6
    AD --> T7
    AD --> T8
    AD --> T9
    AD --> T10
    AD --> T12

    GM --> T4
    GM --> T11
    GM --> T12
```

---

## 3. Talep Durumları

```mermaid
stateDiagram-v2
    [*] --> bekliyor : Talep oluşturuldu
    bekliyor --> onaylandi : Satınalma onayladı
    bekliyor --> iptal : Satınalma iptal etti
    onaylandi --> fiyatlandirildi : Fiyatlandırma yapıldı
    fiyatlandirildi --> yolda : Tedarikçiye sipariş verildi
    yolda --> teslim_alindi : Malzeme teslim alındı
    onaylandi --> iptal : İptal edildi
    fiyatlandirildi --> iptal : İptal edildi
```

---

## 4. Fatura Durumları

```mermaid
stateDiagram-v2
    [*] --> bekliyor : Fatura PDF yüklendi
    bekliyor --> onaylandi : Eşleşme tamam, onaylandı
    bekliyor --> iptal : İptal edildi
    onaylandi --> odendi : Ödeme yapıldı
    onaylandi --> iade : İade edildi
    odendi --> [*]
```

---

## 5. Modüller ve Veri Modeli

```mermaid
erDiagram
    User {
        int id
        string name
        string email
        string role
        int department_id
    }
    Department {
        int id
        string name
    }
    TalepFormu {
        int id
        string siparis_no
        int talep_eden_id
        int department_id
        string durum
        datetime created_at
    }
    TalepKalem {
        int id
        int talep_id
        string malzeme_adi
        float br_fiyat
        string para_birimi
        int tedarikci_id
    }
    Tedarikci {
        int id
        string name
        string email
        string para_birimi
    }
    Fatura {
        int id
        string fatura_no
        int tedarikci_id
        string durum
        string fatura_turu
        float fatura_kuru
        float odeme_kuru
    }
    FaturaKalem {
        int id
        int fatura_id
        int talep_kalem_id
        string eslesme_durumu
    }

    User }o--|| Department : "çalışır"
    TalepFormu ||--o{ TalepKalem : "içerir"
    TalepFormu }o--|| User : "talep eden"
    TalepFormu }o--|| Department : "ait"
    TalepKalem }o--|| Tedarikci : "tedarikçi"
    Fatura }o--|| Tedarikci : "kesilen"
    Fatura ||--o{ FaturaKalem : "içerir"
    FaturaKalem }o--o| TalepKalem : "eşleşir"
```
