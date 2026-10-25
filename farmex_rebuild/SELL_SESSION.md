# Hazırlıktan satış oturumuna geçiş

18 Ekim 2026: `merchant_sell_session.py`, `00420efc` içindeki
`00421279..0042134b` normal geçişini kendi state ve kuyruğu üzerinde modeller.
Giriş, phase2/setup-result0ve BYTE+58nonzero dalının ulaşıldığı açık bağlamdır.
İlk başarılı setup çağrısının gate'i açıp dönmesi mevcut runner'da ayrı kalır.
`SellSessionFrame` phase2/nonzero gate dışında kurulamaz.

`work/audit_sell_session.py`, iki ikilide86talimat kaydının baytlarını,
GetTickCount import kimliğini ve `6801` başlangıç tamponunu doğrular. Rapor
`outputs/FarmexBot_satis_oturum_kod_kaniti.json`. Statik Ghidra/data/import
kanıtıdır, REA Evidence veya native yürütme değildir. Kayıtlar önceki geniş
auditlerle örtüşebilir; benzersiz toplam olarak eklenmez.

Normal sıra:

1. Slot14..41used-byte alanları `+0x59+slot=0` yapılır.
2. QWORD+98toplamı, QWORD+a0net değeri ve DWORD+84pazar-sayacı sıfırlanır.
3. Liste index DWORD+88=0, inventory index DWORD+8c=14yazılır.
4. Oturum-ready BYTE+38=0yazılır.
5. Taze GetTickCount sıfır genişletilerek QWORD+40'a yazılır.
6. `004c7710` için2bayt `68 01`, delay0yerel enqueue planı yapılır.
7. Ayrı normal enqueue dönüşünden sonra phase DWORD+4artırılır.

Source bu aralıkta item-pending+28ve item-stamp+30alanlarını sıfırlamaz;
frame bunları önceki own `SellSlotState` içinden korur. Setup gate+58dekorunur.
QWORD resetleri modelde tek alan olarak gösterilir; kaynak iki DWORD store'u
arasındaki native kesinti/istisna veya eşzamanlı gözlem emüle edilmez.

Saat eksikse reset prefix'i prospective state'te görünür, accepted state girişte
kalır. Queue clock/gate, session clock'tan bağımsızdır. Gate0normal yolda kayıt
olmadan phase ilerleyebilir. Gate nonzero iken yerel kayıt oluşup normal-return
gözlemi eksikse cached queue kaydı tekrar eklenmez. Tamamlanan frame idempotent'tir.
Hiçbir local enqueue veya phase artışı session-ready/sunucu ACK'i üretmez.

`MerchantSnapshot.sell_session_execution`, tekrar başarılı setup sonucunda
runner'ı bu karara bağlar. Eksik handoff, phase2'yi ilerletmez. Tamamlanmış
handoff, source index/slot/phase ve session damgasını own runner'a aktarır.
Saat damgasının doğru alanına yazılması, dış runner'ın tüm wrap/timeout
politikalarının native eşdeğeri olduğunu kanıtlamaz. Bound alan yoksa eski
normal-clock demo yolu ayrı kalır. UI henüz bu handoff girişini sunmaz.

## Birleşik yerel doğrulama

`test_merchant_sell_flow.py` ve `work/verify_sell_model_flow.py` şu zinciri gerçek
profil şeması ve açık kendi örnekleriyle çalıştırır:

```text
profil -> liste -> derived cost -> setup gate
  -> session reset / 6801 local queue
  -> supplied 680101 ready reply
  -> fresh selection -> explicit-CW x87 -> 6803 slot local queue
  -> supplied 6803 pending-clear reply -> phase4 boundary
```

Bir kayıt için maliyet100, net97ve iki kuyruk kaydı üretildi:
`6801`, `68034d0000000200320000000000`. Saat/return/CW gap'leri caller'ı bekletir.
Session ready ve item pending yalnız ayrı sağlanan byte örneklerinden değişir;
bunlar yakalanmış veya doğrulanmış sunucu yanıtı değildir. Queue drain edilmez.

Rapor `outputs/FarmexBot_satis_birlesik_model_testi.json`. Deneme source pazar
açma helper'ını çalıştırmaz. Sonradan [SELL_OPENING.md](SELL_OPENING.md) operand
planı ve ayrı helper-return örneğiyle phase5bekleme sınırına genişletildi.
Güncel [SELL_OPEN_WAIT.md](SELL_OPEN_WAIT.md) devamı, dört verilen UI-span
dönüşü ve taze toplamlarla phase6 sınırına ulaşır; native UI yürütmesi değildir.
Phase0/1için kapalı/clear
girdileri own fixture'dır; gerçek kapatma kanıtı değildir. Orijinal CRT, oyun,
driver veya native game ABI çalıştırılmaz. Bu **birleşik model** doğrulamasıdır,
canlı uçtan uca bot testi değildir.

10yeni session testi ve1birleşik senaryo eklendi. Bu bağın ilk tam Python çalıştırmasında
**1865 test geçti** (7.343 saniye). Maliyet ve hazırlık gizli UI kontrolleri de
yeniden geçti. UI düzenlenmedi, genel smoke son maliyet-modu aşamasındaki
kayıttır. Native callback/heap, gerçek producer'lar, pazar açılışı ve canlı
uyumluluk açık kalır.
