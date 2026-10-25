# Hedef kontrolleri, kimlik boşluğu ve callback adresleri

`target_guards.py`,00464c2c actor kontrolünü ve0040b894 ID listesi kontrolünü koşullu gözlemlerle modeller. Bu modeller native kod çalıştırmaz ve oyun belleğine erişmez.

Actor pointer0 ise hemen full EAX0 döner. Diğer yolda553e7c globalindeki slot guarded helper ile okunur. Sonra553e46 profil BYTE'ı önce1, gerekli dalda yeniden okunarak2 ile karşılaştırılır. Profil1 kolu actor ve guarded root'u stack'e push eder; profil2 yalnız actor'u push eder. İki kolda da callback ECX'i için553e7c slotu yeniden ve doğrudan okunur. Bu root guarded root ile aynı varsayılmaz.553ea0 callback hedefi tazedir. Callback'in AL değeri tam1 ise başarı vardır; AL2 de reddedilir. Başarıda callback'in full EAX değeri korunur; reddetmede full EAX0 döner. Callback ABI'si ve yan etkileri çözülmüş değildir.

ID kontrolü, context+1f8 vektör nesnesinin context+208/+20c begin/end alanlarını okur. Başlangıç count0 ise EAX1 döner. Sonraki her döngüde count tekrar hesaplanır; entry için begin ayrıca taze okunur. Signed farkın sıfıra doğru dörde bölünmesi ve unsigned count karşılaştırması korunur. Full DWORD kimlik eşleşirse EAX0 ile reddedilir. Liste biterse kaynak yalnız AL1 yazar; kalan EAX bitleri context+1f8 değerinden kalır. Varsayılan561f34 context'i için bu sonuç562101'dir, full EAX1 değildir. Başlangıç boş listesi farklı yoldan full EAX1 döner.

`MSSelectorObservation.actor_guards` ve `id_guards`, aday sırasına bağlı typed gözlemlerdir. Child'lar gerçek source actor/stack-ID argümanlarıyla üretilir. Eksik child dış normal ile geçilemez; tamamlanmış child full EAX sonucu dış gözlemle aynı olmalıdır. Sonradan tüketilmiş opaque guard veya boss-filter çağrısına child eklenip geçmişe etki üretilemez.

Bu ID kontrolü kimliği üretmez; stack argümanını değer olarak alır. Seçicide EBP-48 için görülen iki açık erişim yine yalnız okumadır. Actor callback'inin dolaylı etkileri, string/EH helper'ları ve alias olasılıkları dışlanmadığından bunu kesin kaynak hatası veya çözülen kimlik üreticisi olarak işaretlemiyoruz. İsim helper'ında512 bayt yerel tampon var, ancak kaynak count sınırı yok; taşan native davranışı yeniden üretilmez.

553e3c tabanıyla çağrılan profil kurucuları actor slotunu taban+64, iterator slotunu taban+74 üzerinden dolduruyor:

| Sürüm/profil | Actor callback literal | Iterator literal |
|---|---|---|
| Eski US |797720|4e14d0|
| Güncel US |79f7a0|4e3af0|
| Eski Steam |871330|521690|
| Güncel Steam |8716d0|521690|

Slotlar553ea0 ve553eb0'dır. Adres değişiklikleri tek bir genel kaydırma değildir. Kaynakta initializer literal'inin bulunması, çalışan oyundaki profil veya çağrılabilirlik kanıtı sayılmaz.

Sabitlenmiş ca69… oyun dosyasında güncel US literal adresleri, Ghidra ile gelen Capstone5.0.6 kitaplığından96 baytlık doğrusal probe ile kontrol edildi. Iterator4e3af0 adresinde14 bayttan sonra çözümleme durdu. Actor79f7a0 adresindeki96 bayt doğrusal çözülebildi; bu tek başına fonksiyon/CFG/ABI kanıtı değildir. Olası dosya/runtime farkı, yanlış sürüm/adres veya çözümleme varsayımı açıklamalarından hangisinin geçerli olduğu belirlenmedi. Probe REA Evidence olarak etiketlenmez ve oyun çalıştırmaz.

13 yeni test; null actor, farklı profil argümanları, iki root, callback AL1, full EAX, devam boşluğu, fullDWORD/zero-ID eşleşmesi, dinamik/negatif/sarmalı count, bütçe, typed child ve geç binding yasağını kapsar. Eski/güncel ikililerde2984 mevcut talimat kaydı ve altı REA raporu eşleşti. Bunun246 kaydı iki guard modelinin gövdeleridir;2738 kayıt isim helper'ı/seçici/profil kurucularının pasif kanıtıdır. Tam fonksiyon veya canlı uyumluluk sertifikası değildir.
