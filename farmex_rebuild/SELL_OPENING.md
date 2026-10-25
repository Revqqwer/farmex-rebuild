# Satış pazarının native açılış operandları

18 Ekim 2026: `merchant_sell_open.py`, `0041d518` yardımcısının operandlarını ve
phase4caller'ını kendi gözlemleri üzerinde planlar. Bu helper doğrudan paket
formatter'ı değildir. Yeni6804vb.kayıt uydurulmaz; indirect native çağrı planı
oluşur. Gerçek fonksiyon çağrısı veya bellek erişimi yapılmaz.

`work/audit_sell_open.py`, iki ikilide34'er helper talimatı ve caller dalından
toplam **174 talimat kaydı** baytını/clock import kimliğini doğrular. Rapor
`outputs/FarmexBot_satis_acilis_kod_kaniti.json`. Ghidra statik kanıtıdır;
REA Evidence veya native yürütme değildir. Önceki geniş auditlerle örtüşebilen
kayıtlar benzersiz toplam olarak eklenmez.

## Helper sırası

Global slot okumaları, protected getter sonuçları ve direct okumalar ayrı
ordered dizilerdir. Aynı adresin tekrar okunması aynı değer varsayılmaz.

```text
global[553e80] -> protected root
global[554140] -> protected(root + offset) -> container
global[554144] -> protected(container + offset) -> argument

fresh global[553e80] -> direct fresh root
fresh global[554140] -> direct(root + fresh offset) -> ECX context
global[554200] -> EAX method offset
direct[ECX] -> vtable
direct[vtable + EAX] -> EDX target
PUSH 1; PUSH argument; CALL EDX
```

Toplam6global/3protected/4direct DWORD gözlemi gerekir. Adres toplamları DWORD'da
sarılır. Eksik ikinci root, ilk protected root ile doldurulmaz. Adres/sıra
uyuşmazlığı hata, bilinmeyen değer açık gap'tir.

Plan physical `push_order=(1,argument)` ve callee girişindeki stack argümanları
`(argument,1)` ayrımını korur; EAX, ECX, EDX ayrıca kaydedilir. Merchant-object
parametresi helper gövdesinde okunmaz. Callee'nin8bayt argümanı temizlemesi
source epilogue için beklenen sözleşmedir; ABI doğrulaması değildir. Target0bile
ham operand olarak kaydedilebilir; kaynakta olmayan null guard eklenmez.
Executable-page veya protected read/protection etkisinin başarısı kanıtlanmaz.

## Phase4 frame ve runner

Prepared count signed DWORD olarak<=0ise source stop/string bloğuna gider.
Ayrı normal-return gözlemi gerekir; native stop/UI etkileri uygulanmaz ve açma
çağrı planı oluşmaz. Pending/clock alanları bu dalda uydurularak yazılmaz.
Bound runner'ın normal span sonrası `no_sale_slots` ile durması kendi
politikasıdır; `0040ae0c` iç etkilerinin emülasyonu değildir.

Pozitif count dalında `SellOpeningFrame` sırası: pending BYTE+0x48=1 → tek açık
GetTickCount'ın sıfır genişletilerek QWORD+0x50'ye yazılması → `0041d518`
operandlarının tamamlanması → ayrı `helper_returned=True` → phase DWORD+4artışı.
Operandların bilinmesi normal dönüş değildir. Dönüş örneği verilse de eksik
operand bypass edilemez. Accepted state girişte kalırken prefix prospective
gösterilir; bilinen clock/okuma örnekleri frame içinde değiştirilemez. Bu kendi
replay'imizin devamıdır; native thread/callback dondurma veya reentrancy değildir.

`MerchantSnapshot.sell_opening_execution`, market-slot sayacıyla eşleşmeyi ister.
Gap'te phase4ilerlemez; complete own helper-return örneği phase5'e aktarılır.
Bekleme/başarı UI tail'i ve tüm source-clock davranışı bu bağla doğrulanmış
sayılmaz. Workbench henüz bu operand girişi için kontrol sunmaz; API kapsamıdır.

## Doğrulama

Güncel devam: [SELL_OPEN_WAIT.md](SELL_OPEN_WAIT.md), verilen dört UI-span
dönüşüyle birleşik modeli aşama 6 sınırına taşır. Native UI çalıştırılmaz.
Aşağıdaki 1879 test sayısı opening değişikliğinin tarihsel çalıştırmasıdır.

14yeni test; bağımsız root/offset, adres uyuşmazlığı, DWORD wrap, target0,
pending/clock, operand/return ayrımı, partial fill, signed count, empty-span ve
runner sayacı/phase bağını kapsar. **1879 test geçti** (9.146 saniye). Önceki
maliyet/hazırlık gizli UI testleri yeniden geçti; UI düzenlenmedi ve genel smoke
tekrar çalıştırılmadı.

`work/verify_sell_model_flow.py` own profil→liste→cost→session→slot→opening
operandları ve ayrı verilen helper-return üzerinden phase5beklemesine ilerler.
Verilen `68 07` örneğinin offset6DWORD actor eşleşmesiyle pending'i temizlemesi
de sınanır; phase5native/UI tail'i çalıştırılmaz. Queue iki kayıttır; opening
için ekstra paket eklenmez. Rapor `outputs/FarmexBot_satis_birlesik_model_testi.json`.

Örnekteki0x7000target yalnız fixture verisidir; native call yapılmadı. Gerçek
target/ABI, oyun actor/context okuması, loader erişimi ve canlı uyumluluk açık.
Oyun read/write/protection değişimi veya gönderim yapılmaz; readonly metadata
erişim engelini aşan yol eklenmez.
