# Mage/Rogue bekleyen chat isteği tüketicileri

Sonraki API bağı: generic alt model artık üç sınıf tüketicisine isteğe bağlı typed child olarak bağlanabilir. Aşağıdaki bağın bulunmadığına ilişkin notlar önceki aşamanın kapsamıdır. Native etkiler ve UI bağı hâlâ açık. [Güncel generic bağ](GENERIC_CONSUMER_BINDING.md).

Sonraki Priest kapsamı: altı türün normal-yol modeli artık ortak consumer API’sine bağlıdır. Aşağıdaki Priest modelinin bulunmadığına ilişkin notlar önceki aşamanın kaydıdır. Native etkiler hâlâ açık. [Priest tüketicisi](PRIEST_CHAT_CONSUMER.md).

20 Ekim 2026. `chat_skill_consumers.py`, Mage rolü için `004994bc`, Rogue rolü için `004da568` gövdelerinin normal yollarını modeller. Eski/güncel kaynakta iki gövdenin **482 talimat kaydı** baytlarıyla ve GetTickCount import kimliğiyle doğrulandı. Bu korunmuş Ghidra/PE kanıtıdır; yeni REA Evidence veya canlı yürütme değildir.

Her iki gövde önce global pending BYTE `5693a0` nonzero ve ortak lock BYTE `561f7e` zero olmasını ister. Bunlar sağlanmazsa kaynak EAX sıfır döner. Başarılı yollar yalnız AL'a1 yazar; tam EAX'ın1 olduğu varsayılmaz.

## Mage normal yolu

İstek türü tam1 olmalıdır. Helper dönüşleri signed karşılaştırılır: `00462670 >=10`, `004611e0 >=5`, `004645e4 >=2`. Sonra taze sender DWORD ve `569584` context'iyle lookup yardımcısı `004cb898` çağrılır; signed negatif index ilerlemez. Bu erken başarısızlıklar pending isteği temizlemez.

Hareket alanı için global `553e7c` slot'u, guarded DWORD kök ve taze `554020` offset'i üzerinden bir **DWORD** okunur; nonzero ise `00464714` normal dönüşü gerekir. BYTE'a daraltılmaz. Sonra hedef helper'ı ve `55403c` DWORD alanı üzerinden hedef temizleme yolu gelir. Kaynak `TEST EAX,EAX` hemen ardından `JC` kullanır: TEST carry flag'i sıfırladığından bu atlama normal talimat yürütmesinde alınmaz. İlk helper EAX'ı için tahmini negatiflik koşulu eklenmez. Hedef DWORD nonzero ise `00462630` yeniden çağrılır; bu taze EAX, `00465ef8` çağrısına aktarılır.

Index `00464650` yardımcısına verildikten sonra taze `561f88` BYTE'ı iki yolu ayırır:

| Yol | Normal sıra |
|---|---|
| Nonzero | Taze sender ile `004655e8`, kaynak skill literal4. Full EAX zero ise false, pending korunur. Nonzero ise delay2000 → GetTickCount → stamp/lock → pending clear → lowAL1. |
| Zero | Delay1500 → GetTickCount → stamp/lock → taze sender ve actor context ile `0049e8c8` normal dönüşü → pending clear → lowAL1. |

Generic helper'ın0dönmesi, daha önceki hareket/hedef/index yardımcılarının çalışmadığı anlamına gelmez. Model bu çağrı planlarını false sonuçta da korur; gerçek etkileri doğrulanmış saymaz.

## Rogue normal yolu

İlk tür karşılaştırması1 değilse tür globali **yeniden** okunup2ile karşılaştırılır. İki gözlem aynı kabul edilmez. Tür1 için signed seviye eşiği10, tür2 için30dur. Bu seviye başarısızlığı **pending'i temizler**; Mage'deki koruma davranışı buraya taşınmaz.

Alternate BYTE nonzero ise hedef temizleme yolu ve generic `004655e8` çağrısı kullanılır. Skill literal'i tür1için10, tür2için30dur. Full EAX nonzero sonrası2000delay/stamp/lock/pending sırası Mage generic yoluyla aynıdır.

Doğrudan yolda1500delay/stamp/lock **hareket kontrolünden önce** yazılır. Hareket DWORD'u nonzero ise ayrı durdurma dönüşü gerekir. Sonra:

- SW: Kaynak sender globalinden yalnız WORD'u DX'e yükler, tam EDX push eder ve actor context ile `004e08e0` çağırır. Üst16bit sıfırlanmadığı için model hem taze sender WORD'unu hem gözlenen full EDX push DWORD'unu ister; düşük16bit eşleşmelidir.
- Wolf: `004e103c` yalnız actor context argümanıyla çağrılır. Kaynakta olmayan sender argümanı eklenmez.

Doğrudan yardımcı normal döndükten sonra pending temizlenir. Yardımcı dönüşü eksikse önceki delay/stamp/lock projeksiyonu sonuçta kalır, pending clear eklenmez. Bu store'lar inert projeksiyonlardır; gerçek yazım makbuzları değildir.

## Gözlem sözleşmesi

`plan_chat_consumer(family,context_dword,observation)` açık helper dönüşleri ve taze source değerleri ister. `movement_*` ve `target_*` slot/root/offset/DWORD sonuçları ayrı gözlemlerdir; kaynak root+offset toplamı32bit sarılır. Guarded okuyucunun VirtualProtect/fault etkileri emüle edilmez. GetTickCount da çağrılmaz; normal dönüş ve ham DWORD snapshot'ı verilir.

`ChatConsumerFrame` tek çağrıdaki tüketilmiş prefix'i korur. Aynı tamamlanmış frame ikinci skill veya store uygulamaz; model zaten eylem yürütmez. Source producer ile ortak pending ömrü, gerçek callback önceliği ve actor context'in geçerliliği henüz bağlı değildir. Önceki producer modelinin bitmesi otomatik olarak bu tüketicinin çalıştığı anlamına gelmez.

Priest tüketicisi bu modülde yoktur. Alt skill/native yardımcılarının ABI'si, başarı anlamı ve server sonucu açık kalır. Kaynak helper normal dönüşleri gerçek skill başarısı diye sunulmaz. Mevcut UI bu yeni API'yi henüz tüketmez.

## Doğrulama

**13 yeni testle toplam2821 test geçti (6.909 saniye).** Signed eşikler, Mage/Rogue pending farkı, ikinci taze tür okuması, fullEAX generic sonucu, TEST/CF davranışı, DWORD hareket alanı, pointer sarılması, direct lock/clear sırası, gözlenen üstEDX, Wolf argümanları ve her ulaşılan boşluk sınandı. UI/native C değişmedi; UI yeniden test edilmedi.

Kaynak: `outputs/FarmexBot_mage_rogue_chat_tuketici_kaniti.json`; üretici: `work/audit_chat_consumers.py`. Uygulama kaydı `CHAT_SKILL_CONSUMERS_VALIDATION.json`.
