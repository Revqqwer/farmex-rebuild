# MS hareket ve hedef girişi

`monster_stone_combat.py`115talimatlık4c54c8hareket yolunu ve30talimatlık4c5468hedef girişini modeller. Varsayılan context56216c'dir. Bellek erişimleri gerçek okumalar değil, sıralı adres/width/gözlem planıdır. Captured helper sonuçları ve ayrı normal dönüşler gerekir.

Hareket, activeBYTEve51/52/53üç bağımsız alan getter'ıyla kapılanır. StateBYTE, durumfloat'ı ve stanceDWORDiçin553e7cslotu üç kez taze okunur; önceki kök sonucu yeniden kullanılmaz. Nullkök otomatik no-opvarsayılmaz. State'de yalnızAL, stance'de fullDWORD6karşılaştırılır. Ardından diğer/no-attackBYTEkapıları ve mod okunur.

Mod0'da55.0/55.0rawfloatbitleriyle mesafe çağrısı ve49.0ile karşılaştırmadan gözlenenAXkullanılır. `TEST AH,45`sonucu0ise bossmovehelper çağrılır ve erken dönüş vardır; diğer durumda followdalı değerlendirilir. Followkapıları context+5ve56204cBYTE'larıdır.56203ctargetpointer bir kez yerelde tutulur;554008/554010ofsetleri ayrı okunur ve iki helper'ınFSTPfloat32bitleri yakalanır. Aynı physical `(second_bits, first_bits)`argümanlarıyla iki farklı mesafe çağrısı vardır; ilk sonuç yerel float'a kaydedilir.

Son branch, ilk float'ı50.0ile karşılaştırıp `TEST AH,41; JP`uygular. Ham koşul bitleri için greater→mask0/parity-even→çıkış, less→mask1/odd→hareket, equal→mask40/odd→hareket, unordered→mask41/even→çıkış vardır. İkinci mesafe için1.0karşılaştırmasınınAH45maskesi ayrı tüketilir. Böylece basit `<50`koşuluyla eşitlik yolu kaybedilmez. Bunlar gözlenenAXüzerindeki CPUbranch kurallarıdır; x87aritmetik, CW, exceptionve captured float/status tutarlılığı emüle edilmez.

Movementisterse generated `MotionGenieFrame('004646b4',pushes)`ile bağlanır. Childgözlemleri eksikken parentnormal bunu geçemez; tamamlandıktan sonra outerhelper dönüşü hâlâ ayrıdır. `MSCombatFrame`tüketilmiş kök/koordinat/flagve childsonucunu korur; henüz okunmayan offset/yeni sonuçlar sonradan gelebilir. Gerçek directwrite/koruma değişikliği veya pozisyon değişikliği uygulanmaz.

Hedef girişinin yerelBYTE'ı mode0da1, diğer modlarda0yazılır; bu gövdede daha sonra okunmaz. Model bundan ek filtre türetmez. Source40b294preparehelper'ından sonra562040currenttargetDWORDtaze okunur;40b978guard'ınALsonucu nonzeroise4c50d0selector çağrılır. Selector fullEAXsonucu0bile olsa562040'a projekte edilir. Bu30talimatta doğrudan saldırı paketi yoktur; genel MSsaldırısı tamamlandı sayılmaz.

11yeni test; alan/aktif erken dönüşleri, nullve üç bağımsız kök, rawunorderedmask, boss49eşitliği, final50eşitliği/PF, iki mesafe, consumedpointer/freshoffset devamı, generatedchild/parentnormal ayrımı, unusedlocal, guardALve selectorEAXdevamını kapsar. Son tam koşu3062testtir. UIdeğişmedi/yeniden sınanmadı.

Üç gerçek REA raporu güncel PE ve assembly export’u ile eşleştirildi. Hareket/giriş modellerinin dayandığı iki gövde, eski ve güncel sürümlerde toplam 290 talimat kaydı içeriyor. Yalnız pasif incelenen 289 talimatlık seçici gövdesi ise iki sürümde 578 kayıt tutuyor. Toplam 868 mevcut kayıt diskten doğrulandı; bu sayılar tam davranış çözümü değildir. Seçicinin ayrıntıları, ana işleyiciye bağ ve gerçek hareket/hedef/saldırı etkisi hâlâ açık. Yeni envanter kapsamı veya canlı uyumluluk sertifikası iddia edilmiyor.
