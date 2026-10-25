# Kaynak Bekle ve Otur/Kalk dalları

18 Ekim 2026. `source_route_commands.py`, güncel004f276c içinde004f2a1e'den
başlayan Bekle ve erken Otur/Kalk grubunu modeller. Town ve Koordinat
karşılaştırmalarından sonra `SourceRouteStepObservation.commands` ile aynı
satır API'sine bağlanır. Önceki karşılaştırma veya Koordinat parser'ı eksikse
bu komutlara atlanmaz. Sonraki Gate Skill/Open/Gate gövdeleri artık typed
`gates` ile bağlanabilir; ayrıntı SOURCE_ROUTE_GATES.md'dedir. Diğer raw
gövdeler açık kalır; genel modeller onların native caller yollarını
tamamlamış sayılmaz.

## Bekle

004f2a1e..004f2a6c Bekle karşılaştırması/metin temizliği normal dönüşü ile
saklanan AL ayrı gözlemlerdir. Eşleşirse BYTE5f4 okunur. İlk çağrıda5f4=0ise
süre parametresi henüz parse edilmez: ayrı clock5f8'e,0ise5fc'ye yazılır,
en son5f4=1yazılır ve taze index döner.

5f4 nonzero olduğunda index/string/saniye dönüşümü span'ının normal dönüşü
ve EAX DWORD sonucu ayrıca gerekir. Saniye*1000 düşük32bitte yapılır; eşik
signed32'den64bite genişletilir. Ayrı GetTickCount DWORD sıfırla genişletilip
5f8/5fc tam QWORD damga çıkarılır; fark signed64 olarak karşılaştırılır.
Eşiğe eşit veya daha büyükse önce5f4=0, sonra5e8=0 yazılır. Negatif saniye
veya ürün taşması kaynak dalını etkiler; raw API bunları genel rota
editörünün pozitif süre kuralıyla değiştirmez. Örneğin ffffffff saniye
-1000ms eşiği,2147484 saniye -2147483296ms eşiği üretir.

## Otur/Kalk

Bekle false ise004f2b1b..004f2bcb Otur-or-Kalk karşılaştırma/cleanup span'ının
normal dönüşü ile normalize edilmiş0/1 sonucu gerekir. Bu span ilk Otur
eşleşmesinde Kalk karşılaştırmasını kısa devre eder; helper/string içeriği
burada emüle edilmez. Sonuç0ise sonraki komut gövdesi açık bırakılır.

Başlamış5f4 nonzero dalında actor ve eylem karşılaştırmaları çağrılmaz;
2000ms signed64 bekleme sonrası5f4/5e8 sırasıyla temizlenir. İlk dalda
553e7c→guarded DWORD root→taze554020 offset→guarded BYTE zinciri vardır.
AL nonzero ise taze index okunup dönülür; started veya processing değişmez.
Null/API-failure/gerçek0 provenance korunur; getter'ın EAX üst bitleri AL
testinin yerine kullanılmaz. Hiç gerçek koruma API'si veya bellek okuması yoktur.

AL0ise Otur **yeniden** karşılaştırılır ve normal dönüşü ayrı gözlemlenir;
nonzero sonucunda00465de0 normal dönüşü gerekir. Ardından Kalk ayrıca
karşılaştırılır; nonzero sonucunda00465e50 normal dönüşü gerekir. İlk group
sonucundan sonraki iki karşılaştırma sonucu türetilmez. Kaynak, taze sonuçlara
göre iki yardımcıyı da çağırabilir veya ikisini de atlayabilir; her iki
durumda normal yol ayrı clock→5f8/5fc→5f4=1ile biter. Gerçek oturma/kalkma
eylemleri çalıştırılmaz; helper dönüşü eylem başarısı değildir.

## Genel modelde adres etiketi düzeltmesi

Genel `SpecialRouteSnapshot` alanı `actor_raw_byte_55402c` adını taşıyordu.
İkili dosyanın rota yordamındaki **sekiz** actor zinciri554020 globalini
kullanıyor. Alan `actor_raw_byte_554020` olarak düzeltildi; rota UI'sinin
sentetik snapshot üreticisi ve ilgili testler güncellendi. Alanın konumu
değişmedi; keyword kullanan own çağrılar yeni adı kullanır. Yanlış global
anlamını devam ettiren bir alias eklenmedi.

Merchant scan gibi aynı eski etiketi kullanan başka alt sistemlerin kendi
kaynağı bu adımda yeniden incelenmedi ve değiştirilmedi.554020kaynak global
kimliğidir; yeni uygulamanın veya gerçek oyunun doğrulanmış offset'i değildir.

## Bağ ve kanıt

Alt planın bilinen yazıları source parent'a aktarılır; source epilogue taze
index ister. Return index eksikse ön yazılar yalnız prospective own state'de
kalır. Var olan `RouteProgressObservation.step_execution` bağı böylece bu
komutları da tüketebilir; caller'ın taze processing gate'i otomatik doldurulmaz.
UI'de yeni raw komut kontrolleri yoktur; yapılan UI kod düzeltmesi yalnız
genel sentetik snapshot alanını doğru adla üretir. Native helper yan etkileri
ve oyun transportu modellenmiş veya doğrulanmış sayılmaz.

`work/audit_source_route_commands.py`, iki hash'li sürümde **540 talimat
kaydını** disk baytlarıyla doğrular. Bekle signed ürün/clock dalları,
Otur/Kalk group-normalizasyonu, iki bağımsız yeniden karşılaştırma/eylem,
store sırası, beş literal ve her sürümde sekiz actor predicate zinciri
ayrıca kontrol edilir. Report:
`outputs/FarmexBot_rota_bekle_otur_kalk_kod_kaniti.json`.
Sayım her sürüm içindeki aynı adresi bir kez sayar; önceki auditlerle
örtüşmeyi benzersiz yeni kapsam veya tam fonksiyon olarak saymaz. Bu
Ghidra/disk kanıtıdır; REA Evidence değildir.

18 yeni test; raw rota grubu ve mevcut genel special-route kontrolleriyle
birlikte140 ilgili test geçti. Tam Python kontrolünde **2133 test geçti
(8.862 saniye)**. Süre başlangıcında parser'ı atlama, eşitlik,
signed taşma, tam QWORD clock, actor AL/provenance, iki taze eylem sonucu,
eksik helper/index, üst dispatcher gap'i ve doğru generic alan adı sınandı.
Gerçek oyun/native eylemler ve canlı uyumluluk açık kalır.

Alan adı düzeltmesi sonrası tam gizli UI kontrolü de geçti:1037kontrol,
11form,18ana sekme,detay renderer/arama/HP-MP/rota ve mevcut alt motor
senaryoları. Pencere withdraw durumda kaldı. Bu UI kontrolü yeni raw
Bekle/Otur/Kalk girişlerini sunmaz veya canlı oyunu test etmez; genel rota
snapshot üreticisinin ve mevcut uygulamanın bozulmadığını doğrular.
