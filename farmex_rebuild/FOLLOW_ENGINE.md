# Takip modeli — 19 Ekim 2026

19 Ekim takip UI bağı: Davranış/Takip her adımda gerçek panel seçimlerini kullanır; default boş gözlem bekler, açık sentetik fixture ayrıdır. Ulaşılan JSON alanları, cache invalidasyonu ve stale tanı temizliği bağlandı. **2574 test geçti (7.305 saniye)**; tam gizli UI1037kontrol/11form/18sekmede geçti. Native hareket/canlı uyumluluk açık. Ayrıntı: [FOLLOW_UI.md](FOLLOW_UI.md).

`follow_engine.py`, paneldeki takip ayarlarını bağımsız bir yapılandırmaya çevirir ve 0040e2c0 yordamının açıkça ulaşıldığı bildirilen 0040e550 takip dalını modeller. Önceki hareket dallarının buraya ulaştığı varsayılmaz. Bu tur EnginePage/aralıklarla çalışma veya canlı hareket bağı eklenmedi.

Panel üreticisi etkinlik baytını +1e8'e, lider radyo düğmesi seçiliyse mod1'i, değilse mod2'yi +1ec'e ve Unicode nick'i +1f0'a yazar. Manuel radyo düğmesi doğrudan okunmaz; dört panel olayının tamamı aynı ayar yordamını çağırır. Compiler üç gerçek okuma girdisini kullanır; checkbox/radio değerleri bilinen bool, metin bilinen Unicode olmalıdır.

Lider dalında party sayısının signed DWORD olarak pozitif olması gerekir. Lider kimliği WORD'dan sıfırla genişletilir ve lookup'a gönderilir. Dönen pointer için kontrol unsigned nonzero'dur; negatif signed yorumuyla reddedilmez. X/Y ofsetleri, float helper normal dönüşleri ve FSTP sonrası binary32 bitleri ayrı gözlemlerdir.

İsim dalında ikinci mod okuması ayrıca istenir. Tek seferlik önceki-isim başlatması için ayrı dönüş ve oluşan isim gerekir. Boş-isim karşılaştırması, geçici string temizliği tamamlanmadan erken çıkış yapmaz. Önceki isimle eşitlik UTF16 modelinden veya açık RTL flag gözleminden gelir. İsim değişince ayrı assignment dönüşünden sonra önceki isim güncellenir ve cached ID sıfırlanır. ID sıfırsa isim lookup yapılır; sıfır değilse tekrar kullanılabilir. Entity lookup sıfır dönerse cache temizlenir. Önceki own değişiklikler sonraki gözlem boşluğunda korunur.

Kaynak literal 5.0'dır. FUCOMPP sonrası status WORD ve AH45 maskesi eşit/küçük/unordered durumlarını atlar; hareket için kesin büyüklük gerekir. İsim dalında Y'ye ayrıca 4.0 eklenir. Native FPU rounding tahmin edilmez: post-FADD/FSTP bitleri açık gözlemdir. Hareket isteği ayrıca helper normal dönüşü olmadan tamamlanmış plan sayılmaz. Gerçek hareket yürütülmez.

13 yeni test dahil **2564 test, 6.766 saniye** geçti. Signed party sayısı, WORD kimlik, unsigned pointer, taşan adres, FPU maskesi, ikinci mod okuması, isim/cache invalidasyonu, erken çıkışlar, eksik helper dönüşleri ve Unicode karşılaştırma kimlikleri sınandı. UI değişmedi; bu tur UI regresyonu tekrarlanmadı.

İki korunmuş ikilide panel üretici bölümü, dört published event, form alan kayıtları, ulaşılan takip bölümü ve eşitlik yardımcıları 572 talimat kaydıyla doğrulandı. 5.0/4.0 literal baytları ve boş metin kaynağı dosyadan kontrol edildi. Ghidra/disk/form/import kanıtıdır, REA Evidence değildir. Opak string işlemleri, lookup/koordinat/mesafe/hareket helper etkileri ve canlı uyumluluk açık kalır; iki bütün fonksiyonun tamamlandığı iddia edilmez.

Kapsam taraması ayrıca UI/compiler envanterinin dışında kalan 278 düzenlenebilir kontrol yolunu kaydetti. Bunlar özellik sayısı değildir; bazıları editör, alias veya başka modelin girdisi olabilir. Takibin üç compiler alanı artık bilinen API-only durumundadır. Arayüzden motor tüketimi ve gerçek oyun bağlantısı sonraki işlerdir.
