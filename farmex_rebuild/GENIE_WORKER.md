# Genel Genie bölümü ve Notice devamı

Sonraki aşama: genel/Notice worker’ındaki7getter çağrısı optional typed child ile bağlandı. Güncel kapsam [GENIE_GETTER_BINDING.md](GENIE_GETTER_BINDING.md); aşağıdaki metin önceki aşamanın sınırlarını korur.

21 Ekim 2026. `genie_worker.py`, `0045a05c` normal girişini `notice_genie_window.py` ile birleştirir. `GeniePrefixFrame` sıralı gözlemleri tüketir; `GenieWorkerFrame` yalnız45a38c'ye gerçekten ilerleyen model yolunda Notice frame'ine geçer. Bütün sonuçlar inert çağrı/store planıdır; oyunla bağlantı kurmaz.

İlk context+BB/BC/BAbyte'ları kısa devreli ve bağımsız okunur. Herhangi biri nonzero ise4631e8düşük AL'si kontrol edilir. Sıfırken taze context+BAaçıksa ortak recovery damgasına göre signedQWORD elapsed>=5000beklemesi kullanılır. Eşikte004ca588çağrısının ayrı ham EAX gözleminin yalnız AL'si553cf0'a, yeni tick553cf4/f8'e yazılır ve aynı turdaki alarm/stop kontrolleri atlanır.004ca588'in etkisine isim/caption'dan anlam verilmedi.

Beş saniye dolmamış ve cachedAL0ise taze BC/BBbyte'ları alarm ve bot-durdur/Town yoluna karar verir. BAkapalıyken ayrı taze BC/BBokumaları diğer alarm/stop yolunu seçer. İki alarm literal'i farklı adreslerde aynı `Default` metnidir; string hazırlığı/alarm/cleanup opaque normal-span gözlemidir. Stop/Town yolu normal epilogue ile Notice'e uğramadan döner.

Yerel2d/2e0başlangıcından sonra context+B8sürekli-açık yolu seçilirse Genie state,1000ms cooldown ve kalan süre sonuçlarından bağımsız olarak Notice'e ulaşmadan döner. Şartlar uygunsa466cc4`(1,)` ve yeni shared cooldown damgası planlanır; uygun değilse çağrı yapılmadan dönüş vardır.

Genel569100enable,569108mode2ve56910eGenie kapıları uygunsa561f7daktif bayrağı değerlendirilir. Aktif yolda isteğe bağlı561fa8=1, cooldown'dan önce yazılır. Cooldown ve düşükAL remaining uygunsa start, shared cooldown ve ayrıca yeni GetTickCount ile561fa4aktivite damgası planlanır; Notice atlanır. Bu son iki tick tek gözlemle birleştirilmez. Start yapılmazsa Notice'e yerel2d0ile devam edilir.

Aktif bayrak kapalıyken569112resume-delay kapısı ve signed low32`seconds*1000`eşiği kullanılır. Yalnız elapsed **eşikten büyükse** yerel2d1olur; eşitlikte0kalır. Genel kapılar kapalı/non2olduğunda veya delay kapalı olduğunda2d1olur. Bu sonuç Notice frame'inin `other_stop_flag_2d` girdisine bağlanır; başka değer verilmesi reddedilir. Notice kendi kalan gözlemleriyle bağımsız devam eder.

Önceki594talimatlık eski/güncel PE byte kanıtı yeniden denetlendi; `work/audit_genie_worker_prefix.py` yeni prefix branch/sıra özelliklerini ve iki alarm literal'ini kontrol eder. Yeni talimat kapsamı sayılmadı. Kaynak `outputs/FarmexBot_genie_genel_giris_kaniti.json`; korunmuş Ghidra/PE kanıtıdır, yeni REA Evidence değildir.

12yeni test beş saniye eşitliğini, cachedAL'yi, aynı turda alarm atlamayı, bütün always-on erken dönüşlerini, ayrı activity tick'ini, strict resume-delay sınırını, QWORD/DWORD sarma farkını, prefix cache'i ve derived local bayrağı Notice'e bağlamayı kapsar. Son tam koşu `GENIE_WORKER_VALIDATION.json` içindedir.

Normal modelin bu bölümleri kapsaması whole-worker/native/ABI/exception/heap sertifikası değildir. Context flag'lerinin tüm UI producer bağları ve recovery/helper etkileri açık kalır. UI/native C değiştirilmedi; UI yeniden test edilmedi.20Ekim21:15:38UTC host270süreç metadata envanterinde Knight/Farmex/Loader adıyla eşleşme0dı; o anda canlı doğrulama yapılmadı. Bu yalnız o an ve isim kapsamındaki envanterdir.
