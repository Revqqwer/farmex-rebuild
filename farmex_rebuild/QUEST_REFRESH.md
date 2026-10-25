# Yenile — birleştirilmiş yerel akış

`QuestRefreshFrame`, önceden ayrı olan aday, kayıt, koleksiyona ekleme ve
satır/NPC aktarımı aşamalarını `004d6668` sırasıyla birleştirir.
`QuestRefreshState` yalnız kendi kayıt/görünüm verilerimizi tutar.
Oyun erişimi veya otomatik native yardımcı çalıştırması içermez.

Başlangıç sırası: NPC seçeneklerini temizle, HEPSI dönüşümü/ekleme/temizliği,
seçimi sıfır yap, görev satırlarını temizle, koleksiyonun son/baş iterator'larını
al ve erase çağrısını bekle. Opaque erase sonrasında boş koleksiyonu gösteren
açık başlık gerekir; kapasite veya adres tahmin edilmez. Bu gözlem gelene kadar
görünümdeki bilinen temizleme öneki korunur.

Üç geçici string başlangıcından sonra bölge sorgusu ve bölge adı çözümü
beklenir. Beş ad karşılaştırması kaynak sırasındadır; her literal karşılaştırması
kendi temizliği döndükten sonra dallanır. Bölge bulunamazsa dört string
temizlenir ve tarama/sıralama yapılmadan yerel akış biter.

Bölge varsa **0..30000 dahil** indeksler `QuestPreparedFrame`'e gider.
Reddedilen adaylar ad üretimine girmeden sonraki indekse geçer. NPC adı
hariç tutulan kayıt eklenmez, fakat ilgili geçici string temizliği beklenir.
Kabul edilen kayıt `QuestAppendFrame`'e gider. Yeniden ayırma dalındaki
`004d7030` son-iterator normal dönüşü artık `004d71b0` öncesinde ayrı beklenir.
Eksik gözlemde aynı aday/alt frame devam eder; bilinen ekleme tekrar edilmez.

Tarama sonrası `QuestListFrame`, satırları ve NPC seçeneklerini üretir.
Ardından `AlphaSort` normal dönüşü ve sıralama politikası ayrı ele alınır:

- `captured`: tam ve açık bir satır permütasyonu gerekir; BOOL dönüşünden
  kendiliğinden bir sıra çıkarılmaz.
- `owned`: bağımsız sürümün 0..255 seviye alanındaki kararlı yerel sırası
  kullanılır; native eşit anahtar sırası olduğu iddia edilmez.

Son dört string temizliği ve epilog bitmeden Yenile tamamlanmış sayılmaz.
Profil/veri nesneleri veya kendi görünümümüz beklerken dışarıdan değiştirilirse
yeniden denemeyle değişikliği benimsemek yerine çatışma sürer.
Bu, kendi yaşam döngüsü politikamızdır; native eşzamanlılık kanıtı değildir.

Doğrulama: 4842 yerel test, 15.879 saniye; iki saklanan Richard sürümünde
1684 instruction kaydı baytlarıyla denetlendi. Bu sayı Yenile ve iterator/erase
gövdelerinin yeniden kontrolüdür, bitmiş fonksiyon sayısı değildir.
Kanıt ve test kaydı proje kökünde
`outputs/FarmexBot_gorev_yenile_akisi_kaniti.json` ve
`outputs/FarmexBot_gorev_yenile_test_sonucu.json` dosyalarındadır.

Gerçek Yenile düğmesine sağlayıcı bağlantısı, GUI doğrulaması, native
allocator/refcount/SEH eşliği ve canlı oyun veri edinimi henüz açık.
Dağıtım ZIP'i bu API aşamasında yeniden oluşturulmadı.
