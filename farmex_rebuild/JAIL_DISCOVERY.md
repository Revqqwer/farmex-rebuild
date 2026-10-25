# Pencere keşfi ve ön yüklemeyle birleşik yenileme

`jail_discovery.py`, `0045bab0` içindeki ön yükleme çağrısı sonrasının `0045bac8` girişinden itibaren normal kontrol akışını modeller. `JailDiscoveryFrame`, önceki `JailPreloadFrame`'in gözlem/generator altyapısını kullanır; ürettiği kayıtlar ayrıdır. `JailRefreshFrame`, kaynak parent giriş/prologue → ön yükleme child → ayrı child çağrısı normal dönüşü → keşif devamı sırasını bağlar.

## Keşif kararları

Başlangıç string hazırlığı opak normal span'dır. Snapshot flags2/pid0 intent'i, `ffffffff` hata kapısı ve First/Next tam DWORD sıfır karşılaştırmaları korunur. Executable arama sonucunun tam `ffffffff` olması sürecin open/identity/list yollarını atlar. Diğer sonuçlarda OpenProcess handle0 bile olsa kaynak identity read/Unicode conversion çağrılarına ulaşır; kaynakta olmayan bir handle koruması eklenmez.55420c identity adresi her süreçte ayrı okunur.

Duplicate döngüsü her turda taze signed UI count alır. Satır başlığı ve00505d3c karşılaştırma sonucu ayrı gözlemlerdir. Kaynak EAX'ı title cleanup çağrısı boyunca stack'te koruyup sonra AL'ı test eder; generator da kabul edilmiş karşılaştırma DWORD'unu cleanup normal dönüşü beklerken korur. Daha sonra gelen çelişen EAX verisi bu sonucu değiştirmez. ALnonzero duplicate bayrağını1 yapar ve iç döngüyü keser. Üst24 bit alone eşleşme sayılmaz.

Duplicate bulunsa bile00505d4c kimlik karşılaştırması kaynakta değerlendirilir. Düşük ALnonzero ve duplicateFalse birlikteyse Add/SetCaption intent'lerine ulaşılır. Add, item EAX gözlemiyle satır intent'ini üretir; caption ayrı normal dönüşle eklenir. Bu keşif gövdesinde SetChecked çağrısı yoktur; native default checked değeri üretilmez. UI count değerleri önceki Add/ön yükleme intent sayısından türetilmez; kaynakta taze gözlem olmaları korunur.

Karakter okuması Add/caption'dan sonra gelir. Üç0045db9c raw DWORD sonucu ve offset'ler ayrı gözlemlerdir. Unsigned boyut16'dan küçükse553fe8 tekrar okunup root+taze offset seçilir; diğer dal önceden yakalanmış pointer'ı kullanır. DWORD adres toplamları taşar.004604d4, string conversion/assignment, temporary cleanup ve item+8 virtual3c normal dönüşlerinden sonra subitem intent'i korunur. Sonraki cleanup beklerken önceki UI kayıtları geri alınmaz. ReadProcessMemory başarısı veya serbest bırakılmış tamponun geçerliliği varsayılmaz.

Identity cleanup, Process32Next, executable cleanup ve final string/FS/stack dönüş sınırları kaynak sırasındadır. Next, executable cleanup'tan önce gerçekleşir. Eksik gözlem sonraki okumayı tüketmez; aynı frame tekrar ilerletilince Add/subitem intent'leri çoğalmaz.

## Birleşik yenileme

`JailRefreshObservation` üç typed gözlem taşır: `outer`, `preload`, `discovery`. Parent entry/prologue alınmadan child oluşturulmaz. Kaynak çağrı child girişini türetir; child prologue ve diğer normal dönüşler açık kalır. Erken `preload_return=True` eksik child'ı atlatamaz. Child complete olsa da parent normal dönüşü ayrıca gerekir; aksi halde discovery oluşturulmaz. Discovery son FS/stack/return span'ını tamamlayınca birleşik normal kontrol planı complete olur. Ön yükleme ve keşfin UI intent'leri sıralı birleştirilir.

Bu kompozisyon339 instruction parent ile218 instruction child'ın normal kontrol yollarını temsil eder. String/API/virtual yardımcıların semantiği, istisna/SEH/native nesne ve çağrı ABI etkileri tamamlama sertifikası değildir. `whole_function_verified`, `native_execution_verified` ve `live_compatibility_verified` False kalır.

14 test giriş/snapshot/search kapıları, handle0 asimetrisi, signed duplicate count, cleanup boyunca korunmuş AL, duplicate olsa da exclusion, fresh count, Add-before-character prefix, unsigned16/inline offset, Next/cleanup sırası ve child/outer dönüş ayrımını denetler. İki sabit Richard sürümünde seçili yedi fonksiyon1268 instruction kaydı ve altı mevcut REA çıktısıyla doğrulandı. Kanıt `outputs/FarmexBot_koruma_pencere_kesif_model_kaniti.json`.

Model API kapsamındadır. Gerçek UI yenileme düğmesi, runtime VCL/RTL/heap/remote-read etkileri, pencere veya süreç açma ve canlı oyun uyumluluğu doğrulanmadı. Hiçbir süreç taraması, bellek okuması veya gerçek pencere/süreç işlemi uygulanmadı.
