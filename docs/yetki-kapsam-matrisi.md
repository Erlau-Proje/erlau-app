# Yetki + Kapsam Matrisi (V1)

Bu doküman, "kim ne yapar" sorusunu sadeleştirmek için hazırlanmıştır.

## Kural

- Yetki (permission): kullanıcı ne yapabilir?
- Kapsam (scope): bunu nerede yapabilir?

Menü gösterimi için ikisi birlikte aranır:

1. Kullanıcıda ilgili permission açık olmalı.
2. Kullanıcının departmanı o modül kapsamına uygun olmalı (veya admin/gm/satınalma gibi çapraz rol olmalı).

## Modül Kapsamları

- Planlama: `Planlama` departmanı + çapraz roller
- Bakım: `Bakım` departmanı + çapraz roller
- Üretim: `Üretim` departmanı + çapraz roller
- Kalite: `Kalite` departmanı + çapraz roller
- Muhasebe: `Muhasebe` departmanı + çapraz roller + `invoice.view`
- Satınalma: permission bazlı (departmandan bağımsız)

Çapraz roller: `admin`, `gm`, `satinalma`

## Not

Bu V1 menü sadeleştirmesidir. Ekran içi butonlar ve POST işlemleri için de aynı scope yaklaşımı ayrı adımda route/template seviyesinde tamamlanmalıdır.
