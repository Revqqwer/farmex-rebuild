# Durum mesajında kaynak mod/durum seçimi

`session_status_selection.py`, güncel004f9f68 içindeki004f9fda..004fa097 arasındaki50 instruction'lık normal seçim akışını modeller. Başlangıç aşamasına ulaşıldığı açık gözlemle belirtilir. Bunun öncesindeki getter ve diğer çağrıların gerçekten tamamlandığı varsayılmaz.

561f6f bayrağının sıfır/nonzero değeri mesajdaki exclusive baytını0/1 üretir.561f58 modu ayrı ayrı ve taze okunarak0,1,2,3 ile karşılaştırılır. İlk eşleşme sırasıyla1,2,3,4 mesaj baytını üretir; hiçbir karşılaştırma eşleşmezseff kalır. Birinci okumadaki değeri sonraki karşılaştırmalarda tekrar kullanmak kaynak akışı değildir.

56209c ilk okuması geçici durum baytını seçer. Sonraki bütün normal dallar bu baytı tekrar yazsa da ilk kaynak okuması modelden kaldırılmadı. Ardından462738 yardımcısının ayrı normal dönüşü ve tam EAX sonucu gerekir. Yalnız EAX tam olarak1 olduğunda bağlı durum dalına girilir; düşük AL=1 olması tek başına yeterli değildir.

| Koşul | Taze56209c sıfır | Taze56209c nonzero |
|---|---:|---:|
|462738 EAX!=1|0a|33|
|EAX==1,561f60 bot bayrağı sıfır|09|35|
|EAX==1,bot bayrağı nonzero,561f6c sıfır|02|34|
|EAX==1,bot bayrağı nonzero,561f6c nonzero|01|01|

Son satır56209c alanını tekrar okumaz. İlk56209c okuması her durumda gereklidir. Bot bayrağı bağlantısız dalda okunmaz;561f6c bot bayrağı sıfırken okunmaz. Observation/frame yalnız ulaşılan değerleri tüketir; önce tüketilen değerler ve normal dönüş makbuzları bir sonraki ilerletmede değiştirilemez.

`SessionSourceWireFrame`, bir çağrıya ait kalan ham getter/ad girdilerini, türetilmiş oranı ve bu seçimi kendi mesaj üreticisine bağlar. Orandaki bölme hatası seçim okumalarını ve mesaj üretimini durdurur. Bütün normal seçim dalları doğrudan004fa097 serileştirme sınırına ulaşır; bu giriş seçim tamamlanınca kaynak akışından türetilir. Seçim öncesindeki diğer getter'ların etkileri ve serileştirme içindeki metin/CRT etkileri hâlâ gözlem sınırıdır. Tampon dönüşümünün taze global uzunluk WORD gözlemi ayrı kalır. Tamamlanmış çerçeve yeniden ilerletilince aynı sonuç korunur.

Model `mode_byte`, `status_byte`, `exclusive_byte`, `ratio_division_eax` için bağımsız hazır değer kabul etmez; bunları kaynak gözlemlerinden üretir. Kalan getter sonuçları ve serileştirilmiş ad byte'ları hâlâ açık girdilerdir.462738 gövdesinin anlamı, native çağrılar, istisnalar ve canlı uyumluluk doğrulanmadı. Bileşik sonuçtaki `full_builder_verified` ve native/live bayraklarıFalse kalır.

Kaynak denetimi iki sürümde339'ar instruction'ın678 kaydını, seçim aralığında50'şer instruction'ın100 kaydını doğrular;100 zaten678'e dahildir. Yeni REA çağrısı yapılmadı: doğru decoded hash'e bağlı mevcut339 instruction'lık REA kaydı tekrar eşleştirildi.12 yeni test taze okuma, kısa devre, tam EAX karşılaştırması, durum matrisi, tüketilmiş girdiler ve bileşik aşama sınırlarını denetler.

Tam kanıt: `outputs/FarmexBot_oturum_mod_durum_kaniti.json`; denetim: `work/audit_session_selection.py`.
