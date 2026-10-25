# Transformation panelinden yerel kaynak denemesi

Yerel deneme listesindeki **Transformation** seçeneği, Genel bölümündeki dört gerçek kontrolü kullanır: etkinlik kutusu, bekleme metni, rota işlemlerinde kullanmama kutusu ve18 seçenekli beceri listesi. Bu bağlantı, periyodik TS tüketicisinin çözüldüğü anlamına gelmez.

`transformation_trial.py` panelin sabit bir anlık görüntüsünü alır. Boş JSON,0040929a kaynak üretici girişinde bekler; ayar yazımı veya cast uydurmaz. Getter normal dönüşleri ayrı gözlemlerdir. Ulaşıldığında enabled/route/combo sonuçları panelden, parser metni gerçek panel metninden gelir. Bunlar JSON ile çelişkili biçimde değiştirilemez. Parser'ın normal/çözülmemiş istisna yolu ve EAX sonucu ayrıca istenir. Kaynak enabled/rearm önekini yazdıktan sonra parser istisnası varsa önek korunur, sonraki rota/beceri alanları tamamlanmış sayılmaz.

**Panelden sentetik ayar ve açık çağrı örneği** düğmesi kendi açık deneme verisini doldurur. Buradaki strict signed-decimal politika yalnız örneği üretmek içindir; Delphi StrToInt'in bütün biçimleri olarak sunulmaz. Kullanıcının gerçek hesabı, belleği veya servis verisi okunmaz. Sentetik actorDWORD12345678, normal dönüşler ve saat100 bu düğmenin örnek değerleridir.

Ayar üretimi bitince `helper_entry_reached` ayrıcaTrue değilse beceri yardımcısı çağrılmış sayılmaz. True gözlemi yalnız açık bir004c8498/004c8388 helper denemesidir; enabled/wait/route alanlarından periyodik tetikleme türetilmez. Yardımcı seçici, actor, üç kopya, kuyruk gate/tick ve dış cast normal dönüşü için mevcut kaynak modellerini kullanır.38 byte'lık kayıt yalnız kendi kuyruğuna gider. Actor offset6/10'a tamDWORD olarak yazılır; lowWORD'a daraltılmaz.

Aynı çağrı eksik gözlemler arasında ilerler; cast normal dönüşü beklenirken oluşan kayıt tekrar eklenmez. Panel değişince yeni ayar/helper çağrısı başlar ve önceki kendi kuyruk kayıtları korunur. Düğmeyle üretilmiş örnek snapshot hash'i eskiyse reddedilir. **Sıfırla** kendi deneme kuyruğunu temizler. Profil kaydet/yükle dört alanı da korur. Geçersiz JSON önceki sonucu ekranda geçerli bırakmaz.

Bu aşamada scoped UI/compiler envanteri303→307, bunun dışında kalan düzenlenebilir kontrol sayısı219→215 oldu. Bu oranlar özellik tamamlanma yüzdesi değildir. Sınırlı fonksiyon modeli sayısı145 olarak kaldı; yeni bir fonksiyon çözümü diye sayılmadı.

Sekiz birim testi ve gerçek fakat gizli kendi Tk arayüz kontrolü; panel bağını, kaynak girişini, parser exception önekini, kuyruk/clock boşluklarını, tam actorDWORD'u, kopya kayıt oluşmamasını, eski snapshot reddini ve profil roundtrip'i denetler. Geniş UI testine de bu kontrol eklendi. Oyuna paket gönderilmez, native çağrı veya otomatik/periyodik beceri kullanımı doğrulanmış değildir.

Mevcut REA ve disk kanıtları yeniden doğrulandı; bu aşama için yeni REA çağrısı yapılmadı. Ana üretici araştırmasında1465 kayıt, ayrıca örtüşen cast/producer kanıtında552 kayıt kontrol edilir; bunlar benzersiz analiz kapsamı olarak toplanmaz. Kanıt: `outputs/FarmexBot_transformation_panel_bagi_kaniti.json`; test: `smoke_transformation_ui.py`.
