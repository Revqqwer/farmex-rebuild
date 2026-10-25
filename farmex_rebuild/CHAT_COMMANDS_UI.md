# Chat komutları arayüz bağı

Sonraki UI bağı: ayrıntılı yardımcı seçeneğiyle bu modeller Chat Komutları denemesinde kullanılabilir. 2772 test ve tam gizli UI geçti. Aşağıdaki UI bağlantısı bulunmadığına ilişkin notlar ilk aşamanın kapsamını anlatır. [Güncel ayrıntılı deneme](COMMAND_HELPERS_UI.md).

20 Ekim 2026. EnginePage içindeki **Chat Komutları**, Diğer > Chat Komutlarına Göre İşlem Yap panelinin16checkbox/text alanını `ChatCommandsTrial` üzerinden okur. Genel HP veya sınıf-panel ayarlarından bağımsızdır. Bu, kaynak komut dalına girildiği varsayılan yerel gözlem denemesidir; oyun ya da süreç üzerinde eylem yürütmez.

Varsayılan HEX `10`, gözlem JSON'u `{}` olduğundan bilinmeyen prefix/karşılaştırma dönüşleri açık kalır. **Sentetik “go” mesajı** düğmesi ayrıca etiketlenmiş örnek yükler; panelde checkbox açmaz, komut metinlerini değiştirmez. Kod sayfası1254/65001 açıkça seçilir. Örneğin yalnız iki açık komut `go` ise iki çağrı intent'i görülür; diğer checkbox'lar kendiliğinden açılmaz.

Aynı paket, kod sayfası ve derlenmiş panel snapshot'ında aynı frame devam eder. Tamamlanmış aynı girdi yeniden adımlandığında intent listesi büyümez. Sıfırla veya sentetik örnek düğmesi yeni deneme başlatır. Panel/HEX/kod sayfası değişimi de yeni frame açar. Gerçek iki aynı mesajı birbirinden ayıran canlı capture kimliği bu denemede yoktur.

JSON yalnız ulaşılan alanları ayrıştırır. `helper_returns` içindeki `compare:<command>` ve `action:<command>` bool değerleri ayrı normal dönüşlerdir. Genie helper dönüşleri ve raw sonuçları, merkez DWORD'ları ve post-FSTP bitleri ayrı alanlardır. Kaynak karşılaştırmayı kapalı checkbox'ta da yaptığı için gerekli compare dönüşleri atlanmaz. Ulaşılmayan bozuk action/Genie alanı okunmaz; daha önce tüketilmiş Y değeri sonraki X-bit boşluğunda yeniden ayrıştırılmaz.

Bozuk HEX, JSON veya ulaşılan alan hatası önceki `last` sonucu ve frame'i temizler. Mesajın önceki başarılı sonucu hatalı yeni girdide gösterilmez. Kaynak string/float/helper etkilerinin gerçekliği JSON receipt verilmesiyle kanıtlanmaz.

UI/compiler envanteri255'ten271alana çıktı. Envanter dışında251düzenlenebilir yol kaldı; bu sayı eksik özellik veya tamamlanma yüzdesi değildir. Sekiz komutun önceki818talimatlık statik kanıtı kullanılır; tüm chat handler'ı ve helper/native etkileri ayrıca açık kalır.

**8yeni adaptör testiyle toplam2717 birim testi geçti (8.931s).** Tam gizli UI1037kontrol/11form/18ana sekmede geçti. Gerçek checkbox/text değişimi, harf farkı, aynı keyword ile iki intent, normal-return boşluğundan devam, tekrar adım ve stale-frame temizliği sınandı. Hiçbir oyun/native eylem yürütülmedi.
