# NPC seçimine göre görev filtreleme

Gerçek `cmbQuestNPCList` seçim olayı, `QuestNpcFilterFrame` ile mevcut görev
koleksiyonunu kullanarak görünen listeyi yeniden kurar. Yeniden tarama veya
koleksiyondan silme yapmaz. Sağlayıcı `set_source_quest_filter_provider` ile
ayrıca bağlanır; otomatik oyun sağlayıcısı yoktur.

Kaynak callback önce mevcut seçim indeksini okur. Filtre yordamı görünen
satırları temizler; seçili Unicode metni ANSI'ye dönüştürüp geçiciyi temizler.
HEPSI karşılaştırması ve literal temizliği ardından tüm kayıt veya tek NPC
dalına geçer. İki dal da güncel başlık boyutunu her turda yeniden hesaplar.
Tek NPC dalı kayıt+18'i karşılaştırır; eşleşen satır başlığı kayıtların özgün
koleksiyon indeksidir. Sonrasında AlphaSort, seçili ANSI temizliği ve epilog
ayrı beklenir. Seçim-1 için HEPSI varsayılmaz; native indeks hatası açık kalır.

API varsayılanı, kaynak eşitlik sonuçlarının açık gözlem olarak verilmesidir.
Bağımsız arayüz `owned_bytes` modunu açıkça kullanır: kod sayfasıyla üretilen
seçili ANSI byte'ları ile kayıt NPC byte'ları tam eşit karşılaştırılır.
Büyük/küçük harf katlama veya alt dize arama yapılmaz. Bu kendi sürümümüzün
politikasıdır; native AnsiString kod sayfası dönüşümü/alias semantiği
doğrulanmış değildir. Seviye sıralamasının eşit anahtar politikası da yereldir.

Dinamik NPC seçenekleri ve seçimi çalışma zamanı durumundadır. Başlangıçta
boş tanımlanan profil combo alanına dinamik indeks yazılmaz. Böylece Yenile
ve filtreleme sonrasında profil doğrulaması diğer ayarları reddetmez.
Profil değişimi çalışma zamanı verilerini ve eski sağlayıcı/timer'ı iptal eder.
Yenile veya metadata işlemi beklerken başka bir filtre başlatılmaz.
Filtre beklerken combo ve rakip görev düğmeleri devre dışıdır.

Eksik kod sayfası/dönüşte temizlenen veya üretilmiş satır öneki korunur;
tamamlanmış boş liste sonucu verilmez. Sağlayıcı değişimi bekleyen filtreyi
iptal ederken görev koleksiyonunu korur. Yenile'deki alt satır dönüşümü hata
verirse de düzeltmeden sonra kayıt/satır öneki tekrarlanmadan devam eder.

14 filtre birim testi ve Yenile dönüşüm hatası için bir regresyon eklendi.
Gerçek combo olayı NPC/Other/HEPSI seçimleri, özgün indeksler, sıralama,
koleksiyonun korunması, gizli formda devam, sağlayıcı/profil iptali ve profil
geçerliliğiyle kontrol edilir. Tam test ve GUI kanıtı
`QUEST_NPC_FILTER_UI_VALIDATION.json` içindedir. Kaynak byte kanıtı proje
kökünde `outputs/FarmexBot_gorev_NPC_filtre_UI_kaniti.json` dosyasıdır;
iki saklanan PE'de776 instruction kaydı yeniden denetlenmiştir.

Görev ayrıntıları, seçili Al/Ver, native eşlik ve canlı oyun edinimi açıktır.
Bu filtreleme, oyun tarafında görev alma/iptal etme onayı değildir.
