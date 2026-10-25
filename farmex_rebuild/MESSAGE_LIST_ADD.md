# Flood satırı ekleme

REA `0045ca20`126 assembly kaydı, Richard'ın iki sabitlenmiş sürümünde incelendi. `message_list_add.py` yalnız normal yolun kendi işlem planını üretir. Native VCL/CRT çağrısı veya oyun eylemi yapmaz.

Giriş sınırı `0045ca30`, SEH kurulumu sonrasıdır. İlk olarak message(stack+10), sonra channel(stack+c) by-value argüman kopya dönüşleri beklenir. Ayrı yakalanmış stack+14 gecikme DWORD'u **signed32 olarak5'ten küçükse** satır oluşturulmaz ve derleyici çağrılmaz. İki argüman temizliği yine ayrı gerçekleşir. Negatif değerler bu daldadır; unsigned karşılaştırma veya clamp eklenmedi.

Kabul dalı: `TListItems.Add` normal dönüşü → yakalanmış item EAX → kanalın Unicode dönüşümü → `TListItem.SetCaption` → geçici Unicode temizliği → mesajın Unicode dönüşümü → SubItems virtual+3c → temizlik → gecikmenin Unicode dönüşümü → aynı SubItems virtual+3c → temizlik → typed `MessageListFrame` → bağımsız üst çağrı dönüşü → kanal ve mesaj argüman temizliği. Dönüşüm metinleri yakalanmış değerlerdir; Python codec veya `str(delay)` native sonuç yerine kullanılmaz. Item EAX0 için kaynakta olmayan başarı kontrolü eklenmedi.

UI intents, gerçekleşmiş ekran değişiklikleri değildir. Yeniden derleyici UI satırlarını bağımsız ve taze okur; önceki ekleme intentlerinden sonuç satırları uydurulmaz. Daha sonraki temizleme veya child dönüşü eksikse önceki intentler ve tamamlanmış child korunur. Aynı frame tamamlandığında yeniden çalıştırılmaz.

Kaynak çağrı taraması: başlat/durdur callback `004b169c` yalnız `0045cbac` çağırır. Liste derleyicisi ekleme `0045ca20`, iki silme callback'i `004b14a4/004b14dc` ve genel ayar çağrısından ulaşılabilir. İki silme callback'inde önce ayrı virtual UI işlemi, sonra561f55 kapısı vardır. Virtual slotların tüm semantiği ve silme callback modelleri bu aşamada uygulanmış değildir. Ekleme düğmesi `004b1558`108 kayıtla analiz kapsamına alındı; butonun parser/ANSI/ComboBox zinciri henüz bağımsız runtime modeli değildir.

10 yeni test,5 sınırı/negatif DWORD'lar, bağımsız kopyalar, Unicode captures, intent prefix korunması, child/üst dönüş ayrımı ve kaynakta olmayan kontrollerin eklenmemesini denetler. Gerçek UI bağlama, native string/heap/SEH/virtual dispatch ve canlı gönderim açık kalır.
