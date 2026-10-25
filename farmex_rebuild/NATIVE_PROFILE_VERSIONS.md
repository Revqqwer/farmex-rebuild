# Depo ve beceri fixture tablolarının kaynak sürümü

19 Ekim 2026. `native_profile_versions.py` depo ve alternatif beceri operandlarını **kaynak Richard SHA256 + profil + fixture türü** ile bağlar. Eski `storage_profiles` ve `skill_native_plans.SOURCE_GLOBALS` arayüzleri12f3e2dd…359a54 tarihsel fixture davranışını korur; güncel febdac80…45759 için yeni API açık hash ister. Üretim oyunu veya canlı profil otomatik seçilmez.

Bulunan eksik, HP/MP dışındaki bu iki sabit tablonun tarihsel değerlerle etiketlenmiş olmasıydı. Güncel değerler ayrı veri kümesine alındı:

| Alan | Eski US | Güncel US |
|---|---:|---:|
| Depo/skill root slot (`553e80`) | `111563c` | `1128a7c` |
| Dialog root slot (`553f44`) | `1116394` | `11297dc` |
| Quantity input root (`553f48`) | `1114f7c` | `11283bc` |
| INN context ofseti (`5540bc`) | `22c` | `26c` |
| VIP context ofseti (`554128`) | `230` | `270` |
| Skill lookup target (`553ebc`) | `503be0` | `5066b0` |
| Skill target (`553ee4`) | `886b30` | `88eb50` |
| Skill context ofseti (`5540a0`) | `468` | `4a8` |

Güncel Steam root/dialog/input alanları `11eaab0` / `11fd704` / `11e867c`; lookup-context slotu `11e950c`, skill target'ı `7df2d0` oldu. Her profil için15depo ve6skill alanı tutulur; ortak root iki grupta da vardır. Skill mode1/2 açık nominal profil girdisidir, constructor'daki bir store veya canlı detector ölçümü değildir.

`make_versioned_storage_observation` gerçek kaynak helper adresini korur. Güncel `004fe290`/`004fe318`, eski operand modelindeki canonical `004fe274`/`004fe2fc` rollerine eşlenir. Canonical ad yalnız yerel model kimliğidir; o eski adrese çağrı yapılmaz. Yanlış source-hash/helper çifti reddedilir. Diğer beş depo helper'ının adresi bu iki kaynakta aynı kaldı.

`make_versioned_skill_observation` güncel root/context ve iki beceri hedefini aynı hash/profil kimliğiyle mevcut skill operand modeline verir. `plan_versioned_native` çıktısında kaynak hash'i, gerçek helper adresi ve canonical rol taşınır; normal gözlemler olmadan native başarı uydurulmaz. Legacy fixture'ı yalnız yeniden etiketlemek güncel hash altında kabul edilmez.

Tablolar değiştirilemez ve her projeksiyon ayrı kopyadır. Runtime cache gibi tablolarda bulunmayan alanlar açıkça eklenebilir. Bilinen initializer alanını farklı değerle override etmek bu **sabit fixture sözleşmesinde** reddedilir; bu ret oyunda global'in değişemeyeceği anlamına gelmez. Gerçek değişmiş global örnekleri ayrı ordered-observation API'lerine verilmelidir.

Eski ve güncel iki US/Steam kurucusundaki **76 alan store kaydı**, US sıfır lookup-context için `XOR EBX,EBX` dahil, dosya baytlarıyla doğrulandı. Dokuz canonical helper gövdesi relative adresler ve import kimlikleriyle karşılaştırıldı; toplam **1022 talimat kaydı** doğrulandı. Quantity helper'ın frame setup/temporary cleanup sınırları açıkça opaque kalır; bunların iki sürümde eşdeğer alt yordam olduğu iddia edilmez. Bu Ghidra/PE audit'idir, REA aracı çıktısı değildir.

**10 yeni testle toplam2687 birim testi geçti (6.778s).** Güncel US/Steam slot planları, beceri hedefleri, quantity cache kökü, yanlış hash/helper/profil, tarihsel snapshot'ın güncel root yerine geçememesi ve immutable/cache sınırları test edildi. UI ve native C değişmedi; son UI testi2657aşamasındadır.

Bu kayıt kaynak tablo kimliğini doğrular. Oyun dosyası hash'i, runtime slot değerleri, dolaylı hedef ABI'si, gerçek bellek etkileri ve canlı uyumluluk ayrıca doğrulanmalıdır. Yeni factory'ler eski arayüzlerin çağrılarını kendiliğinden değiştirmez; UI henüz bu kaynak-sürümü seçim katmanını tüketmez.

Sonraki API entegrasyonunda alternatif iksir, depo item ve worker-page tüketicileri sürümlü girdiyi kabul edecek şekilde bağlandı. Factory `normal_returned` parametresini ayrıca taşır; kaynak kimliği sonuçta korunur ve ulaşılan karışık sürümler reddedilir. Güncel test sonucu ve sınırlar: [VERSIONED_NATIVE_CONSUMERS.md](VERSIONED_NATIVE_CONSUMERS.md).
