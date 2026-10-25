# Genie durum ve kalan-değer BYTE okuyucuları

Sonraki aşama: genel/Notice worker’ındaki7getter çağrısı optional typed child ile bağlandı. Güncel kapsam [GENIE_GETTER_BINDING.md](GENIE_GETTER_BINDING.md); aşağıdaki metin önceki aşamanın sınırlarını korur.

21 Ekim 2026. `genie_getters.py` kaynak `004631c8` ve `004631e8` sarmalayıcılarını gerçek okuma yapmadan modeller. Her biri553e7cglobalinden slot adresini alır;0045dc44ile DWORD kök gözlemini ister; taze554070veya554074offset'ini ekler;0045dbdcile **BYTE** alan gözlemini ister; ayrı wrapper normal dönüşüyle tamamlanır.

BYTE okuyucunun başarılı yolunda `MOV AL,[ECX]` vardır; EAX üst24bit'i açıkça sıfırlanmaz. Plan raw EAX'i ve lowAL'yi ayrı korur. Null/protect-failure yolları full EAX0döndürür; pozitif normal read receipt'i bununla karıştırılmaz. Kök DWORD okuyucu0döndürse de wrapper offset ekleyip ikinci yardımcıyı çağırır. Kendi erken null-root guard'ımız eklenmedi.

Her iki guarded reader gövdesi VirtualProtect ile40hexkoruma isteği yapar ve aynı gövdelerde eski korumayı geri yüklemez. Model bunu çalıştırmaz veya etkisizmiş gibi simüle etmez. `GuardedReadReceipt` yalnız address/width/raw EAX/normal dönüş gözlemidir. Bounded kendi snapshot'ının varlığı, oyun belleği veya koruma etkisi kanıtı değildir.

| Kaynak modül | Profil |553e7cslot literal'i | Durum offset'i | Kalan-değer offset'i |
|---|---|---:|---:|---:|
|12f3e2dd…359a54|US|1115574|760|75c|
|12f3e2dd…359a54|Steam|11ea638|760|75c|
|febdac80…45759|US|11289c0|760|75c|
|febdac80…45759|Steam|11e9638|760|75c|

Değerler hex'tir. Constructor553e3ctabanına40/234/238offset'leriyle bu alanları yazar; çağıranın taban push'u ayrıca doğrulandı. `source_getter_observation` yalnız açık kaynak hash/profil seçimiyle fixture oluşturur. Genel API eksik runtime gözlemini bu sabitlerle doldurmaz. Kökler statik source initializer literal'idir; yüklü oyunun sürümü veya canlı pointer değeri değildir. “Kalan” BYTE'ın zaman birimi bu audit ile kanıtlanmadı.

`GenieGetterFrame` tüketilmiş global/read prefix'ini korur. Yanlış adres veya genişlik reddedilir; eksik normal guarded read sonradan tamamlanabilir. Field EAX bilinse bile wrapper return gözlemi eksikse plan tamamlanmaz.

`work/audit_genie_getters.py` eski/güncel iki wrapper, iki reader ve dört initializer/caller projeksiyonunda toplam184talimat kaydını dosya baytlarıyla doğrular. Kaynak `outputs/FarmexBot_genie_byte_okuyucu_kaniti.json`; korunmuş Ghidra/PE kanıtıdır, yeni REA Evidence değildir. Yedi yeni test width/order/null-root/EAX farklarını, prefix devamını ve dört version/profile fixture'ını kapsar. Tam koşu `GENIE_GETTERS_VALIDATION.json` dosyasında kayıtlıdır.

Bu getter sonuçları henüz genel worker/Notice/chat tüketicilerine typed child olarak bağlanmadı. UI/native C değişmedi; UI yeniden test edilmedi. Gerçek process read, VirtualProtect, Genie etkisi ve canlı uyumluluk doğrulanmadı.
