# DC eylem koşulları ve sınırlı çağırıcı bağlantısı

`dc_propagation.py` üç ayrı kapsam sunar: `DCPeriodicFrame` sınırlı parent dalı, `DCConsumerFrame` iki tüketicinin normal kontrol yolları ve `DCCascadeFrame` ulaşılan tüketici child'ını ayrı outer-return ile bağlayan kompozisyon. Hiçbir Windows/sender/remote-memory işlemi uygulanmaz.

## Zaman ve seçim

Parent bounded entry00459981'dir. Kaynak callback0046f520,00459970'e **562194** context'ini verir; varsayılan context ayrı callback callsite byte'larıyla doğrulandı. Context+6e nonzero ise plan0045998e sınırına çıkar; bu alternatif parent dalının tamamlandığı anlamına gelmez. Sıfırsa5691b1 enable baytı okunur. Enable0,00459c5a devam sınırına çıkar.

Enable açıkken GetTickCount normal dönüşü ve EAX gözlemi ayrı alınır;553ce4 stamp DWORD'u taze okunur. `((tick-stamp)&ffffffff)>=300000` unsigned koşulu sağlanırsa5691b2 taze okunur: sıfır scan0046d904, nonzero list0046dd70. Helper normal döndükten sonra ayrı post GetTickCount/EAX alınır ve553ce4 store intent'i üretilir. İlk tick'in yeniden kullanılması veya helper dönüşü beklenmeden store yapılması yoktur.

## İki tüketici

Her biri kaynak giriş/prologue ister. Scan payload byte'ını526fa8, list526faa adresinden ayrı gözlemle alır. Diskteki01 değeri runtime'da otomatik doldurulmaz; raw gözlem tutulur. Liste yolu scratch init, üç fresh count/begin okuması ve ayrı element begin'ini kullanır. Pointer farkının negatif adjustment/SAR2 ve unsigned sınırı korunur. Title pointer0 için52704c NUL adresi vardır. Window, PID ve handle bağımsız sıfır kapılarıdır.

Scan yolu opak başlangıç/executable/string arama sınırlarını, snapshot=-1, First/Next tam DWORD, search=-1 ve düşük AL identity karşılaştırmasını korur. Bu kaynak yolunda handle0 kimlik/guard okumalarını otomatik atlatmaz. Process32Next, executable cleanup'tan önce gelir. Tek bir helper/encoding/remote read sonucundan kaynakta bulunmayan başarısızlık varsayımı türetilmez.

Guard ilk remote root DWORD'u ve5541f8 offset'ini alıp0045dbbc byte sonucunun **AL tam1** olmasını ister. Nonzero2/ff ilerlemez;101DWORD'unun AL1'i ilerler. Sonra553f3c+5541a0 ve553f64+5541e4 zincirlerinin iki ayrı DWORD sonucu alınır. Her iki zincir, birincinin sıfır kontrolünden önce çalışır. Yalnız iki sonuç0 olduğunda00464834 çağrı intent'i ve `(handle,captured_payload_bytes)` kaydı oluşur. Kaynak local payload adresi semboliktir; native stack pointer'ı uydurulmaz.

Gönderim helper'ı opak normal dönüş sınırıdır. Payload intent'i çağrıya ulaşıldığını planlar; kuyruğa gönderildiği, remote write/thread tamamlandığı, EAX başarı değeri veya oyunda DC gerçekleştiği anlamına gelmez. Helper beklerken aynı frame yeniden ilerletilince payload intent'i çoğalmaz. Önceden tüketilmiş payload byte'ı sonradan değiştirilmez.

## Parent–child ve doğrulama

`DCCascadeObservation` parent/consumer typed gözlemleri taşır. Parent tüketici çağrısına ulaşınca doğru kind/context ile child oluşturulur ve giriş türetilir. Erken parent receipt eksik child'ı atlatamaz. Child complete olduğunda parent'ın ayrı `consumer` normal receipt'i ve post_tick hâlâ gereklidir. Helper hiç payload üretmeden normal dönebilir; kaynak parent yine post timestamp yoluna gider.

12 test bounded entry/enable, kaynak context, unsigned299999/300000/tick wrap, iki selection yolu, fresh post stamp, exactAL1, ikinci zincirin atlanmaması, her DWORD kapısı, liste PID/handle kapıları ve scan handle0 farkı, snapshot/search/compare erken çıkışları, pending-send/idempotence ve child/outer ayrımını denetler. İki Richard görüntüsünde1940 önceki chain instruction kaydı ve ek üç callback callsite instruction'ı her sürümde, toplam1946 kayıt doğrulandı. Sekiz mevcut REA çıktısı yeniden eşleştirildi; callback site ek raw-byte kanıtıdır. Kanıt: `outputs/FarmexBot_DC_koruma_model_kaniti.json`.

API kapsamıdır.441instruction parent'ın diğer stop/relogin/process/string/SEH yolları, gerçek callback scheduling, VCL/RTL/remote reader etkileri, sender ABI ve canlı oyun uyumluluğu açık kalır. `whole_function_verified`, `native_execution_verified` ve `live_compatibility_verified` False kalır. Gerçek allocation/write/thread/send/process işlemi yapılmadı.
