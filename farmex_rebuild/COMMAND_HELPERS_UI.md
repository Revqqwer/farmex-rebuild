# Chat komutlarında ayrıntılı yardımcı denemesi

20 Ekim 2026. **Chat Komutları** bölümündeki **Ayrıntılı yardımcı denemesi** seçeneği, ulaşılan sekiz eylemi bağımsız yardımcı modellerine bağlar. Kapalıyken önceki dispatcher/normal-dönüş denemesi korunur. Açıkken üst `action:<key>` dönüşü tek başına yeterli değildir: alt model de gerekli gözlemleri tamamlamalıdır.

**Ayrıntılı sentetik örnek** düğmesi bu seçeneği açıp uydurulmuş pointer, saat ve olumlu dönüş gözlemleri yükler. Panel checkbox'larını veya komut metinlerini değiştirmez. Diğer panelinde yalnız açık ve metni tam `go` olan komutlar çalışılan dala girer. Örnekler gerçek oyundan alınmış veri veya başarılı oyun eylemi değildir.

## JSON sözleşmesi

Önceki üst alanlar (`helper_returns`, merkez koordinat/FSTP ve Genie guard gözlemleri) korunur. Yardımcı girdileri `helpers` nesnesinin altında eylem anahtarına göre verilir:

| Eylem anahtarı | Alt JSON |
|---|---|
| `disconnect`, `stand` | `gate`, ardından yalnız gerekirse `tick`. |
| `town` | `buffer_address`, sıralı `global_samples`, ayrı `helper_returns`. |
| `return_center` | `global_samples`, `guarded_reads`, gerekirse `direct_samples`, ayrı `normal_returns`. |
| `genie_start`, `genie_stop` | Aynı operand gözlem yapısı; iki seçenek okuması ve taze doğrudan çağrı zinciri ayrı korunur. |
| `bot_start`, `bot_stop` | `values` ve ayrı `normal_returns`; ulaşılan değer/span adları [başlat/durdur kapsamında](BOT_SWITCH.md). |

Global/doğrudan örnek satırı `[adres, DWORD]` biçimindedir. Guarded satırı `{"address":8192,"width":4,"eax":4096,"normal_returned":true}` biçimindedir. Bu, yalnız kaynak okuyucunun opaque dönüş gözlemidir; VirtualProtect çalıştırılmaz. Normal dönüş henüz bilinmiyorsa o satırın EAX değeri ayrıştırılmaz.

Örneğin yalnız DC alt girdisi `{"helpers":{"disconnect":{"gate":1,"tick":100}}}` olabilir; bu tek başına üst karşılaştırma veya eylem dönüşlerini sağlamaz. Gate sıfırsa tick okunmaz. Gate bir kez tüketildiyse sonraki tick gözleminde eski gate yeniden ayrıştırılmaz.

## Devam ve sıfırlama

Adapter yalnız ulaşılan alanı ayrıştırır. Tam konumsal örnek listeleri kullanılır; önce tüketilmiş satırlar daha sonraki boşlukta yeniden ayrıştırılmaz. Ulaşılmayan Town, kapalı komut veya Genie guard'ının atladığı dal içindeki bozuk veri denemeyi bozmaz. Ulaşılan bozuk alan ise sonuç, parent frame, bütün yardımcı frame'leri ve yerel kuyruğu temizler.

DC ve kalkma aynı çağrı denemesinde tek yerel kuyruğu kullanır. İkisi de enqueue edilirse kayıt ID'leri 1 ve 2, payload'lar `00` ve `12 01` olur. Tam alt sonuç üst dönüş beklerken yeniden adımlanması kayıt çoğaltmaz. Kuyruk yalnız bu yakalanmış mesaj denemesine aittir; gerçek kaynak kuyruğunun oturum ömrü veya canlı gönderimi modellenmiş sayılmaz.

Aynı HEX/panel/kod sayfası/ayrıntılı-seçenek snapshot'ı aynı çağrıya devam eder. Bunlardan biri değişirse yeni frame ve boş yerel kuyruk açılır. Sıfırla veya örnek düğmesi de yeni deneme başlatır. Aynı HEX'li iki ayrı canlı mesajı ayıran capture kimliği henüz yoktur.

## Doğrulama sınırı

Town'ın thread yardımcısı normal dönmüş olsa bile callback çalışması doğrulanmış sayılmaz. Hareket/bot durdurma store listeleri inert projeksiyonlardır; belleğe yazım makbuzu değildir. Hiçbir adapter native çağrı, thread, süreç erişimi, koruma değişikliği, network gönderimi veya oyun eylemi yapmaz. Arayüz ve test sonucu canlı uyumluluk kanıtı değildir.

Kaynak: `command_helper_trial.py`, `chat_commands_trial.py`, `simulation_ui.py`. Alt kaynak kapsamları: [DC/kalkma/Town](COMMAND_HELPERS.md), [hareket/Genie](MOTION_GENIE_HELPERS.md), [başlat/durdur](BOT_SWITCH.md).

## Doğrulanan sonuç

14 yeni adaptör testiyle toplam **2772 test geçti (6.945 saniye)**. Tam gizli UI **1037 kontrol/11 form/18 ana sekmede** geçti. Sekiz typed yardımcı, ortak iki kayıtlı kuyruk, Town geç boşluğundan prefix koruyarak devam, tekrar adımda kayıt çoğaltmama ve hatalı girdide stale temizliği sınandı. Bu aşama mevcut dört kaynak audit’ini tüketir; yeni ikili talimat veya canlı oyun kanıtı eklenmedi. UI/compiler271 ve envanter dışında251yol değişmedi; bunlar tamamlanma yüzdesi değildir. Makine kaydı: `COMMAND_HELPERS_UI_VALIDATION.json`.
