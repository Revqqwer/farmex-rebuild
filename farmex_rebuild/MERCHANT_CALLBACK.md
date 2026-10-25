# Pazar dış callback kapısı

Sonraki reached-tail modeli enable1yazısını ayrı koşulla planlar:
[ROUTE_RESUME.md](ROUTE_RESUME.md). Tam rota bitişi veya otomatik global capture değildir.

18 Ekim 2026: `merchant_callback.py`, `004230d8` normal selector yolunu kendi
gözlemleri üzerinde modeller. SELL/BUY iç phase motorlarını çağırıp çağırmama
kararıdır; native callback veya helper çağrısı değildir. Daha önceki caller
reachability ve `004eb2c4` rota yardımcısının iç etkileri açık kalır.

Kaynak sırası:

1. Master BYTE561f60sıfırsa çık.
2. Lock BYTE561f6fnonzero ise çık.
3. Route-pending BYTE568d81nonzero ise `004eb2c4(5687a8)` normal dönüşü gerekir.
4. Master561f60yeniden okunur;0ise çık. Route helper çağrılmadığında da taze okuma gerekir.
5. Enable561f6c taze okunur;0ise çık.
6. Object+0DWORD ilk okuma1ise SELL00420efc. Değilse ikinci taze okuma2ise
   BUY004220c8. İkinci okuma bilinmiyorsa ilk değerle doldurulmaz.

Örneğin `(2,1)` mode dizisi BUY çağırmaz; ilk2SELLdeğildir, ikinci1BUYdeğildir.
`(0,2)` ise BUY seçer. İkinci mode örneği SELL1dalında okunmaz. Post-route
master/enable önceki entry değerlerinden veya helper dönüşünün kendisinden
üretilmez; yardımcı global'ları değiştirmiş olabilir.

`tick_merchant_callback` typed runner'a yalnız seçilen kind tutarlıysa geçer.
Kind uyuşmazlığı yerel API hatasıdır; engine'i sessizce diğer türe çevirmez.
Kapı skip/gap ise phase tick yapılmaz. Snapshot factory verilirse yalnız phase
yardımcısına gerçekten erişildiğinde bir kez değerlendirilir; diğer aşamaların
girdilerini erken parse etmez. Bu kendi lazy adapter sözleşmesidir. Normal
snapshot örneği doğrudan da verilebilir; önceden oluşturulmuşsa onun constructor
doğrulaması callback kapısından önce gerçekleşmiş olur.

`RouteStartDecision.state.globals[561f6c]` içindeki reset0explicit post-enable
örneği olarak verildiğinde callback skip olur, aktif own MerchantRunner bile
phase ilerletmez. Tekrar1olması için ayrı yeni gözlem gerekir. Süre geçti diye
enable uydurulmaz. Bu global'in native restore producer'ı veya bütün rota→pazar
geri dönüş döngüsü henüz doğrulanmadı. UI otomatik bu adapter'a taşınmadı;
Workbench'in doğrudan normal phase denemeleri ayrı kalır.

Geniş `test_merchant_sell_flow.py` senaryosundaki22phase çağrısı şimdi bu dış
adapter'dan geçer. Her invocation'daki eligible byte/mode değerleri açık sabit
own fixture'lardır; oyundan yakalanmış global örnekler değildir. Senaryonun
kapanış/session/slot üç yerel kaydı ve verilen yanıt/helper dönüşü sınırları sürer.

## Kanıt ve test

`work/audit_merchant_callback.py`, iki hash'li dosyada **66 talimat kaydının**
baytlarını doğruladı. Tüm gate ve reread callsite'ları ayrı anchor'lardır.
Eski route helper004eb2a8, güncel004eb2c4olduğu için bu çağrı opaque rolüyle
normalize edilir; iç gövde/ABI eşdeğerliği iddia edilmez. Rapor:
`outputs/FarmexBot_pazar_callback_kod_kaniti.json`.
Ghidra statik kanıtıdır; REA Evidence veya native yürütme değildir. Örtüşen
instruction kayıtları benzersiz fonksiyon tamamlanma sayısı olarak toplanmaz.

9 yeni test dahil **2024 yerel test geçti** (7.263 saniye). Gate önceliği,
helper-return gap'i, taze post-global/mode okumaları, lazy snapshot değerlendirmesi,
kind uyuşmazlığı ve route-start enable resetinin callback'i bastırması sınandı.
Birleşik model doğrulaması da geçti. UI değiştirilmedi; UI smoke tekrarlanmadı.
Native global/helper/callback etkileri ve canlı uyumluluk açık kalır.
