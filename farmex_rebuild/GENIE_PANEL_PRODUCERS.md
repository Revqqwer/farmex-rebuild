# Genie arayüz üreticilerinin kaynak bağı

21 Ekim2026. Mevcut güncel Richard snapshot'ında13kontrol, yayımlanmış DFM alan/metot kayıtları ve Ghidra talimatlarıyla eşleştirildi. `work/audit_genie_panel_producers.py` tekrar üretir; kanıt `outputs/FarmexBot_genie_panel_uretici_kaniti.json` içindedir.260benzersiz talimat kaydı disk baytlarıyla doğrulandı. Yeni ikili envanter kapsamı veya13tam özellik iddiası yoktur.

| Kontrol | Ayar yazımı | Modeldeki kullanım |
|---|---|---|
| chGenieWithBot |562194+B8 BYTE|always_b8_byte|
| chGenieStopWithBot |562194+B9 BYTE|ayrı bot durdurma bayrağı|
| chAutoGenieCoupon |562194+BA BYTE|initial/recovery BA|
| chNoRemainGenieTimeTown |562194+BB BYTE|initial/retry/empty BB|
| chNoRemainGenieTimeAlarm |562194+BC BYTE|initial/retry/empty BC|
| chanticropengenie |5690f8+16 BYTE =56910e|general_genie_byte|
| chanticrwaitclosegenie |5690f8+1A BYTE =569112|resume_delay_byte|
| chanticrgenienobotatack |5690f8+17 BYTE =56910f|general_no_attack_byte|
| chbnk |5690f8+41 BYTE =569139|Notice enabled_byte|
| chbnkingenienobotatack |5690f8+50 BYTE =569148|Notice no_attack_byte|
| txtanticrwaitclosegenie |5690f8+1C DWORD =569114|resume_seconds_dword|
| txtbnkgenieclosetime |5690f8+4C DWORD =569144|Notice minutes_dword|
| rdbnkgenie |5690f8+44 DWORD =56913c, değer3|Notice mode_dword|

Kontrol grubu üreticisi4576ec, koruma üreticisi46b928'dir. Olay callback'leri561f55bayrağını sınayıp doğru üreticiye sırasıyla562194/5690f8bağlamını gönderir. Genel worker45a05cçağırıcısı46f0a8da562194gönderir; böylece üretici ve tüketici için yalnız benzer ofset varsayılmadı, gerçek bağlam da eşleştirildi.

`chGenieWithBot` caption'ı “Bot Atack Baslatinca Genie Baslat” ve form ofsetiBD0'dır. Ayrı `chFreeGenie` ofset51C'dedir; caption benzerliğinden bunları aynı özellik saymamak gerekir. İşleyicinin B8dalındaki erken dönüş davranışı kaynakta olduğu gibi korunur.

`rdbnkgenie` için değer3yazımı koşulludur; önceki radyo dalları daha yüksek önceliklidir. Tek başına bu widget'ın true gözlemi kesin mode3sayılmaz. Metin alanları GetText→45ef80dönüşümüyle yazılır; saniye alanında60, dakika alanında30başlangıç literal'i görülür. Sayı dönüştürücüsünün hatalı metin/locale/fallback etkisi bu aşamada çözülmüş sayılmaz.

Bu statik bağlar UI compiler'a yeni alan eklemez ve canlı okuma yapmaz. İşleyicide tekrar okunan bayraklar gerçek oturumda değişebilir; tek sabit konfigürasyon snapshot'ı native eşdeğerlik değildir. Tam model testinin son sonucu3012'dir; çalışma kodu değiştirilmediğinden bu aşamada testler yeniden koşturulmadı. Kaynak korunmuş PE/Ghidra/DFM verisidir; yeni REA Evidence değildir.
