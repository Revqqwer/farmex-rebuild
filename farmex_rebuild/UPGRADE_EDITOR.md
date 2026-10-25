# Upgrade seçim ve Anvil ID düğmeleri

Güncel ek:4677 aşamasında ID AL Text setter'ının oluşturduğu parametre
event'leri own UI üreticisine bağlandı. Bekleyen inner frame bitmeden üst
cleanup ilerlemez. Kapsam UPGRADE_PARAMETER_UI.md; native VCL olay zamanlaması
ve runtime/SEH etkileri yine sertifikalanmış değildir. Aşağıdaki4646 notları
önceki editor aşamasının kapsamını anlatır.

4646 Python testi ve yeni tam yerel GUI1037 kontrol/11 form/18 sekme geçti.
UPGRADE_EDITOR_VALIDATION.json kapsamı kaydeder. Upgrade sekmesinin bütünü
ve gerçek item işlemleri tamamlanmış sayılmaz.

Tüm Itemleri Seç, açık raw561f55 gözleminden sonra her loop testinde fresh
signed count alır. Ulaşılan satır checked=true olur; caption sayıya çevrilmez,
subitems/duplicate satırlar korunur. Tekrar basmak seçimi kapatmaz. Sayı
setter'lar arasında büyüyebilir/küçülebilir. Kendi uzun listemiz64 fazda yield
edip100ms timer ile devam eder; tüketilen gate ve indeks korunur.

ID AL,561f55 guard'ını kullanmaz. Ayrı TargetIdFrame alt gözlemleriyle full
DWORD hedefi alır;0 ise edit metni değişmez. Nonzero DWORD signed32 olarak
%i biçiminde yazılır;65536 daraltılmaz,FFFFFFFF -> -1. Format ve cleanup
normal dönüşleri ayrıdır. Getter normal dönüşü eksikken hedef varsayılmaz;
format eksikken text yazılmaz; setter sonrası cleanup beklenirken metin
bir daha yazılmaz. Kendi Tk setter/profile alanı güncellenir; kaynak OnChange
yardımcısının runtime global/exception etkileri bu aşamada uygulanmaz.

İki actual button, explicit provider yokken own adapter politikasıyla disabled
kalır. Provider kurunca kaynak tasarım izin veriyorsa açılır. Missing gate veya
normal gözlemde success uydurulmaz. Own FIFO/reentrant click, hidden form,
partial selection prefix ve profile/provider generation invalidation vardır.
Native callback'in monolitik zamanlaması veya yarışları taklit edilmiş değildir.

Gerçek GUI testi iki düğmeyi invoke eder: flag0 select no-op, invalid caption
satırlarının işaretlenmesi, tekrar basınca toggle olmaması, full target/-1,
zero hedef, bağımsız getter/format/cleanup, text prefix, gizli formda devam,
80-row chunk sırasında profil iptali, reentrant FIFO ve stale provider sınanır.
Ortak oyun eylem kuyruğu değişmez.1944 event/helper/formatter instruction
kaydı iki pinli dosyada doğrulanır; mevcut target-frame kanıtı hashleri korunur.
Yeni başarılı REA decompile çağrısı yoktur. Oyun bellek/ağ/eylem IO0.

Sıradaki Upgrade açıkları: Listeyi Yenile envanter/name/filter üreticisi ve
actual düğme; start/stop/Armor ve gerçek parameter callback bağları; source
gate/target/normal gözlemlerinin otomatik edinimi; native VCL/SEH/heap/CP ve
uçtan uca güncel oyun uyumluluğu.
