# Satış pazarı izleme ve yeniden açma kararı

18 Ekim 2026: `merchant_sell_monitor.py`, erişilmiş aşama 6 için
`00421eb8..0042209d` caller dalını verilen gözlemler üzerinde modeller.
`MerchantSnapshot.sell_monitor_inputs` ile `MerchantRunner` içine bağlanır.
Bu API için workbench giriş kontrolleri henüz yoktur.

## Kaynak sırası

İlk okuma reopen BYTE +c9'dur. Sıfırsa başka saat, süre veya gösterim gözlemi
istenmez. Nonzero ise dakika DWORD +cc ile 60000 çarpımının alt 32 biti signed
olarak kullanılır. GetTickCount örneğinden kurulum damgası +10'un yalnız alt
DWORD'u çıkarılır; sonuç yine signed32 olarak yorumlanır. Damganın üst DWORD'u
bu dalda okunmaz. Bu hesap aşama 5'in signed64 açılış bekleme hesabından ayrıdır.

Elapsed >= interval ise kaynak phase DWORD +4'ü sıfırlar ve ortak epiloga
atlar. Geri sayım dalına girmez. Model yalnız bu yazıyı planlar; runner'ın
`restarting=True` ve `restart_due` sonucu kendi orkestrasyon bilgisidir.
Gerçek pazarı kapatma veya tekrar açma işlemi bu kararla kanıtlanmaz.

Süre dolmamışsa kaynak iki ayrı signed IDIV yapar:

```text
display_seconds = trunc(interval / 1000) - trunc(elapsed / 1000)
```

Negatif bölmede sıfıra doğru kesilir; farkın tek kez bölünmesiyle değiştirilmez.
Ardından `00421f47..0042209d` string/gösterim/cleanup span'ının normal dönüşü
ayrı verilmelidir. Eksik dönüşte model tamamlanmaz ve runner aşama 6'da kalır.
Gösterilecek signed sayı planlanır; gerçek VCL metni veya UI etkisi uygulanmaz.
BUY izleme dalındaki çanta sayımı bu SELL dalında yoktur.

## Kanıt ve doğrulama kapsamı

`work/audit_sell_monitor.py`, hash ile sabitlenmiş eski ve güncel dosyalarda
**242 caller talimat kaydının** baytlarını doğrular. GetTickCount import kimliği,
byte/dword alanları, signed branch, iki IDIV ve phase yazısı ayrı kontrol edilir.
Adresleri değişen dört opaque wrapper'ın **184 talimat kaydı** ayrıca diskten
doğrulanır; bu, helper iç etkilerinin eşdeğerliğini veya çalışmasını kanıtlamaz.
Rapor `outputs/FarmexBot_satis_izleme_kod_kaniti.json`.
Ghidra statik kanıtıdır; REA Evidence değildir. Örtüşen audit kayıtları benzersiz
bir kapsam toplamı olarak toplanmaz.

13 yeni test; kapalı reopen, ulaşılan eksik alanlar, 59999/60000 sınırı,
ayrı span dönüşü, iki IDIV, negatif elapsed, DWORD sarması, minute çarpımı,
ham tipler ve bound runner davranışını sınar. Tam çalıştırmada **1906 test geçti**
(6.919 saniye). UI değiştirilmedi; genel UI smoke bu aşamada tekrarlanmadı.

`work/verify_sell_model_flow.py`, mevcut profil/liste/maliyet/session/slot/açılış
senaryosuna izlemeyi ekler: verilen açılış yanıtının kurulum damgası kullanılır,
999 ms elapsed için span eksikliği bekletir, verilen normal dönüş izlemeyi
tamamlar, 60000 ms elapsed phase 0 yeniden açma kararını üretir. Yerel kuyruk
iki kayıtta kalır. Test girdileri canlı yakalama veya sunucu ACK'sı değildir.
Phase 0'a dönmek sonraki kapatma/açma döngüsünü çalıştırmış sayılmaz.

Ortak fonksiyon epiloğu, exception/unwind, string/VCL iç etkileri, callback
eşzamanlılığı ve gerçek oyun producer'ları bu modelin dışındadır. Orijinal
DLL/oyun çalıştırılmaz; bellek erişimi, paket gönderimi veya canlı uyumluluk
kanıtı oluşmaz. Statik analiz, kendi model testi ve canlı doğrulama ayrıdır.
