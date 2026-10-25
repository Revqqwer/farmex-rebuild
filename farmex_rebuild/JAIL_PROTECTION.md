# Hapis koruması: iki kaynak akışı ve TP alt model bağlantısı

`jail_protection.py`, `0046d66c` süreç tarama ve `0046dc5c` pencere listesi yordamlarının normal karar akışını kaynağa bağlar. `tp_jail_protection.py`, TP olay modelinde ulaşılan `jail_all`/`jail_list` çağrısını bu modellerden birine bağlayan isteğe bağlı API'dir. Bütün okuma, API çağrısı ve süreç kapatma kayıtları inerttir; Windows veya oyun üzerinde uygulanmaz.

## Liste yolu

Kaynak giriş/prologue ve ilk string oluşturma normal dönüşleri ayrıdır. Kullanılmayan `526fa9` byte okuması da gözlem ister. Her döngüde context `+d0` ilk kez okunur; sıfır değilse `+d4` son pointer'ı ve sonra yeniden `+d0` çıkarma pointer'ı alınır. DWORD farkı negatifse 3 eklenir, signed sağa 2 kaydırılır ve sonuç indeksle unsigned karşılaştırılır. Negatif farklar basitçe sıfıra kırpılmaz; örneğin -4 farkı `ffffffff` sayısını verir.

Eleman için `+d0` bir kez daha, ayrı gözlem olarak okunur. Adres `begin+index*4` DWORD taşmasıyla hesaplanır. String atama yardımcısının normal dönüşünden sonra yakalanmış title pointer'ı kullanılır; sıfırsa kaynak NUL adresi `52704b` seçilir. `FindWindowA`, yazılmış PID ve `OpenProcess` handle'ı bağımsız sıfır kapılarıdır. `GetWindowThreadProcessId` API dönüş değeriyle yazdığı PID birbirine eşit varsayılmaz. Handle nonzero olduğunda kaynak `TerminateProcess(handle,0)` çağrı kaydına ulaşır. İterasyon sonunda kaynak vektör sınırlarını yeniden okur; sabit liste uzunluğu kullanılmaz.

## Süreç tarama yolu

Başlangıç metni ve `.bnbx` string hazırlığı opak normal span olarak kalır. Snapshot fiziksel PUSH sırası `(0,2)`; `ffffffff` hata değeri `Process32First` çağrısını atlar. First/Next tam DWORD sonuçları sıfırla karşılaştırılır. Her süreçte executable hazırlığı ve `0041ac60` arama dönüşü ayrı gözlemlerdir. Tam `ffffffff` arama sonucu open/remote-text/compare/terminate yolunu atlar.

Bu kaynak yolunda sıfır handle kontrolü yoktur. Başarısız OpenProcess sonucunu otomatik atlamak kaynak davranışını değiştirirdi. Model sıfır handle ile de yalnız inert uzak metin çağrı planını üretir. `55420c` adresi her süreçte yeniden okunur; uzunluk parametresi `ff` olur. Dönen pointer ve string dönüşüm/karşılaştırma yardımcılarının normal dönüşleri açık gözlemlerdir. Serbest bırakılmış tampon adresinden güvenilir metin türetilmez. `00505d4c` dönüşünün düşük AL baytı nonzero ise kaynak terminate çağrısına ulaşır. Unicode cleanup'tan sonra `Process32Next` çağrılır; executable string cleanup'ı bu Next dönüşünden sonra gerçekleşir.

## Devam ve üst çağrı

`JailObservation` değişmez BYTE/DWORD ve normal dönüş haritaları taşır. `JailFrame` yalnız o anda ulaşılan gözlemi tüketir. Akış generator ile sürer; aynı frame tekrar ilerletildiğinde eski çağrı intent'leri tekrar eklenmez ve önceden alınmış sonuçlar değişmez. İlerideki gözlemler henüz ulaşılamadan saklanmaz. Kaynakta bulunmayan bir süreç sayısı sınırı eklenmedi; eksik bir sonraki gözlemde beklenir.

Çağrı tuple'ları fiziksel PUSH sırasındadır. Yerel string/PID/process-entry adresleri semboliktir; Python nesne adresleri veya gerçek process pointer'ları değildir. Son cleanup ve FS/stack/return span receipt'leri ayrıca gerekir. `complete=True` yalnız bu kaynak kontrol planının tamamlandığı anlamına gelir; native başarı, tüm helper semantiği, SEH yolları veya tam fonksiyon sertifikası değildir. Void yordamlar için uydurma başarı EAX değeri üretilmez.

`TPJailFrame`, parent TP modelinde gerçek `jail_all`/`jail_list` çağrısına ulaşınca doğru child girişini türetir. Erken parent normal-return receipt'i eksik child'ı atlatamaz. Child tamamlandıktan sonra parent'ın ayrı normal dönüşü yine gereklidir. Child beklerken parent'ın önceden ürettiği `561f6e/561f70` flag intent'leri korunur. Diğer opcode/TP yollarında child oluşturulmaz.

## Doğrulama ve kalan kapsam

18 hedefli test; boş/fresh/değişen vektör, negatif signed farkın unsigned sınırı, pointer taşması, üç bağımsız liste kapısı, sıfır title, snapshot hatası, First=0, search=-1, sıfır handle ile tarama, düşük AL, Next/cleanup sırası, kesinti/idempotence ve child/outer dönüş ayrımını denetler. İki sabit Richard görüntüsünde yedi fonksiyon ve 117 instruction'lık TP olay dilimi toplam **1218 instruction kaydı** üzerinden doğrulandı; yedi mevcut REA çıktısı yeniden denetlendi. Kaynak kanıtı: `outputs/FarmexBot_koruma_jail_model_kaniti.json`.

Yeni modeller API kapsamındadır; arayüz denemesi ve gerçek incoming hook bu isteğe bağlı child API'sini henüz kullanmıyor. String/encoding yardımcıları, yerel/uzak kimlik metninin güvenilirliği, gerçek pencere listesi üreticisi, istisnalar, native stack/object/protection etkileri ve canlı oyun eşdeğerliği açık kalır. Oyun belleği okuması/yazması veya süreç kapatma yapılmadı.
