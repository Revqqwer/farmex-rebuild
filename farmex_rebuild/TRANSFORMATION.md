# Transformation yapılandırma ve kullanım API'si — 19 Ekim 2026

`transformation.py`, dört panel alanını derler, 004c8498 skill seçimini ve 004c8388'in yerel kayıt üretimini modeller. Periyodik TS işçisi veya rota engelinin çalışma koşulları tamamlanmış sayılmaz. Yeni model bu tur EnginePage'e bağlanmadı.

| Kaynak alan | Doğrulanan üretim |
|---|---|
| +20 BYTE | Transformation etkinlik seçimi |
| +21 BYTE | Ayarlar üretildiğinde koşulsuz 1 |
| +22 BYTE | Rota işlemlerinde kullanmama seçimi |
| +24 DWORD | Combo indeksinin skill kimliği |
| +28 DWORD | Signed bekleme değeri ×1000, düşük 32 bit |

18 indeksin kimlikleri kaynak compare/store zincirinden doğrulandı. İndeks −1 veya eşleşmeyen başka bir değer kaynak varsayılanı olan ilk skill'e gider. Bekleme derleyicisi açıkça sınırlı signed decimal32 politikasıdır; Delphi parser'ın bütün biçimlerini emüle etmez. Native ayar yordamının hata/exception yan etkileri modellenmedi.

Skill seçici önce verilen kimlikle 00464268 çağrısının ayrı normal dönüşü ve EAX sonucunu ister. Yalnız AL sıfır değilse ilk kimlik kullanılır. AL sıfırsa kimliğe 2000 eklenir, DWORD taşması korunur ve ikinci kontrol yapılır. İki kontrol de sıfırsa cast planı üretilmez. EAX'ın üst bitlerinin nonzero olması AL sıfır kontrolünü değiştirmez.

Cast gövdesi 38 baytlık `31 06` kaynak şablonunu kullanır. Seçili skill offset2'ye, taze actor DWORD'u offset6 ve offset10'a dört bayt olarak kopyalanır. Potion paketindeki lowWORD kopyası burada uygulanmaz. Actor normal dönüşü, actor değeri ve üç memcpy dönüşü ayrı gözlemlerdir.

`TransformationFrame` tek açık helper çağrısını temsil eder. Bilinen kontrol/actor/copy öneklerini eksik gözlemler arasında korur. Hazır payload yalnız own kuyruğa delay0 ile eklenir; gate/tick gözlemleri ayrı kalır. Dış cast dönüşü beklerken aynı kayıt ikinci kez eklenmez. Gate0'ın bilinen skip sonucu da yeniden denenmez. Sender veya oyun bağlantısı çağrılmaz; kayıt ACK değildir.

Kaynakta ayrıca stop/Town sonrasında ayrı 569140 baytıyla bu helper'a gidilen dar caller bölümü bulundu. Bu kaydı, genel periyodik kullanım ve rota engeli akışıyla eşitlemedik. İncelenen ikilide etkinlik/reset/rota/bekleme alanlarının mutlak adres baytları bulunmadı; dolaylı veya başka modüldeki okuyucular bundan elenemez. Bu nedenle otomatik TS'nin tamamlandığı söylenmez.

12 yeni test dahil **2586 yerel test, 7.936 saniye** geçti. İki korunmuş ikilide producer bölümü, dört published event/form alanı, seçici, serializer ve dar caller toplam 552 talimat kaydıyla doğrulandı. Şablon ve StrToInt/memcpy import kimlikleri diskten kontrol edildi. Kapsamlar başka denetimlerle örtüşebilir; yeni tam-fonksiyon veya canlı uyumluluk sertifikası değildir. Bu Ghidra/disk/form/import kanıtıdır, REA Evidence değildir.

UI değişmedi ve bu tur UI testi tekrarlanmadı. Gerçek skill kontrolü, actor okuması, native kopya/kuyruk/cast etkileri, periyodik tetikleme ve canlı oyun uyumluluğu açıktır.
