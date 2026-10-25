# BUY başarısızlık gözlemi ve yerel banka rotası aktarımı

19 Ekim2026. BUY bölümündeki **BUY başarısızlık gözlemlerini bağla** seçeneği
varsayılan kapalıdır ve reset/yeni denemede alınır. Bu workbench gözlemi gerçek
oyundan gelmez. Application ayrı BMerchant panel Text/directory/codepage
reader'ını bağlar; SELL reader'ı BUY için tekrar kullanılmaz.

MerchantRunner,BUY setup gecikmesi geçip helper sonucu1olduğunda lazy failure
factory'yi çağırır. Bekleme/result0/diğer phase'lerde JSON parse edilmez.
`parse_buy_failure`, preview planın ulaşılan operandlarına göre alanları
valide eder. Helper normal dönüşü ile helper EAX çıktısı ayrı aşamalardır;
örneğin inventory_returned bilinmiyorsa free_count_dword okunmaz. Inventory
ve bank count için trace'teki read_result, yeni native helper çağrısı değildir.

Örnek **sentetik** girdi:

```json
{
  "inventory_returned": true,
  "free_count_dword": 0,
  "threshold_dword": 0,
  "alarm_byte": 0,
  "policy_results": [2, 2, 2],
  "bank_count_returned": true,
  "bank_count_dword": 1,
  "setup_gate_byte": 0,
  "branch_span_returns": [true, true],
  "route_span_returned": true
}
```

`free_count_dword` hazırlığın count'u değildir; kaynak failure dalında ikinci,
taze helper çağrısına aittir. Bank count da ayrı helper sonucudur. Normal
dönüş bool'ları fixture varsayımlarıdır; `ready` kutusundan doldurulmaz.
192slot sayaç modeli typed API'de kullanılabilir; JSON arayüzü bu aşamada
yalnız explicit raw EAX çıktısını alır ve otomatik192oyun okuması yapmaz.

Parser,typed memory/input/factory nesnelerinin JSON'dan enjekte edilmesini
reddeder. Ulaşılmamış invalid alarm/policy/count/notification tail'i önceki
gap'i maskelemez. Bank unavailable yolunda stop normal dönüşü eksikse sonraki
notification gözlemi okunmaz. `bank_error_returns` nesnesi ortak route input
factory'ye ancak bank/string/call span'ına gelince uygulanır; hata helper
receipt'leri [SELL_BANK_ROUTE_UI.md](SELL_BANK_ROUTE_UI.md) ile aynı tiptedir.

## Rol ve handoff denetimi

Dosya ready import olsa bile dış route/string/helper normal dönüşü eksikse
own phase2ve RoutePage korunur. Current karar bank_route olduğunda tam BUY
failure planı callback'e verilir. RoutePage,BUY veya SELL parent tipini,
complete/status/phase0koşullarını ve child kind/global eşleşmesini denetler:
BUY BMerchant569908,SELL SMerchant5698bc. Yanlış rol veya global etiketiyle
çıplak import handoff sağlamaz. Sonuç yalnız own simülatörü başlatır; native
start/reset/movement veya gerçek banka işlemi değildir.

Gizli UI senaryosu hazırlık envanterini28,ikinci failure gözlemini0olarak
ayrı verir. Bank reader önceki gap'te çağrılmaz; outer return olmadan bekler.
BUY için seçili buy.R(Bekle3) yüklenir; aynı anda SELL'e seçili sell.R(Bekle9)
karıştırılmaz. Yerel Bekle3tamamlandıktan sonra reset yapmadan dosya silinince
missing-file error receipts ile own MerchantRunner durur; önceki handoff
başarısı kullanılmaz. Native global stop veya diğer motorların durduğu
çıkarılmaz.

Sekiz yeni birim test reached-only JSON,normal-return/result ayrımı,stop-before-
notification,typed input injection reddi,lazy setup gate ve rol denetimini
sınar. Önceki960BUY failure/slot scope ve1082panel producer instruction kaydı
ayrı/örtüşebilen kapsamlar olarak yeniden doğrulandı. Native slot memory,
helper/VCL/heap/clock/start ve canlı uyumluluk doğrulanmadı. Oyun eylemi0.
