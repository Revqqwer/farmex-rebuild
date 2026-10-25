# Bot başlatma ve durdurma kapsamı

Sonraki UI bağı: ayrıntılı yardımcı seçeneğiyle bu modeller Chat Komutları denemesinde kullanılabilir. 2772 test ve tam gizli UI geçti. Aşağıdaki UI bağlantısı bulunmadığına ilişkin notlar ilk aşamanın kapsamını anlatır. [Güncel ayrıntılı deneme](COMMAND_HELPERS_UI.md).

20 Ekim 2026. `bot_switch.py`, `0040ac18` temel aktivasyon yardımcısını ve `0040ae0c` üst mod dallarını normal yol üzerinde birleştirir. Kaynak kanıtı eski ve güncel Richard'da **1042 talimat kaydını**, alan yazımlarını, string sabitlerini ve import kimliklerini doğrular. Bu korunmuş Ghidra/PE kanıtıdır; yeni REA Evidence veya canlı yürütme değildir.

**16 yeni testle toplam 2758 test geçti (6.975 saniye).** Arayüz ve native C değişmedi; arayüz bu aşamada yeniden test edilmedi. Yeni API, chat başlat/durdur eylemlerine isteğe bağlı typed alt plan olarak bağlandı. Diğer kontrol, maden ve merchant durdurma çağıranları henüz bu alt modele bağlanmadı.

## Temel aktivasyon sırası

Üst yardımcı frame kurulumu ve temel yardımcı frame kurulumu ayrı normal dönüş gözlemidir. Temel yardımcı her iki dalda önce context'e göre BYTE `74`, BYTE `75`, BYTE `49`, DWORD `70`, BYTE `90`, DWORD `94` alanlarını sıfırlar. Bu işlemler, zaten başlatılmış olma kontrolünden de önce gelir.

Argümanın düşük BYTE'ı sıfır değilse context `2c` BYTE'ı okunur. Zaten sıfır değilse UI/notification dalı atlanır. Sıfırsa form aktiflik çağrısının düşük AL sonucu kontrol edilir; sıfır sonucunda ayrı aktivasyon çağrısı gerekir. Caption aralığı normal döndükten sonra context `168` sıfır, `2c` bir olur; bildirim aralığının normal dönüşü ayrıca istenir. Caption kaynak literal'i `Bot Durdur [ F11 ]`, bildirim literal'leri `Bot Baslatildi !` ve `success` olarak doğrulandı.

Düşük argüman BYTE'ı sıfırsa durdurma caption aralığı, context `2c=0`, durdurma bildirim aralığı sırasıyla planlanır. Temel yardımcı dönüşü ayrıca gerekir. Kaynak, bu temel yardımcının argümanını DL yükleyip EDX push ederek geçirir; üst 24 bit için değer uydurulmaz. Dallanma yalnız düşük BYTE'a bağlıdır.

UI/string aralıkları normal dönüş sözleşmeleridir. Unicode dönüşümleri, form pointer ömrü, vtable ABI'si ve bildirim yardımcısının iç etkileri emüle edilmiş sayılmaz. Boşluk öncesi listelenen store'lar da **inert normal-yol projeksiyonlarıdır**; gerçek belleğe yazıldığına dair makbuz değildir.

## Başlatma modları

Her ulaşılan karşılaştırma context `24` DWORD'unu yeniden okur. `mode_for_zero`, `mode_for_two`, `mode_for_four`, `mode_for_five` bu nedenle ayrı gözlemlerdir; kararlı mod varsayılmaz.

| Dal | Normal yol |
|---|---|
| 0 | UI checkbox düşük AL'a göre mevcut veya girilmiş koordinatları seçer. Koordinat yardımcısı/label/cleanup aralıkları normal döndükten sonra context `38=1`. |
| 2 | `0047baa4` çağrısının düşük AL'ı sıfır değilse `38=1`; sıfırsa alan için yeni store yok. Sonraki mod dallarına düşmez. |
| 4 | DWORD `5697e4`, BYTE `569838`, BYTE `569870` sıfır; context `38=1`. |
| 5 | Context `38=1`. |
| Diğer | Temel aktivasyon yine gerçekleşebilir; `38` alanına koşulsuz bir store eklenmez. |

Mod 0 mevcut koordinat yolunda önce Y `004625d8`, sonra X `004625ac` gözlemlenir; koordinat yardımcısının fiziksel push sırası Y, X, context'tir. Normal yardımcı sonucu context `cc=X`, `d0=Y` DWORD projeksiyonlarıyla temsil edilir. Sonraki label aralığı **Y/X getter'larını tekrar çağırır**; label sonuçlarının ilk koordinatlarla aynı olduğu varsayılmaz. Bu label/string aralığı opaque kalır.

Girilen koordinat yolunda GetText/StrToInt içeren Y ve X aralıkları ayrı normal dönüş ve ham EAX gözlemi ister. Negatif değerler ham DWORD bitleri olarak korunur. StrToInt exception yolu normal dönmüş gibi kabul edilmez. Koordinat yardımcısının kendi UI/string gövdesi ayrı opaque sınırdır.

## Durdurma yolu

Taze mode tam 2 ise `0047baa4` durdurma çağrısı yapılır; üst kod bu dönüşün AL değerini koşul olarak kullanmaz. Sonra `004631c8` durum yardımcısının düşük AL'ı **tam 1** ise `004ca4c4` çağrılır. Bu yardımcı, Genie arayüz yardımcısı `00466cc4` ile karıştırılmaz.

Context BYTE `38`, BYTE `118`, DWORD `108`, DWORD `10c` sıfırlanır. Ardından `STOP_GLOBAL_RESETS` içindeki **38 sıralı global store** projekte edilir. Bunların ikisinde `FFFFFFFF`, birinde `0E`, birinde `0D` vardır; hepsini sıfırlamak kaynak davranışı değildir. Son olarak `00464714` hareket-durdurma yardımcısının normal dönüşü ayrı beklenir.

Temel durdurma dahil toplam 49 inert store vardır. Son hareket yardımcısında boşluk varsa bu projeksiyonlar sonuçta korunur; oyuna uygulandığı iddia edilmez.

## Kullanım ve doğrulama sınırı

`BotSwitchObservation(values=...,normal_returns=...)` yalnız açık gözlemleri taşır. `plan_bot_switch(context,argument_dword,o)` eksik gözlemde `request` döndürür. `BotSwitchFrame` tek çağrı için yalnız ulaşılan değerleri ve normal dönüşleri saklar. Sonraki gözlemde önceki koordinat/mod değerleri değişse bile tüketilmiş prefix değiştirilmez; aynı tamamlanmış frame yeniden store uygulamaz. Zaten hiçbir store uygulanmaz; sonuçlar projeksiyondur.

Chat bağında context ve **tam DWORD argüman** fiziksel push sırasıyla eşleşmelidir. Aynı düşük BYTE'a sahip farklı bir DWORD, doğru chat çağrısının yerine geçirilemez. Eksik alt model üst normal-dönüş işaretiyle aşılmaz; tamamlanan alt model de üst `action:bot_start` veya `action:bot_stop` normal dönüşü yerine geçmez.

Testler; base store sırası, zaten başlatılmış dalı, düşük AL sınırları, her taze mode okuması, iki koordinat yolu, sentinel'lar, her ulaşılan gözlem/normal dönüş eksikliği, prefix devamı ve chat argüman bağını kapsar. Gerçek UI, bellek, thread, network veya oyun eylemi yapılmaz. İstisna yolları, kaynak context ömrü, yardımcıların bütün etkileri ve canlı eşdeğerlik açıktır.

Kaynak: `outputs/FarmexBot_baslat_durdur_kod_kaniti.json`; üretici: `work/audit_bot_switch.py`. Uygulama/test kanıtı: `BOT_SWITCH_VALIDATION.json`.
