# Pazar yanıtı durum modeli

18 Ekim 2026: `merchant_reply.py`, mevcut iki Richard ikilisinin `004d82a4`
fonksiyonundaki `004d8e0c..004d90bf` opcode `68` dalını verilen sabit byte dizisi
üzerinde modeller. Ağ dinleme, hook, oyuna erişim veya paket gönderme içermez.
`work/audit_merchant_reply.py` iki dosyanın SHA256 kimliğini, seçilen 472 talimat
kaydının disk baytlarını, import kimliklerini ve aşağıdaki bağları doğrular.
Rapor: `outputs/FarmexBot_pazar_yanit_kod_kaniti.json`. Ghidra kaynaklı statik
kanıttır; REA Evidence nesnesi veya orijinal program yürütme sonucu değildir.

| Dal | Gerekli gözlem | Yerel durum etkisi |
| --- | --- | --- |
| `68 27` / `68 02`, tarayıcı pasif | byte 2'de DWORD kimlik, taze yerel kimlik, eşleşince saat | önce sıfır genişletilmiş saat `+08`, sonra pending `+18=0` |
| `68 01 01` | durum byte 1 | hazır `+38=1`; diğer durumlar önceki değeri korur |
| `68 03` | ek gözlem yok | pending `+28=0` |
| `68 07` | byte 6'da DWORD kimlik, yerel kimlik, eşleşince saat | önce pending `+48=0`, sonra sıfır genişletilmiş saat `+10` |
| `68 28` | byte 2'de DWORD kimlik, yerel kimlik, eşleşince saat | önce pending `+48=0`, sonra sıfır genişletilmiş saat `+10` |
| Tarayıcı aktif, alt tür `27/02/11` | kimlik/saat gerekmez | tarayıcı pending `+0f=0`, AL=0 |
| Tarayıcı aktif, alt tür `05/23` | durum 1 ise `004bc650` normal dönüşü, ardından ayrı `004bf57c` normal dönüşü | tarayıcı pending `+0f=0`, AL=0 |

Tarayıcı aktifken diğer alt türler normal pazar dalına ilerler. `004bc650`
argümanları tarayıcı nesnesi, payload adresi ve uzunluktur; `004bf57c` nesne ve
alt türden türetilen mod 1/2 alır. Bu yardımcıların iç etkileri uygulanmadı;
normal dönüşleri açık gözlem olarak istenir. Normal pazar dalında AL=1 olur.
AL sonucu tek başına sunucunun işlemi kabul ettiğini kanıtlamaz.

Kaynakta `0046f1b8`, `005697e0` adresini `004230d8` üzerinden hem SELL hem BUY
runner'ına geçirir. Bayraklar ayrı uydurulmuş nesneler değil bu ortak nesnenin
alanlarıdır. Kimlik `00462650` EAX sonucu olan DWORD'dur; WORD'e daraltılmaz.
Kimlik eşleşmezse saat çağrısı ve ilgili yazmalar gerçekleşmez.

`plan_merchant_reply` eksik gözlemde kabul edilen durumu korur, kaynakta o
noktaya kadar görülen yazmaları `prospective_state` içinde ayrı gösterir.
Kaynak ham okumalarda sınır kontrolü yoktur; modelin kısa girdiyi reddetmesi
kendi güvenli girdi politikasıdır. Sembolik okuma/çağrı listesi bir native CPU
izi değildir. Saat gözlemleri dışarıdan açıkça verilmelidir; sıfır varsayılmaz.

`merchant_snapshot_from_reply`, açıkça verilen durumu mevcut `MerchantRunner`
girdisine bağlar. Phase 4'te pending açıkken bekleme ve uygun kimlikli yanıttan
sonra phase 5'e geçiş test edilir. İşlem onayı, para veya eşya değişimi üretilmez.
Snapshot'ın genel saati normal artan saat kısıtlarını kullanır. BUY aşama 4
pending dalı için ayrı ham kaynak saat girişi eklendi; [MERCHANT_OPEN_CLOCK.md](MERCHANT_OPEN_CLOCK.md).
Diğer aşamaların native saat davranışı ve tüm runner'ın eşdeğerliği doğrulanmış değildir.

## Arayüzde sıralı yanıt denemesi

`Buy Merchant` ekranındaki “Yanıt örneğiyle bekle” seçeneği varsayılan kapalıdır.
Seçim yeni deneme başlatılırken alınır; çalışma sırasında kutuyu değiştirmek
mevcut denemenin modunu değiştirmez. Hazırlık/çanta örneği seçeneği de ayrı
açılmalıdır. Açma caller'ı tamamlandığında pending bayrağı yeni modele aktarılır.
Aşama 4'te hazır kutusu bu bayrağı otomatik temizlemez.

Hex alanındaki sabit veriyi ve yerel DWORD kimliğini “Aşama 4: yerel örneği işle”
düğmesiyle işleyin. Örneğin `68 28 01 00 00 00` ve kimlik `1` beklemeyi kaldırır;
sonraki normal adım runner'ı aşama 5'e ilerletir. İşleme düğmesi saati veya
runner'ı ilerletmez. Kimlik uyuşmazlığı, kısa veri ve geçersiz girdi durumu
korur. Hex veya kimlik hatası ekranda gösterilir. Kimlik 32 bit işaretsiz sayıdır;
ondalık veya `0x` öneki kullanılabilir. Tarayıcı bu arayüz örneğinde pasiftir.

Bu kontrol yalnız aşama 4'te kullanılabilen sıralı bir denemedir. Native callback
eşzamanlılığı, açma helper'ı sürerken gelen yanıtlar ve diğer phase'lerdeki gerçek
üretici etkileri arayüz bağlantısının kapsamı dışındadır. Yeni deneme eski
yanıtı/durumu temizler. SELL ekranı bu kontrolü göstermez. Kaynak modele ait
diğer alt türler ayrı API üzerinden test edilebilir.

12 hedefli test; kimlik konumu, kısmi durum/yazma sırası, tarayıcı önceliği,
iki bağımsız normal dönüş, eşleşmeme, kısa veri ve runner bağını kapsar.
18 Ekim arayüz bağlantısından sonraki tam Python çalıştırmasında 1731 test geçti
(7.632 saniye). Genel gizli `smoke_ui.py` kontrolü de 1037 kontrol/11 form/18 ana
sekme ve mevcut davranış kontrolleriyle başarıyla tamamlandı; yeni yanıt
seçeneğinin kapsamı aşağıdaki ayrı hedefli kontrolle doğrulandı.
`work/verify_merchant_reply_ui.py` gizli kendi Tk arayüzünde yanlış tam DWORD
kimliği, kısa/bozuk veri, `07` kimlik konumu, açık yanıtla phase geçişi, saat,
kuyruğun değişmemesi, mod seçiminin başlatmada alınması ve reset kapsamını sınar.
`work/verify_buy_open_frame_ui.py` önceki açma caller/kuyruk davranışını ayrıca sınar.
Canlı oyun yanıtlarının özgün programla karşılaştırılması ve uçtan uca pazar
işlemi henüz doğrulanmadı.
