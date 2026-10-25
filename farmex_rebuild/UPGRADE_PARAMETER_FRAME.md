# Upgrade sıralı parametre üreticisi

Bu belge4670 API aşamasının kaydıdır. Güncel üç gerçek alan olayı ve nested
ID AL bağlantısı UPGRADE_PARAMETER_UI.md / UPGRADE_PARAMETER_UI_VALIDATION.json
içindedir;4677 test ve yeni tam GUI geçti. Aşağıdaki eski bağlanmamış UI
notları bu API aşamasının tarihsel kapsamıdır. Native/live sertifika değildir.

4670 Python testi geçti. Yeni API/test dosyaları app/smoke_ui closure dışında;
4658 tam GUI kaynak/log hashleri aynıdır. Yeni GUI çalıştırılmadı.
UPGRADE_PARAMETER_FRAME_VALIDATION.json kapsamı sınırlar. Gerçek üç
OnChange olayı ve start/stop/worker bağlantısı henüz bu API'ye bağlı değildir.

Kaynakta üç olay aynı4f7620 üreticisine gelir; her published wrapper561f55
guard'ını kullanır. Üretici önce combo Text'ini ANSI'ye dönüştürüp object+0
string alanına atar ve geçici ANSI/Unicode string'leri temizler. Sonra fresh
Anvil Text'i/helper0 sonucu lowDWORD object+8'e; sonra fresh bekleme Text'i/
helper2000 sonucu lowDWORD object+4'e yazılır. Her yazım kendi daha sonraki
cleanup normal dönüşünden öncedir. Yeni model atomik snapshot commit etmez;
bilinen prefix, sonraki eksiklikte kalır. Native etkileri geri aldığı iddiası
yoktur. Parent callback dönüşü ve native heap/SEH eşliği sertifikalanmaz.

Scroll boş değilse somut effective codepage gerekir; host ACP tahmin edilmez.
Kendi Windows flags0 counted dönüşümü embedded NUL'u korur. Empty Unicode
yolunda pinli RTL length<=0 dalı default CP okumadan temizler; kendi boş
temsilimiz bytes empty/codepage None'dır, canlı pointer/nullness kanıtı değildir.
Conversion ve assignment normal dönüşleri ayrıdır. Text read/init/get normal
onayları ayrı tutulur; elde edilmiş Text poll ile tekrar okunmaz. Sonraki
Anvil/bekleme alanı gerçekten ulaşıldığında fresh okunur.

Kabul edilen sayı yolu mevcut pinned RTL Int64 scalar parser'ını kullanır;
hex/signed64/unsigned hex bitleri ve lowDWORD korunur. Helper normal receipt
olmadan alan yazılmaz. Reddedilen parse için helper'ın döndürdüğü rawQWORD
ve normal dönüş ayrıca verilmelidir.0/2000 kaynak argümanları kaydedilir,
fakat geçersiz girişte native fallback başarı sonucu tahmin edilmez. Scalar
helper45ef80 exportunda45efd9..45efe4 exception-only aralığı retained normal
listing dışında kalır; byte'ları audit'te saklanır. Catch/unwind bütünü açık.

Başlatma yardımı4f7af8 combo'yu doğrudan okumaz. Object'in cached ANSI üyesi
00403d84 ile Unicode'a çevrilip scroll aramasına verilir. Bu nedenle güncel
combo snapshot'ını doğrudan başlatmanın yerine koymak doğru değildir. Yeni
API state'i bu bağımlılığı hazırlamak içindir; gerçek başlat/durdur ve parametre
callback bağları sonraki aşamadır. Legacy demo compiler ayrı kapsamda kalır.

12 yeni test gate0/unknown, prefix sırası, ayrı normal/cleanup, hex/lowDWORD,
fresh sonraki alan, invalid sonuç/receipt gereği, CP/empty/NUL ve terminal
cancel/idempotence'i sınar.2128 source/RTL instruction kaydı iki pinli dosya
ve standart RTL kanıtıyla doğrulandı. Yeni REA decompile veya kaynak bot
çalıştırması yoktur. Oyun bellek/ağ/eylem IO0. Diğer özellikler, native runtime
ve güncel oyun canlı uyumluluğu açık kalır.
