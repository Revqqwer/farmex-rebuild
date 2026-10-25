# Manuel relog başlangıcı ve durum kaydı

`relog_entry.py` iki ayrı normal yol içerir. Ham gözlemler `JailObservation`
üzerinden gelir; hiçbir oyun, Windows, UI, bellek veya kuyruk çağrısı yapılmaz.

| Yordam | Kaynak sıra |
|---|---|
|00412efc /19talimat|Giriş;562202 byte=1; taze5539f8->form->458button->vtable94, EDX0 sanal çağrı;553c7c/553c80 DWORD=0;462738 sonucu **tam1** ise561ef8 bağlamıyla4c7e0c; ayrı çıkış.|
|00412ed0 /12talimat|Giriş;553f6c tazeDWORD->45dc44 normal ve EAX->50b2d4;461b24 normal ve EAX->50b2cc;4619b8 normal ve EAX->50b2d0; ayrı çıkış.|

Manuel başlangıçtaki flag ilk UI okumasından önce yazılır. UI normal dönüşü
gelmeden sayaç sıfırlama veya bağlantı çağrısına geçilmez. Bağlantı101hex gibi
AL1/fullDWORD farklı değer olduğunda kuyruk helper'ı çağrılmaz.562208 pending
bayrağı bu19talimat içinde yazılmaz; başarılı yeniden giriş çıkarımı yapılmaz.
4c7e0c opak sınırdır; çağrılması gerçek gönderim/bağlantı değişikliği kanıtı değildir.

Durum kaydında üç EAX sonucu dönüş sırasıyla ayrı yazım niyetleri oluşturur.
FFFFFFFF,0 gibi değerler aynen tutulur; ek bir başarı/ID doğrulama kapısı eklenmez.
461b24 ve4619b8 içinde string/UI yardımcıları vardır; bunlar bu modelde ham
dönüşlerdir. Sonuçlar tahmini sunucu/kanal/karakter ID'leriyle doldurulmaz.
45dc44 içindeki gerçek bellek erişimi/koruma davranışı yürütülmez.

`DisconnectRoutineObservation.snapshot`, bu12talimatlık modeli otomatik veya
manuel kurulum yolundaki412ed0 çağrısına isteğe bağlı bağlar. Alt giriş ulaşılan
kenardan türetilir; alt prologue/normal/EAX/epilogue ayrı gerekir. Alt model
tamamlansa bile dış `relog_start` veya `runtime_snapshot` dönüşü ayrıca gerekir.
Bağlandıktan sonra gözlemi kaldırmak opak dönüşle atlamayı sağlamaz; opak dönüş
tüketildikten sonra geriye dönük bağlama reddedilir. Disabled veya yalnız geri
sayım yolları bu alt modeli oluşturmaz. Önceki yazım önekleri eksik sonraki
yardımcı/çıkış sırasında korunur.

Önceki `relog_start` etiketi kaynak412ed0 çağrısının model adıdır: bu12talimat
durum kaydeder; yeni thread veya oturum başlatma sertifikası değildir.

REA ile iki yeni function analizi alındı ve mevcut441talimatlık caller analizi
yeniden kullanıldı. Eski/yeni sabitlenmiş modüllerde12+19+441+10button callback,
toplam964talimat kaydı byte doğrulanır. Yardımcıların iç semantiği, native
prologue/epilogue/SEH/ABI, tam fonksiyon davranışı ve canlı uyumluluk açık kalır.
