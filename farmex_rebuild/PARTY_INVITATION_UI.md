# Parti daveti deneme ekranı — 19 Ekim 2026

Davranış denemelerine **Party Daveti** seçeneği eklendi. Her adımda Diğer > Party Davet Ayarları panelindeki etkinlik, tümünü/liste modu, ret ve Party Bug seçimleri ile PartyList caption'ları yeniden okunur. Genel HP/MP alanları ve class-panel anahtarı bu yolu etkilemez.

Captured HEX alanı başlangıçta kısa `2f02`, gözlem alanı `{}` değerindedir. Bu girdiler başarılı bir kabul veya ret üretmez; gerekli gözlemde bekler. “Sentetik Alice daveti örneği” düğmesi açıkça yerel bir örnek doldurur. Ekrandaki action yalnız karar/çağrı planıdır; davet, kabul, ret veya ağ yanıtı gönderilmez.

Codepage açıkça1254veyaUTF8 seçilir. Bu yerel dönüştürme politikasıdır; oyundaki gerçek RTL/codepage ile aynı olduğu kanıtlanmış değildir. Liste satırlarının checked durumu kaynak producer tarafından okunmadığından compiler da bunu filtreleme koşulu yapmaz.

`PartyInvitationTrial` yeni adımda güncel paneli derler ve yalnız ulaşılan JSON alanlarını ayrıştırır. Erken blocker/disabled çıkışları kullanılmayan hatalı filtre alanlarına bakmaz. Tümünü kabul et modu da isim filtresinin normal dönüşünü atlamaz. Kabul/ret ve son cleanup dönüşleri ayrı kalır. Yeni bozuk HEX/JSON, önceki başarılı sonucun tanısını temizler.

8 yeni test dahil **2619 birim testi, 7.604 saniye** geçti. Gizli UI kontrolü gerçek enable/all/list/bug widget'larını, checked olmayan izinli satırı, Alice kabul/Bob ret kararını, filtre boşluğunu, stale sonuç temizliğini ve ilgisiz bozuk HP girdisinden izolasyonu sınar. Tam UI sonucu PARTY_INVITATION_UI_VALIDATION.json dosyasındadır.

Compiler envanterine dört seçim ve liste olmak üzere beş gerçek girdi eklendi; toplam252'dir. Envanter dışında270düzenlenebilir yol kalması270eksik özellik anlamına gelmez. Statik kaynak kanıtı önceki1548talimat denetimidir; bu tur native davranış kanıtı eklenmedi.

Canlı packet yakalama, gerçek yardımcılar, dış hook davranışı, davet yanıtı ve gerçek parti üyeliği doğrulanmadı. CAPTCHA sınırı ayrı ve manuel kalır; bu ekranla ilişkili değildir.
