# Eski işleyiciye bağlam aktarımı — 0046eca8

Güncel ve eski decoded modüldeki 12 talimat dosya baytlarıyla karşılaştırıldı; hepsi aynı. Kaynak, önce 00553e80 içindeki kök-slot adresini alır ve bu adresteki DWORD'u okur. Ardından 005540d4 içindeki ofseti köke ekleyerek yeni bir DWORD okur ve ECX'e koyar. Son olarak 00554228 içindeki saklanmış işleyiciyi çağırır. Çağrı öncesinde açık stack argümanı push edilmez; EBX ve EBP saklanıp dönüşte geri alınır.

Bu küçük yordamın gövdesinde zaman damgası veya 00555e23 bayrağına doğrudan yazım yoktur. Çağrılan işleyicinin etkileri bilinmiyor. Bu nedenle yalnız bu gövdeden zamanlayıcı sıfırlama, başarı veya oyun eylemi sonucu çıkarılamaz. Null/adres koruması da gövdede yoktur; bağımsız sürümün keyfi adres çağırması için bir sözleşme değildir.

Güncel initializer çağrılarındaki 00553e3c taban argümanı ve parametreye bağlı yazımlar ayrıca dosya baytlarıyla doğrulandı:

| Kaynak profil | Başlangıç yordamı | Kök-slot adayı, taban+44 | Alan ofseti, taban+298 |
|---|---|---|---|
| US | 004fd640 | 01128a7c | 000003b0 |
| Steam | 004e4398 | 011eaab0 | 000003b0 |

Taban+44, 00553e80 alanına; taban+298 ise 005540d4 alanına karşılık gelir. Bu kök-slot adayları HP/MP karakter kök-slotundan farklıdır. Dosyadaki initializer değeri, yüklü oyun görüntüsünde aynı adresin/alanın geçerli olduğunu kanıtlamaz.

## Kendi 32 bit programımızdaki ölçüm

`native/context_callback_fixture.c` yalnız kendi iki veri alanını, kök slotunu ve alıcısını oluşturur. Oyun adresi/PID girdisi veya yükleyici içermez. Kaynak callback'in register/stack biçimini kendi değişkenleriyle kurar; oyun veya vendor modülü çalıştırılmaz.

Beş vaka geçti: sıfır ofset, 8 ofset, hizasız 3 ofset, değişen kök ve kaynakta görülen 3b0 ofset. Alıcının gördüğü ECX doğruydu. EBX ve EBP korundu; stack başlangıca döndü. Kendi alıcımız EAX/ECX/EDX/EBX ve carry flag'i kasıtlı değiştirdi. Dış callback EBX'i geri getirdi; EAX/ECX/EDX ve carry değişiklikleri kaldı. Alıcı girişindeki stack farkı 16 bayttı.

Bu ölçümün alıcısı açıkça RET0 kullanır. Gerçek saklanmış işleyicinin ABI'si, parametreleri, thread bağlamı, geçerli pointer'ları veya yan etkileri bununla doğrulanmaz. Önceki 19 HP/MP/disk-hash vakası ayrı tarihsel test kapsamıdır; bu beş vaka onların veya 1554 Python testinin yerine geçmez.

Derleme:

```powershell
.\native\build_context_callback_fixture.ps1 -CompilerPath 'C:\tools\tcc\tcc.exe' -OutputDirectory 'C:\work\context-fixture'
```

Çalıştırılacak dosya kendi `farmex_context_callback_fixture.exe` programımızdır. Beş JSON satırı ve başarılı doğrulamada exit0 üretir. Derleyici ve EXE kaynak paketine dahil değildir. Kanıt kayıtları: FarmexBot_callback_baglam_kod_kaniti.json ve FarmexBot_callback_baglam_native_testi.json. Bu kaynak/fixture çalışması REA runtime Evidence olarak etiketlenmez.
