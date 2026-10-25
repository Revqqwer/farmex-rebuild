# Satış döngüsünün kapatma caller'ı

18 Ekim 2026: `merchant_sell_close.py`, `00420efc` içindeki erişilmiş aşama 0
dalını (`00420f9e..0042104a`) kendi gözlemleri üzerinde planlar. Fonksiyonun
bundan önceki coin alarm dalı bu modelin dışında kalır. Native protected getter,
kuyruk veya oyun çağrısı yapılmaz. Workbench için giriş kontrolleri henüz yoktur.

## Kontrol ve sıra

Önce global 553e7c okunur; değer `0045dc44` protected getter argümanıdır.
Verilen EAX sonucu + taze global 554148 adresinden `0045dbdc` sonucu istenir.
Yalnız AL==1 açık pazar dalına girer; AL=2 veya255 açık sayılmaz. Sonucun üst
24 biti bu kararda kullanılmaz. Eksik getter sonucu kapalı pazar sayılmaz.

Açık değilse phase +4 artar; mevcut pending +18 ve damga +20 değişmez, saat
ve queue girdisi gerekmez. Açıksa global 553e7c yeniden okunup protected getter
yeniden gözlenir; önceki kök yeniden kullanılmaz. Taze global 55414c offset'i
ile ikinci byte getter sonucu AL==1 ise kapatma subtype27, diğer bütün AL
değerlerinde subtype02 olur. Ham getter EAX'ları DWORD, adres toplamları low32'dir.

Diskteki 50dad6 WORD seed'i `6802` olarak doğrulandı. İkinci test1ise ikinci
bayt27 olur. Ardından kaynak sıra:

1. Pending BYTE +18 =1.
2. Ayrı GetTickCount; DWORD sıfır genişletilip QWORD +20'ye yazılır.
3. `004c7710` için iki bayt ve delay0 ile kendi yerel enqueue modeli.
4. Ayrı enqueue-helper normal dönüşü.
5. Phase +4 artışı; aşama1.

Queue helper'ın kendi tick'i caller tick'inden ayrıdır. Connection gate0 kendi
queue modelinde kayıt eklemeyen normal yoldur; bu durumda da ayrı helper dönüşü
gerekir. Gate nonzero ise yerel kopya, normal dönüş gözlemi eksikken prospective
queue'da kalır; sonraki adımda aynı kayıt yeniden eklenmez. Bilinen örnekler
aynı frame'de değiştirilemez. Completed frame idempotent'tir. Bunlar native heap
ve callback devamı değil, kendi replay sözleşmelerimizdir.

`MerchantSnapshot.sell_close_execution` bağı, varsa ayrı `currently_open`
bayrağının probe ile eşleşmesini ister. Eksik gözlem aşama0'ı bekletir. Tamamlanan
frame phase1 ve close damgasını runner'a taşır. Kapanış niyeti üretmek oyun
eylemi veya ACK değildir. Aşama1'in ayrı bound bekleme yolu aşağıda açıklanır;
legacy girişler kullanıldığında eski normal-clock politika ayrı devam eder.

## Doğrulama

`work/audit_sell_close.py` ilk aşama0 çalışmasında iki sabit hash'li ikilide **96 talimat kaydının**
baytlarını, seed'i ve GetTickCount import kimliğini doğruladı. Getter callsite'ları,
fresh global okumaları, AL karşılaştırması, pending/clock/queue/phase sırası ayrıca
kontrol edildi. Getter iç etkileri/ABI ve gerçek queue execution bu kanıt değildir.
Rapor `outputs/FarmexBot_satis_kapatma_kod_kaniti.json`.
Ghidra statik kanıtıdır; REA Evidence değildir. Örtüşen audit kayıtları benzersiz
fonksiyon tamamlanması veya toplam kapsam olarak toplanmaz.

10 yeni test dahil ilk çalıştırmada **1949 test geçti** (6.822 saniye). Bir ayrı own integration
testi close frame → verilen eşleşen kapatma yanıtı → başlangıç damgasından
hazırlık kapısına ilerler. Bu senaryoda tek yerel close kaydı vardır; queue drain
edilmez. Sonraki çalışma geniş `test_merchant_sell_flow.py` senaryosunu da bu frame'e
bağladı; güncel kapsam aşağıdadır. UI bu aşamada
değişmedi; yeni UI smoke çalıştırılmadı. Canlı uyumluluk açık kalır.

## Aşama 1 beklemesi ve birleşik akış

`merchant_sell_close_wait.py`, `0042104f..0042111a` dalını modeller.
Pending BYTE +18 sıfırsa saat/damga gerekmeden phase2 yazısı planlanır.
Nonzero ise ayrı GetTickCount sıfır genişletilir, tam close QWORD +20 çıkarılır;
signed64 fark >=10000 karşılaştırması kullanılır. DWORD saat sarması negatif
farkla bekleyebilir; unsigned32 elapsed'e çevrilmez.

Timeout yolunda önce `00421091..004210fd` mesaj/cleanup span'ının, sonra
`0040ae0c(0x561f34,0)` yardımcısının normal dönüşü ayrı gerekir. Stop dönüşü eksik
mesaj dönüşünü atlayamaz. Bu helper'lar çağrılmaz. Plan tamamlanınca runner'ın
`close_timeout` ile durması kendi politikasıdır; kaynak helper iç etkileri değildir.

`MerchantSnapshot.sell_close_wait_inputs` bağı pending bayrağı tutarlılığını ve
yalnız pending dalında okunan close damgasının caller phase damgasıyla eşleşmesini
ister. Eksik gözlemde legacy saate düşmez. Clear branch aşama2'ye geçer; runner'ın
o sırada tuttuğu monotonic phase zamanı kendi bookkeeping alanıdır, kaynakta yeni
başlangıç damgası yazısı olarak yorumlanmaz. Hazırlık başlangıcı ayrı reply +8
alanından gelir. Workbench henüz bu phase0/phase1 gözlemleri için kontrol sunmaz.

Geniş birleşik model artık close frame'in accepted pending değerini reply state'e
taşır; önce raw close-wait gate'ini, sonra verilen eşleşen close yanıtını ve clear
phase geçişini kullanır. Aynı yerel queue close→session→slot boyunca korunur:
`6802`, `6801`, `68034d0000000200320000000000`. Üç kayıt drain/gönderim veya üç
başarılı oyun işlemi değildir. Native opening/UI span dönüşleri ve incoming yanıt
byte'ları hâlâ açık own fixture'lardır. Sonuç phase6 timer'ın yeniden açma kararıyla
phase0'a döner; bir sonraki native kapatma döngüsü çalışmış sayılmaz.

Audit güncel olarak phase0+phase1'de **204 talimat kaydını** doğrular; eski96sayısına
eklenmez. İkinci clock import, SUB/SBB ve unsigned-low/signed-high branch, mesajdan
sonra stop ve clear pending sonrası phase artışı ayrı anchor kontrolleridir.
8 yeni testle **1957 yerel test geçti** (7.202 saniye). UI değiştirilmedi, UI smoke
tekrarlanmadı. Ortak coin alarm/epilog, protected getter ve helper iç etkileri,
native callback eşzamanlılığı ve canlı uyumluluk açık kalır.
