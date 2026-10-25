# Priest bekleyen chat isteği tüketicisi

Sonraki API bağı: generic alt model artık üç sınıf tüketicisine isteğe bağlı typed child olarak bağlanabilir. Aşağıdaki bağın bulunmadığına ilişkin notlar önceki aşamanın kapsamıdır. Native etkiler ve UI bağı hâlâ açık. [Güncel generic bağ](GENERIC_CONSUMER_BINDING.md).

20 Ekim 2026. `priest_chat_consumer.py`, `004cee18` gövdesinin altı normal yolunu modeller. Ortak `plan_chat_consumer('Priest',context,observation)` ve `ChatConsumerFrame` arayüzünden kullanılabilir. Eski/güncel gövdelerde **668'er, toplam1336 talimat kaydı** ve GetTickCount/`CC32260MT.DLL::__ftol` import kimlikleri doğrulandı. Bu Ghidra/PE kanıtıdır; yeni REA Evidence veya canlı yürütme değildir.

## Ortak giriş

Pending nonzero ve ortak lock zero olduktan sonra, context `fc` Buff skill argümanı ve `104` AC skill argümanı hazırlanır. İkisi de bütün tür karşılaştırmalarından önce gelir. Alan signed pozitifse ham DWORD kullanılır; değilse sırasıyla `004ce71c` ve `004ce840` resolver'ının normal dönüşü/EAX'ı gerekir. Resolver sonucu0olsa bile kaynakta olmayan ek reddetme kuralı konulmaz.

İstek türü globali,1den6ya kadar her ulaşılan karşılaştırmada yeniden okunur. Kararlı tür varsayımı yapılmaz. Hiçbiri eşleşmezse false dönülür; pending için yeni clear store eklenmez.

| Tür | Ek signed gate | Hedef yolu | Generic helper skill argümanı |
|---|---|---|---|
| 1 Buff | `004645e4 >=2` | Party index→select→object/distance | Hazırlanan Buff argümanı |
| 2 AC | Bu gövdede ek gate yok | Object/distance→target cleanup | Hazırlanan AC argümanı |
| 3 Und | `00462e08 >=54`, sonra `004645e4 >=2` | Party index→select→object/distance | `28e` |
| 4 Str | `00462670 >=4` | Object/distance→target cleanup | `4` |
| 5 Cure | `00462ddc >=25` | Object/distance→target cleanup | `20d` |
| 6 Disease | `00462ddc >=35` | Object/distance→target cleanup | `217` |

Gate başarısızlığı, negatif party index veya geçersiz mesafe dalı pending'i temizleyip false döner. Buff/Und'da object lookup0dönerse mesafe adımı atlanabilir; diğer dört tür object0için pending'i temizler. Bu iki davranış tek bir genel “hedef yoksa bekle” kuralına indirgenmez.

## Mesafe sınırı

Nesne varsa taze `554008`/`554010` offset'leriyle iki guarded float yardımcı çağrısı yapılır; post-FSTP binary32 bitleri ayrı gözlemlerdir. Fiziksel mesafe push sırası Y, X'tir. `00460548` ve `__ftol` normal dönüşleri ardından yalnız dönüşümün düşük EAX DWORD'u **signed <=28** koşulunda değerlendirilir.

Model Euclidean mesafe, x87 yuvarlama modu, FPU exception veya `__ftol` overflow davranışı üretmez. Dönüşüm sonucu açık gözlem olarak verilir. Örneğin gözlenen ham EAX negatif signed değerse kaynak karşılaştırması onu28den büyük saymaz; model buna kaynakta olmayan clamp eklemez. Bu fixture sonucu, böyle bir EAX'ın gerçek oyunda üretildiği iddiası değildir.

Hedef temizleme yollarındaki altı `JC`, `TEST EAX,EAX` hemen arkasındadır; TEST carry flag'i sıfırladığı için normal akışta alınmazlar. Hedef DWORD alanı ve gerektiğinde taze target ID ayrı gözlemler olarak kalır.

## Generic ve doğrudan yollar

Taze alternate BYTE nonzero ise `004655e8` çağrısının **full EAX nonzero** sonucu gerekir. Zero sonucu pending'i korur; daha önceki helper etkilerini geri aldığı varsayılmaz. Nonzero sonrası2000delay, tick, stamp, lock ve pending clear projeksiyonları gelir.

AC/Str/Cure/Disease generic başarısı ayrıca taze sender ile party-index lookup yapar. Signed nonnegative index varsa ikinci taze GetTickCount sonucu `56970c + index*4` adresine yazılacak şekilde projekte edilir. Kaynakta üst index sınırı yoktur. Model geçerli slot sayısı uydurmaz; adres32bit sarılır ve bütün store'lar inert kalır. Bu, o adrese gerçek yazımın geçerli veya başarılı olduğunu kanıtlamaz.

Doğrudan yolda önce hareket DWORD'u ve gerekirse durdurma normal dönüşü, sonra1500delay/tick/stamp/lock gelir. **Pending doğrudan skill yardımcısından önce temizlenir.** Bu sıra Mage/Rogue modelindeki “yardımcı döndükten sonra clear” sırasından farklıdır. Geç bir yardımcı boşluğunda clear projeksiyonu sonuçta korunur; gerçek belleğe yazım makbuzu değildir.

Buff/AC/Und doğrudan çağrısı `004d3568`, Str `004d36ac`, Cure `004d3674`, Disease `004d3690` yardımcısıdır. Str full sender DWORD kullanır. Diğer beş tür yalnız sender WORD'unu DX'e yükleyip full EDX push eder; üst16bit için ayrı gözlem gerekir. Sıfır genişletme uydurulmaz. TRUE kaynak dönüşü yalnız lowAL1anlamındadır.

## Doğrulama ve açık işler

**14 yeni testle toplam2835 test geçti (6.957 saniye).** Altı skill argümanı, ortak resolver sırası, taze tür okumaları, signed eşikler, iki null-object davranışı, dönüşüm sonrası mesafe, generic failure, dört türün ek stamp'i, unbounded index sarılması, direct clear-before-helper ve geç boşlukta prefix korunması sınandı. UI/native C değişmedi; UI yeniden test edilmedi.

Native/FPU/protection/helper etkileri, geçerli nesne/context ömrü, callback önceliği ve producer→consumer ortak yaşam döngüsü açık kalır. Gerçek skill veya server sonucu doğrulanmadı. Yeni API henüz deneme UI'sine bağlı değildir.

Kaynak: `outputs/FarmexBot_priest_chat_tuketici_kaniti.json`; üretici `work/audit_priest_chat_consumer.py`. Uygulama kaydı `PRIEST_CHAT_CONSUMER_VALIDATION.json`.
