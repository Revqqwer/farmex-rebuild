# Takip denemesinin panel bağlantısı — 19 Ekim 2026

Davranış denemelerine **Takip** seçeneği eklendi. Bu deneme her adımda Genel > Takip panelinin etkinlik, lider seçimi ve nick değerlerini yeniden alır. Genel class-panel anahtarı ve HP/MP gibi ilgisiz sayısal alanlar bu yolu etkilemez. Manuel radyo düğmesi kendi UI grubunda lider seçimini kaldırır; kaynak compiler'ın lider-only mod seçimi korunur.

Gözlem girdisi varsayılan `{}` olduğundan oyun dalına ulaşıldığını veya helper dönüşlerini varsaymaz. “Sentetik örneği doldur” yalnız açıkça seçilmiş yerel fixture verir: X10/Y20, lider dalında Y20, isim dalında Y24. Gerçek oyun verisi veya gönderilmiş hareket değildir. Gerçek gözlemler bağlanana kadar bu ekran bir doğrulama aracıdır.

`FollowTrial` ve ulaşılan alanları tüketen `parse_follow_sample`, önceki isim/ID durumunu adımlar arasında taşır. Kullanılmayan JSON alanı parse edilmez: devre dışı takip, party sayısı sıfır veya boş isim sonraki yanlış alanlarda hata üretmez. Her helper normal dönüşü ayrıdır. Seçilen own UTF16 karşılaştırması bile normal dönüş eksikliğini doldurmaz.

Aynı isim cached ID'yi kullanır; panelde nick değişince önceki isim ve cache source sırasıyla güncellenir. Sonraki lookup dönüşü eksikse bu önceki own değişiklikler korunur. Hatalı yeni JSON son tanıyı temizler; eski hareket sonucu tekrar başarı olarak gösterilmez. Sıfırla own takip durumunu temizler. Hareket isteği ile onun normal dönüşünün bilinmesi ayrı kalır.

10 yeni birim testi dahil **2574 test, 7.305 saniye** geçti. Gizli UI kontrolü gerçek checkbox/radio/text widget'larından lider→isim geçişini, güncel nick'i, cache reuse/invalidation, eksik dönüşü, stale tanı temizliğini ve ilgisiz bozuk HP girdisinden izolasyonu denetler. Tam UI sonucunun kaydı FOLLOW_UI_VALIDATION.json dosyasındadır.

Compiler envanterine üç doğrudan takip girdisi eklendi; toplam 247'dir. Dört UI kontrolünden manuel radio doğrudan source getter girdisi değildir. Envanter dışında 275 düzenlenebilir yol kalması, 275 eksik özellik anlamına gelmez. Statik kaynak kanıtı önceki 572 talimatlık denetimdir; yeni native davranış kanıtı eklenmedi.

Otomatik oyun callback'i, canlı gözlem üreticileri, native string/lookup/float/hareket etkileri ve gerçek oyun uyumluluğu tamamlanmadı. Hiçbir oyun hareketi veya ağ işlemi yürütülmedi.
