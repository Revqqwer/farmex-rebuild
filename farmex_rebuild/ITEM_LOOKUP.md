# Item base ve extension lookup planları

`item_lookup.py`, kaynak `00465514` ve `00465580` yardımcılarının anahtar, taze global okuma, register/argüman ve normal dönüş sınırlarını modeller. Native lookup algoritmasını veya oyun belleğini çalıştırmaz. Çağrı hedefi, normal dönüş ve EAX değeri ayrı gözlemlerdir.

Temel anahtar unsigned `itemID // 1000 * 1000` değeridir. İlk istemci türü BYTE okuması birse tek anahtar push edilir, fonksiyon hedefi 0x553ec4 globalinden gelir. Bu dalda ECX bilinmez değildir: XOR/MOV CL/DEC dizisi onu sıfır yapar. İlk okuma bir değilse istemci türü tekrar okunur. İkinci okuma ikiyse 0x553ec0 globalinin işaret ettiği DWORD ECX olur ve aynı fonksiyon hedefi çağrılır. İkinci okuma iki değilse başlatılmış sıfır sonuç döner; context/fonksiyon okumaları gerekmez. İki tür okuması birbirine eşitlenmez. Bu helper itemID sıfır için ayrıca erken çıkış yapmaz.

Extension helper itemID sıfırsa hiç dış okuma yapmadan sıfır döner. Diğer durumda anahtar unsigned `itemID % 1000` değeridir. Resolver DWORD'un yalnız düşük BYTE'ı kullanılır. Tablo slot adresi `tableBase + lowBYTE * 4` düşük DWORD ile hesaplanır; `0045dc44` slot değerini okur. Bu değer ECX'e, 0x553ecc globalindeki fonksiyon hedefi EAX'e ve remainder anahtarı stack'e gider. Slot değeri sıfır diye kaynakta olmayan erken çıkış eklenmez.

Normal dönüş gözlemi olmadan yalnız EAX sağlanması yeterli değildir. Native helper'ın iç map/tree davranışı, kaynak register/stack ABI'sinin gerçek yürütümü veya yüklü global değerleri bununla kanıtlanmaz. Null context dereference ve null call target tamamlanmış normal yol sayılmaz; bunlar kaynakta yeni güvenlik kapısı varmış gibi sunulmayan açık sınırlardır.

9 yeni test dahil toplam 4150 test geçti (`work/item_lookup_full_tests.log`). Unsigned sınırlar, bağımsız iki tür okuması, düşük BYTE tablo seçimi, DWORD adres sarması, normal dönüş/result ayrımı ve sıfır yolları denetlendi. İki Richard sürümündeki 152 talimat kaydı disk baytlarıyla doğrulandı (`FarmexBot_item_lookup_kaniti.json`). Yeni başarılı REA analizi yok; mevcut Ghidra kaydı kullanıldı.

Mevcut `item_name.py` 00467908 isim yardımcısı için daha önce oluşturulmuş captured-byte modelini zaten içeriyor. Lookup planları ve bu model Merchant metadata üreticisine birleştirilecek; aynı isim yardımcısı yeniden yazılmadı. Native lookup/metadata sonuçları ve doğru ANSI→Unicode dönüşümü sağlanmadan gerçek item adı/türü çözüldü iddiası yapılmaz. Panel/dağıtım bu aşamada değişmedi.
