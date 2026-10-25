# Unicode karşılaştırma dönüşü ve yerel rota adı sağlayıcısı

18 Ekim 2026. `source_unicode.py`, native RTL yüklemeden karşılaştırma
wrapper'ının normal dönüşünü modeller. `owned_route_texts.py`, açıkça seçilen
own metin modeliyle komut karşılaştırmalarını mevcut source observation
ağacına bağlar. Bu kaynak metnini/oyun belleğini okuyan bir adapter değildir.

## İkili dosyadaki zincir

Güncel00505d3c stack'teki iki referansı EAX/EDX'e aktarır ve00402e00çağırır.
00402e00 bu referanslardan iki string pointer'ı okur ve PE import'u üzerinden
`rtl260.bpl!@System@@UStrEqual$qqrv` çağırır. Normal dönüşte `SETZ AL` vardır.
Sonuç yalnız ZF'den türetilen düşük BYTE0/1'dir; EAX'in üst24biti SETZ ile
sıfırlanmaz. Post-helper EAX ayrıca gözlenmemişse model tam EAX'ı bilinmiyor
tutar. Dolayısıyla AL kesin olsa bile EAX DWORD'u0/1diye uydurulmaz.

Unicode assignment00505c88→00402de0 zinciri de ayrı olarak doğrulandı:
UStrAsg import'u çağrılır, dış wrapper EAX'e destination referansını geri
yazar. Bu audit refcount/allocator/string-header yazılarının implementasyonu
veya runtime assignment doğrulaması değildir. NPC608değer kopyasının own
immutable frame modeli native refcount emülasyonu sayılmaz.

## Gözlenmiş flag ve own metin politikası ayrı

`UnicodeEqualityObservation` için UStrEqual normal dönüşü açıkça gerekir.
Gözlenmiş `zero_flag` verilirse SETZ modeli AL üretir; optional post-helper
EAX verilirse sadece düşük BYTE değiştirilerek tam değer üretilebilir.
Flag veya normal dönüş eksikliği false karşılaştırma değildir.

Alternatif `use_owned_text_model=True` **açıkça seçilirse** post-conversion
iki Unicode metin UTF16LE code unit dizisi olarak, surrogatepass ile
karşılaştırılır. Eksik metin empty string değildir. NUL,space/case farkları,
composed/decomposed metin ve surrogate temsil korunur; casefold,trim veya
normalizasyon yapılmaz. Aynı anda gözlenmiş ZF ve own model verilemez.

[Üretici operator== belgesi](https://docwiki.embarcadero.com/Libraries/Sydney/en/System.UnicodeString.operator_H3DH3D)
case-sensitive karşılaştırmayı belirtir; aynı sayfa uygun durumlarda Windows
locale etkisine de değinir. Bu belge pinned RTL260gövdesinin ordinal/code-unit
semantiğini bayt düzeyinde kanıtlamaz. Bu yüzden UTF16karşılaştırması açık
**own policy** olarak işaretlenir; native RTL/locale/live uyumluluğu diye
sunulmaz. RTL260.UStrEqual/UStrAsg gövdeleri ve yüklü runtime kimliği bu
audit kapsamında doğrulanmadı.

Loot isim cache'inin önceden kullandığı aynı UTF16key fonksiyonu bu ortak
modüle taşındı; public `loot_name_cache.unicode_key` alias'ı korunur. O
alt sistemde yeni locale veya native conversion varsayımı eklenmedi.

## Rota observation sağlayıcısı

`bind_owned_route_texts(template,texts)` her karşılaştırma noktası için ayrı
own Unicode text alır. Town,Koordinat,Bekle,üç Gate,iki Delos,Change Camp,
NPC ve Randomize sonuçları ilgili frozen observation nesnelerine bağlanır.
Posture group'un Otur/Kalk örnekleri ile iki action recheck'i ayrı anahtardır.
İlk Otur true ise unknown Kalk text'i group sonucunu engellemez; ilk örnek
unknown ise sonraki Kalk true'dan kaynak group sonucu tahmin edilmez.

Eksik metinlerin AL'ıNonekalır. Sağlayıcı bütün sonraki adlar bilinmiyor diye
erken Town veya cursor yolunu durdurmaz; source dispatcher yalnız ulaşılan
örneği tüketir. Sağlayıcı string construction/cleanup receipt'lerini **asla
true yapmaz**. Var olan span receipt'leri korunur; yeni oluşturulan alt
frame'lerde receiptNonekalır. Kaynak helper/body/actor/clock/queue boşlukları
komut adının bilinmesiyle atlanamaz.

`owned_stable_route_texts` convenience factory'si ancak
`stable_same_invocation=True` açık sözleşmesiyle aynı own satır adını tekrar
kullanır. Randomize karşılaştırması komut adına değil parametre224metnine
bakar. Factory gerçek native index/array okumalarının sabit olduğunu
kanıtlamaz. Canlı adapter taze ad örneklerini ayrı sağlamalıdır.

Bu compiler bütün template'i kendi giriş politikasıyla doğrular; raw AL'lar
ile own türetilmiş karşılaştırmaları karıştırmayı reddeder. Bu bütün-template
kuralı native short-circuit kuralı değildir; mevcut raw source API'leri
değiştirilmedi. Bağlanan sonuç `owned_route_text_model` provenance ve
`native_runtime_verified=False` taşır. Bir kaynak fonksiyonun tamamlanma
veya canlı sertifikası olarak kullanılamaz. Raw provider henüz rota UI'sinde
ayrı kontrol olarak sunulmaz.

## Kanıt ve kontrol

`work/audit_source_unicode.py`, iki hash'li ikilide dört wrapper ve iki
import jump stub'ından **82 talimat kaydını** baytlarıyla doğrular. Stack/ref
argüman sırası,UStrEqual/UStrAsg kimlikleri,SETZ AL ve assignment EAX dönüşü
ayrıca anchor'lardır. Eski wrapper00505d20,güncel00505d3c'dir; erken00402e00
adresi değişmez. Rapor `outputs/FarmexBot_unicode_karsilastirma_kod_kaniti.json`.
Bu Ghidra/disk kanıtıdır; REA Evidence değildir. RTL helper body veya exception
semantiğini kanıtlamaz; önceki auditlerle örtüşme benzersiz kapsam sayılmaz.

8primitive +15own-provider yeni testi; mevcut loot isim cache kontrolleriyle
birlikte37hedefli test geçti. Tam Python kontrolünde **2215 test geçti
(11.382 saniye)**. SETZ üst-bit koruma,unknown normal-return/ZF,
UTF16surrogate/NUL/case/space/normalizasyon farkları,compiler receipt koruma,
unknown unvisited örnekler,fresh posture recheck,Gate seçimleri,Randomize
parametre kolonu ve mixed raw girdi reddi sınandı. Gerçek native runtime,
oyun string/pointer/codepage gözlemi ve canlı uyumluluk açık kalır.

Ortak key fonksiyonu loot cache tarafından da kullanıldığı için tam gizli
UI kontrolü tekrar çalıştırılıp geçti:1037kontrol,11form,18ana sekme ve
mevcut loot/route/diğer motor senaryoları. Kendi pencere withdraw kaldı.
Yeni owned text provider UI'de raw/native gözlem gibi sunulmadı; native
fixture ve gerçek oyun kontrolleri bu aşamada yapılmadı.
