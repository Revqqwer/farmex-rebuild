# Görev satırları ve NPC listesi — yerel aktarım aşaması

`QuestListFrame`, `QuestCollection` içindeki hazırlanmış kayıtları
`QuestRowSink` ve `QuestNpcSink` içine kaynak sırasıyla aktarır.
`QuestRowFrame`, kaynak `004d540c` yordamındaki satır oluşturma bölümüdür.
Bu API'ler henüz gerçek Yenile düğmesine veya oyun verisine bağlı değildir.

Satır başlığı kaynak tarama kimliği değil **koleksiyon indeksi** olur.
Alt alanlar minimum seviye ve görev adıdır. ANSI görev/NPC adları için açık
Windows kod sayfası gerekir; boş byte dizisi doğrudan boş metindir.
Kod sayfası eksikse sistem varsayılanı seçilmez.

Satır yardımcısının normal dönüşünden sonra NPC alanı yeniden okunur.
`00467d90` üyelik yardımcısının normal dönüşü ile normalize edilmiş AL sonucu
ayrı gözlemlerdir. Yerel Python metin eşitliği, büyük/küçük harf dönüşümü
veya tahmini bir karşılaştırma bunların yerine geçirilmez. Sonuç false ise
NPC dönüşümü, ekleme ve Unicode temizliği sırasıyla beklenir. Mevcut NPC
seçenekleri korunur; HEPSI eklemek daha önceki Yenile başlangıcının işidir.

Döngü her turda güncel koleksiyon başlığından işaretli fark/bölme ile boyut
hesaplar ve işaretsiz karşılaştırır. Yerel kayıt sınırı dışına erişim eksik
gözlem olarak durur; native bellek hatası taklit edilmez. Satır/NPC ekleme
sonrası eksik temizleme veya dönüş bilgisi, oluşmuş öneki geri almaz ve
devamda yeniden ekleme yapmaz. Haricî yerel görünüm değişikliği çatışmadır;
bu kendi yaşam döngüsü politikamız native VCL yarış davranışını kanıtlamaz.

`complete=True` yalnız bu aktarım aşamasının bittiğini belirtir. Son durum
`rows_and_npcs_emitted_sort_pending`, `sort_verified=False` olur.
Kaynağın sonraki `00506b78` çağrısı, eşit anahtarlardaki sıra, Yenile'nin
son temizlemeleri ve bütün olayın UI bağlantısı hâlâ açıktır.

Saklanan iki PE dosyasıyla instruction karşılaştırması:
proje kökündeki `outputs/FarmexBot_gorev_satir_kaniti.json`.
Eski sürümün import thunk adresleri güncel sürümden 0x1c önce bulunur;
her sürümün kendi operandları ve baytları ayrı doğrulanır.
Bu bir yeni REA decompiler çalışması veya canlı çalışma kaydı değildir.
