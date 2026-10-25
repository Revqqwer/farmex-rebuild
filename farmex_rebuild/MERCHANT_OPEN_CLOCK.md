# BUY açılışı: kaynak saat kapısı

18 Ekim 2026: `merchant_open_clock.py`, `004220c8` içindeki aşama 4 bekleme
kapısını modeller. `work/audit_merchant_open_clock.py`, eski ve güncel ikilide
toplam 56 talimat kaydının disk baytlarını, karşılaştırma/jump bağlarını ve
`GetTickCount` import kimliğini doğrular. Rapor:
`outputs/FarmexBot_pazar_acma_saat_kod_kaniti.json`. Statik Ghidra kanıtıdır;
REA Evidence veya özgün kodun çalıştırılması değildir. 56 kayıt önceki geniş
auditlerle örtüşebilir; benzersiz talimat sayısına eklenmemelidir.

Pending BYTE `+48=0` ise saat çağrısı yapılmadan açık dalına geçilir. Aksi halde
GetTickCount EAX sonucu sıfır genişletilir, QWORD `+50/+54` SUB/SBB ile çıkarılır.
Üst DWORD sıfırsa düşük DWORD 10000 ile unsigned karşılaştırılır; üst DWORD
sıfır değilse signed negatif sonuç bekler, pozitif sonuç timeout dalına gider.
Eşit 10000 değeri timeout dalındadır. İşlem aşağıdaki 64 bit eşdeğeridir:

```text
bits = (zero_extend(tick_DWORD) - stamp_QWORD) mod 2^64
timeout_path = signed64(bits) >= 10000
```

Bu işlem unsigned32 süre farkı değildir. Örneğin tick=10 ve stamp=0xfffffff0
için sonuç -4294967270'tir; kaynak bekler. Model bunu genel bir “taşma düzeltmesi”
ile değiştirmez. `remaining_ms` yerel açıklayıcı alanıdır; kaynakta böyle bir
sleep veya UI sayacı hesaplandığı iddia edilmez. Ham örnek alanları DWORD/QWORD
olarak doğrulanır; bilinmeyen saat sıfır kabul edilmez.

`MerchantSnapshot.buy_open_clock` açık `BuyOpenClockSample` alır. Yalnız BUY
aşama 4 pending yolunda bu örnek, normal monoton saat farkının yerini alır.
Saat örneği verilmezse önceki monoton politika geçerlidir. Bekleme runner'ı
ilerletmez. Pending temizse örnek due olsa bile açık dalı önce gelir.
Snapshot'ın genel `now_ms` alanı hâlâ monoton olmalıdır; bu, bağımsız ham kaynak
saat gözlemiyle aynı alan değildir.

Arayüzün yanıt örneği modu aşama 4'te mevcut own-caller damgasını ve ayrı
sentetik DWORD tick'i bu girişe bağlar. `work/verify_merchant_reply_ui.py`,
monoton UI zamanı 2^32'yi geçerken kaynak tick'inin sarılması, beklemenin
korunması ve ardından uygun yanıtta ilerlemeyi doğrular. Oyun saati okunmaz.

Kaynak timeout yolu `0040ae0c(00561f34,0)` ile başlar ve string/bildirim etkileri
içerir. Bu model o yardımcıların etkilerini çalıştırmaz. Runner'ın due sonucunda
`open_timeout` ile durması mevcut bağımsız sürüm politikasıdır; özgün timeout
gövdesinin eşdeğeri değildir. Pending temiz dalın VCL/formatlama çağrıları ve
`+58` temizliği/phase artışının tüm native çağrı sırası da bu saat modeliyle
doğrulanmış sayılmaz. Model yalnız kaynak saat kapısını sağlar.

12 yeni test; 9999/10000/10001 sınırı, taşma, pozitif/negatif üst DWORD, signed64
uçları, ham alan doğrulaması ve runner bağlantısını kapsar. Tam birim çalıştırması
1743 test ile geçti (6.382 saniye). Yanıt ve önceki caller için hedefli gizli UI
kontrolleri geçti; genel UI smoke önceki yanıt bağlantısı aşamasında çalıştırıldı.
BUY phase5 için ayrıca [MERCHANT_MONITOR.md](MERCHANT_MONITOR.md) planı eklendi.
Canlı uyumluluk, kalan Merchant phase'lerinin kaynak saatleri ve timeout helper
etkileri açık kalır.
