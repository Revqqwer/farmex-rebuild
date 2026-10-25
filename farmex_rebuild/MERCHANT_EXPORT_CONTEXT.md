# Dışa aktarım zamanı ve kimlik bağlamı

`merchant_export_context.py`, dosya adında kullanılan iki kaynak yardımcısının sınırlı modelidir. Bilgisayar saatini veya oyunu kendiliğinden okumaz. Kaynak gözlemleri olmadan bir karakter adı, kod sayfası veya tarih üretmez.

`00466dc4` `_time` ve `_localtime` çağırır, dönen struct'tan dokuz DWORD kopyalar. Kaynak ifade:

    signed(tm_mday).signed(raw_tm_mon).signed32(tm_year + 1900)  signed(tm_hour)-signed(tm_min)-signed(tm_sec)

Alanlar `%i` ile sıfır dolgusu olmadan yazılır. Yıl eklemesi DWORD taşmasıyla modellenir. Ay için +1 yoktur: Ocak gözleminde0 kullanılır. İki boşluk tarih ve saat parçalarını ayırır. Model takvim doğrulaması, saat dilimi veya Python datetime düzeltmesi eklemez. Dokuz DWORD gözlemi yoksa kendi güncel saatini kullanmaz. Null localtime için kaynakta kopyadan önce güvenli alternatif saptanmadı; model boş tarih uydurmaz.

`004632b4` girişte `GetCurrentProcess` çağırıp sonucunu saklar; sonraki gövdede bu değer kullanılmaz. Kaynak import kimliği ayrıca sabitlendi. Model bu normal çağrı gözlemini de ister. Ardından root pointer, storage ve data okumaları ayrı EAX gözlemleridir. Storage işaretsiz olarak16'dan büyük/eşitse data pointer/storage count ile kopya yardımcısı çağrılır. Aksi halde data pointer okuması yine yapılır; taze inline offset tekrar okunur ve owner+offset üzerinden255 byte istenir. Null owner kaynak akışında otomatik boş ada çevrilmez.

Kopya yardımcısının ANSI sonucu Unicode'a, sonra yeniden ANSI'ye dönüştürülür. İki dönüşüm ve cleanup ayrı gözlemlerdir. İlk kopya byte'larının final çıktıya aynı kalacağı varsayılmaz. Assignment tamamlanmadan `ansi_result` yoktur; assignment sonrası cleanup eksikse atanmış sonuç korunur. Yardımcıların içindeki read/page-protection, managed allocation veya SEH yan etkileri yürütülmez.

Zaman modeli, kendi x86 sürecinde sabit kimlikli CC32260MT `_localtime`/`_sprintf` referansında15 epoch gözleminde0 fark verdi. Bu, orijinal `00466dc4` yordamının çalıştırılması değildir. Gerçek oyunun saat dilimi/CRT globali, pointer kimliği veya son adı yakalanmış sayılmaz. İlgili kanıtlar `FarmexBot_merchant_CRT_zaman_native_kaniti.json` ve `FarmexBot_merchant_export_baglam_kod_kaniti.json` içindedir.

İlk bağlam API aşamasında11 yeni testle toplam4316 Python testi geçti. Sonraki controller/UI aşamasında toplam4330 test ve tam GUI1037 kontrol/11form/18sekme geçti. Kaydet düğmesi, açık bağlam sağlandığında kendi gerçek dosyasını yazar; otomatik oyun kimliği/tm/kod sayfası sağlayıcısı henüz bağlı değildir. Güncel kapsam MERCHANT_TXT_EXPORT_VALIDATION.json ve MERCHANT_TXT_EXPORT.md içindedir. Bu API yeni pakete dahil edilir; tam source native/oyun eşliği sertifikası değildir.
