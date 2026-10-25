# Zamanlayıcı invocation gözlem frame'i

`MerchantScanFrame`, tek bir `004bf9dc` invocation'ının kendi gözlem durumudur. `merchant_scan_step` kararını her ilerlemede aynı immutable başlangıç state'inden, yalnız ulaşılmış/gözlenmiş alanları cache'leyerek projekte eder. Böylece bekleyen helper dönüşü, fresh count veya post saat için tekrar sorgulama indeks artışını biriktirmez ve yeni helper dönüş isteği üretmez.

`new_return_requests` yalnız normal dönüş gözlemi talebidir. İçinde native ABI argümanı veya çalıştırılabilir native komut yoktur; `executable_native_command=False` kalır. Token'lar kendi süreç/frame/target kapsamındadır, persistent veya başka süreçteki native handle değildir. Aynı bekleyen target için polling yeni token çıkarmaz. Önceden verilmiş tamamlanmış gözlemler logical call trace oluşturabilir; bunlar dispatch edilmesi gereken yeni çağrılar değildir.

Data0 ve booleanFalse gibi kullanılan gerçek değerler saklanır. Normal dönüş alanında yalnızTrue kabul edilip cache'lenir; None/False normal dönüş kanıtı sayılmaz. Bilinen harici child başarısızlığı için `abort(reason)` terminaldir. Native child'ın kısmi bellek/queue/UI etkileri hâlâ bilinmez; abort yalnız kendi caller-prefix'ini korur, native rollback veya exception recovery gerçekleştirmez.

Henüz ulaşılmamış alanlar, önceki snapshot'ta verilmiş olsalar bile dondurulmaz. Örneğin koleksiyon EAX'ı, helper normal döndükten sonra tüketilir. Rota boyutunun ilk ve fresh okumaları farklı alanlardır; tüketimin pre/post saatleri de ayrıdır. Post saat beklenirken tüketim için yeniden dönüş isteği üretilmez.

Distance status WORD'ü bilinmiyorsa, normal scalar distance gerçekten tüketilene kadar fallback seçimi dondurulmaz. Scalar kullanıldıktan sonra aynı invocation'a sonradan başka raw status getirerek branch değiştirilemez. Raw status zaten gözlenmişse doğrudan kaynak maskesiyle saklanır. Bu, yeni tick'leri engellemez: waiting/busy/normal helper dönüşüyle invocation terminal olduğunda yeni tick için yeni frame gerekir. Eski terminal frame yeni veriyi işleyip yeni iş yapmaz.

`complete` kendi normal-value invocation projeksiyonunun bitmesidir; source helper receipt, canlı ACK veya native yürütüm eşliği değildir. Bounds-exception intenti terminal fakat incomplete'dir. Frame, tek thread'de sıralı gözlem ilerletmesi için tasarlanmıştır; native stack capture, gerçek timer veya child queue/call executor değildir.

12 yeni regression testiyle4396 Python testi geçti. Yeni GUI çalıştırılmadı; değişen scheduler modülü ve yeni testi300 modüllük app/smoke_ui import closure'ı dışındadır, closure hash'leri önceki4372 tam GUI kaydıyla aynıdır. Güncel kayıt MERCHANT_SCAN_FRAME_VALIDATION.json; source/own frame kapsamı FarmexBot_merchant_zamanlayici_frame_kaniti.json içindedir. Sonraki açık iş typed child execution ve timer/data/reply sağlayıcısı birleşimidir.
