# Hareket ve Genie yardımcılarının kaynak analizi

Sonraki UI bağı: ayrıntılı yardımcı seçeneğiyle bu modeller Chat Komutları denemesinde kullanılabilir. 2772 test ve tam gizli UI geçti. Aşağıdaki UI bağlantısı bulunmadığına ilişkin notlar ilk aşamanın kapsamını anlatır. [Güncel ayrıntılı deneme](COMMAND_HELPERS_UI.md).

20 Ekim 2026. Korunmuş eski ve güncel Richard ikililerinde beş yardımcıdan toplam **290 talimat kaydı** disk baytlarıyla doğrulandı. Import adresleri kimlikleriyle normalleştirildiğinde bu kapsamdaki gövdeler aynı. Bu kayıt Ghidra/PE kanıtıdır; yeni REA Evidence çıktısı veya canlı yürütme sonucu değildir.

Bağımsız uygulama: `motion_genie_helpers.py` artık bu operand sırasını uygular. **13 yeni testle toplam 2742 test geçti (6.720 saniye)**. Hareket ve Genie planları, chat komutlarına isteğe bağlı typed alt sonuç olarak bağlanır; yardımcı adresi ve fiziksel push argümanları tam eşleşmelidir. Tam alt sonuç bile üst yardımcı için ayrı normal dönüş gerektirir. Arayüzdeki ayrıntılı gözlem adaptörü bu yeni planlara henüz bağlanmadı; mevcut arayüz normal-dönüş örneklerini kullanır.

## Hareket: `004646b4`

1. `553e7c` globalindeki adres, DWORD okuyucu `0045dc44` ile okunur. Sonuç yerel değişkende tutulur.
2. Sonuca taze `554014` offset'i eklenerek BYTE `1` doğrudan yazılır.
3. Aynı köke taze `554018` eklenerek birinci stack argümanının DWORD bitleri yazılır.
4. Aynı köke taze `55401c` eklenerek ikinci stack argümanının DWORD bitleri yazılır.
5. Aynı köke taze `554020` eklenerek BYTE okuyucu `0045dbdc` çağrılır. Düşük BYTE tam `2` değilse `00465f30(1)` çağrılır.

Chat merkez komutunda fiziksel push sırası Y sonra X olduğundan birinci stack argümanı X bitleri, ikincisi Y bitleridir. Bu yardımcı kendi başına float dönüşümü yapmaz; çağıranın verdiği 32 bitleri kopyalar. Diğer çağıranların sayı türleri ayrıca izlenmelidir. DWORD okuyucu sıfır dönerse bile üç doğrudan yazımdan önce kök-null kontrolü yoktur; bu yol güvenli atlama olarak modellenemez.

Son yardımcı `00465f30`, taze `553e80` globalindeki adresi doğrudan dereference eder, fiziksel olarak `1` ve verilen argümanı push eder, taze `553f50` hedefini çağırır. Dolaylı hedefin ABI'si ve gerçek etkisi burada doğrulanmadı.

## Genie: `00466cc4`

Önce `553e80` adresindeki DWORD okunur. Buna taze `554178` eklenip ikinci DWORD okunur; bulunan nesnenin taze `55417c` ve `554180` alanlarından **iki seçenek de** okunur. İlk argümanın düşük BYTE'ı sıfır değilse ilk seçenek, sıfırsa ikinci seçenek saklanır. İkinci seçenek, ilk dal seçilse de önceden okunmuştur.

Sonra kaynak ayrı bir doğrudan çağrı zinciri kurar: `553e80` yeniden okunur ve dereference edilir; `554178` yeniden okunup nesne ECX'e alınır. `1` ve seçilmiş değer push edilir. Taze `554200` vtable offset'i, `[ECX]` tabanına eklenir; buradaki hedef `CALL EDX` ile çağrılır. Önceki okuyucuların döndürdüğü nesne ile bu taze ECX'in aynı olduğu varsayılamaz. Bu son doğrudan dereference'lar için null guard yoktur.

## Okuyucuların önemli yan etkisi

`0045dc44` ve `0045dbdc` sıradan salt okunur okuyucular değildir. Null adres için sıfır dönerler; diğer durumda sırasıyla 4 veya 1 bayt için `VirtualProtect(...,0x40,...)` çağırırlar. Başarısızsa sıfır, başarılıysa doğrudan okunan değer döner. Bu gövdelerde eski korumayı geri yükleyen çağrı yoktur. BYTE başarısında yalnız AL yazılır; üst EAX byte sonucu olarak yorumlanmamalıdır.

İnceleme sırasında bu yordamlar çalıştırılmadı; oyun belleği okunmadı/yazılmadı ve sayfa korumaları değiştirilmedi. Mevcut bağımsız modellerdeki salt okunur gözlem, kaynak okuyucunun bütün yan etkilerini emüle ettiği şeklinde sunulmamalıdır.

## Açık kalanlar

Güncel initializer offset değerleri, canlı pointer'lar, hata/istisna yolları, dolaylı çağrı ABI'si ve oyun etkisi bu kanıtın dışında. Tamamlanmış fonksiyon veya canlı uyumluluk sertifikası eklenmedi.

## Bağımsız modelin gözlem sözleşmesi

`MotionGenieObservation`, sıralı global DWORD örnekleri, `GuardedReadReceipt` sonuçları, ayrı doğrudan DWORD örnekleri ve normal-dönüş makbuzları alır. Guarded sonuç yalnız kaynak yardımcının normal döndüğü ve EAX değerinin gözlendiği anlamında kullanılır; o yardımcının koruma değişikliği veya hata yolunu emüle etmez. Null adresteki yardımcının normal dönüşünde EAX sıfır olmalıdır. BYTE okuyucunun sonucu düşük 8 bitte yorumlanır.

`plan_movement_helper(x_bits,y_bits,o)` üç inert yazım planını kaynak sırasıyla oluşturur. Her adım `write_moving`, `write_x`, `write_y` normal gözlemini ayrı ister. Root sıfırsa bile kaynakta olmayan erken çıkış eklemez; hesaplanan adreste yazımın normal devam ettiği gözlenmedikçe bekler. Pointer toplamaları 32 bit sarılır. Düşük BYTE tam 2 ise dolaylı çağrı girdilerine bakılmaz; diğer durumda taze kök ve hedef istenir.

`plan_genie_helper(argument_dword,o)` önce iki seçeneği de gözlemler; sonra argümanın düşük BYTE'ını kullanır. Önceki guarded kök/nesne, sonraki doğrudan okumaların yerine kullanılamaz. Son çağrı ECX, hedef ve fiziksel push sırasını taşır; `indirect_target` normal dönüşü ayrı istenir, ABI ve oyun sonucu sertifikalanmaz.

`MotionGenieFrame(helper,push_order)` yalnız ulaşılan gözlemleri önbelleğe alır. Sonraki boşlukta önceki yazım makbuzları, seçenekler ve pointer örnekleri değiştirilmez. Tamamlanan aynı frame yeniden çıktı üretmez. Gözlemler tam konumsal listelerdir; yeni delta listeleri olarak yorumlanmazlar. Bir frame tek çağrıyı temsil eder; yeni çağrı için yeni frame gerekir.

Yeni testler; bitlerin aynen kopyalanması, DWORD sarılması, düşük BYTE sınırları, seçilmeyen seçeneğin okunması, her gözlem eksikliği, adres/width uyuşmazlığı, sonraki eksikte prefix korunması, chat argüman eşleşmesi ve alt/üst dönüş ayrımını kapsar. UI ve native C değişmedi; UI yeniden test edilmedi.

Makine kanıtı: `outputs/FarmexBot_hareket_genie_yardimci_kaniti.json`; üretici: `work/audit_motion_genie_helpers.py`.
