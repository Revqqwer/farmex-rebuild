# SELL başarısızlık dalı ve yerel banka rotası aktarımı

19 Ekim2026. EnginePage SELL bölümündeki **SELL başarısızlık gözlemlerini
bağla** seçeneği varsayılan kapalıdır; yeni deneme/reset sırasında alınır.
Bu kendi simülasyonumuzdur; gerçek çanta/oyun/ACK gözlemi veya native helper
çalıştırması değildir. Paneldeki SMerchant rota adı/klasör/codepage factory'si
ve RoutePage yerel simülatörü Application tarafından bağlanır.

## İki lazy sınır

MerchantRunner yalnız SELL phase2, setup gecikmesi geçmiş ve helper sonucu1
olduğunda failure factory'yi çağırır. Bekleme/result0/diğer phase/BUY dalı
JSON'u parse etmez. Direct DTO ile factory ve legacy bank gate ile bound
failure aynı ulaşılan dalda kullanılamaz.

Failure planı header/status, alarm, üç bağımsız policy örneği, bank status,
setup gate ve iki bank status span'ını kendi kaynak sırasıyla tüketir. Ancak
route/string/call span'ına gelince panel route-input factory çağrılır. Earlier
gap, stop/disconnect veya bank-unavailable dalı rota okuyucusunu/dosyayı açmaz.
Reader yok veya None ise detailed gap korunur; outer receipt bypass sağlamaz.

`parse_sell_failure` source planın ulaşılan son operandını izleyerek yalnız
o JSON alanının değerini valide eder. Kullanılmayan policy/branch tail ve
bank-error value'ları önceki gap'i maskelemez. Bütün JSON'un sözdizimi ve
bilinen root key'leri başta doğrulanır; JSON callable veya raw route input
enjekte edemez. Native çağrı yoktur. Bank error receipt nesnesi yalnız route
factory ulaşıldığında okunur.

Örnek **sentetik** bank-path verisi:

```json
{
  "header_span_returns": [true, true],
  "alarm_byte": 0,
  "policy_results": [2, 2, 2],
  "status_byte_90": 0,
  "setup_gate_byte": 0,
  "branch_span_returns": [true, true],
  "route_span_returned": true
}
```

Bu bool değerleri oyundan okunmuş değildir; her normal dönüş ayrıca verilen
bir fixture varsayımıdır. `setup_gate_byte` caller'ın own setup_seen durumu ile
uyumlu olmalıdır; ikinci girişte1olabilir. `ready` kutusu failure receipt'lerini
doldurmaz. Missing/nonpositive/unselected route error yolları ayrıca
`bank_error_returns` nesnesinde error_message_returned,path_cleanup_returned,
error_stop_returned,error_notification_returned,error_final_cleanup_returned
boolean gözlemlerini ister. Gerekmeyen path cleanup dalı mevcut modelce atlanır.

## Handoff kapsamı

Dosya importu ready olsa bile outer route/string/helper normal-return receipt
eksikse phase2ve own simülatör korunur. Bütün reached gereksinimler sağlanıp
MerchantRunner **bank_route** kararı döndürdüğünde, yalnız bu çağrının ready,
complete dış failure planı RoutePage'e aktarılır. RoutePage dış planın
bank_route_span_returned/phase0durumunu ve iç bank import planını ayrıca
denetler; çıplak import veya incomplete/wrong parent kabul edilmez. Adımları yükleyip
kendi simülatörünü başlatır; zaman yine yerel +ms adımlarıyla ilerletilir.
Bu native route-start state stores,callback,timer veya movement yürütmesi
değildir. RouteStartExecution sağlanmadı diye native reset alanları uydurulmaz.

Yeni failure factory çağrısında önceki handoff tanısı temizlenir. Sonraki
denemede dosya yoksa önceki ready sonuç kullanılmaz; normal error receipts
sağlandığında own MerchantRunner bank_route_load_failed ile durur. Bu global
native stop etkilerinin veya zaten çalışan başka motorların tamamının
durdurulduğu iddiası değildir.

Dokuz yeni birim test lazy boundaries,parsed prefix,unknown/empty,normal
receipt,factory çatışması ve legacy bypass denetimlerini sınar. Gizli gerçek
own UI testi source preparation'ın matched_count0 sonucunu1e üretir; erken
bozuk JSON bekleme sırasında okunmaz,header gap rota okuyucusuna ulaşmaz,
ready import outer gap'te bekler,receipt sonrası seçili Bekle2 dosyası yerel
simülatörde biter. Reset yapmadan ikinci girişte dosya silme hatası ve stale
handoff temizliği ayrıca sınandı.

498failure-caller ve3076route-caller instruction kaydı, ayrı/örtüşebilen
kapsamlar olarak iki binary sürümünde yeniden doğrulandı. Bunlar yeni native
çalıştırma kanıtları veya toplanabilir completion sayıları değildir.
Üreticiler `work/audit_sell_failure.py`, `work/audit_merchant_bank_route.py`;
Ghidra/disk kanıtıdır, REA Evidence değildir. Oyun belleği/eylemi0; canlı
uyumluluk ve bütün native start/helper zinciri hâlâ doğrulanmadı.
