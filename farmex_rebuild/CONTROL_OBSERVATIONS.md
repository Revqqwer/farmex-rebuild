# Birleşik kontrol gözlem biçimi

Motor denemeleri → Kontrol içinde panel ayarları ve **Birleşik kontrol / yardım / alarm modeli** seçilir. Bu arayüz yalnız yerel plan üretir. JSON, Farmex dışa aktarımı veya canlı oyun yakalaması değildir; verilen normal-return değerleri gözlem varsayımlarıdır. Gerçek gönderim/ACK doğrulaması yapılmaz.

Boş `{}` hiçbir timer, ad veya helper dönüşü oluşturmaz. Önceki NP/coin/level veya saat/party dalı erken dönerse JSON okunmaz. `initial_state` yalnız sıfırlamadan sonraki ilk ulaşılan JSON adımında alınır. Sonraki düzenlemeler kabul edilmiş timer state'ini yeniden başlatmaz. Eksik aşamada kabul edilmiş state korunur; kısmi yazımlar `prospective_state` içinde gösterilir.

Alanlar:

- `initial_state`: `timers` adres→QWORD haritası; `last_activity_qword` ayrı son kutu zamanı. Bilinmeyen değer verilmez.
- `observed_ansi_hex`: yayımlanmış yardım metni yolu→dönüştürülmüş AnsiString hex baytları. Unicode panel metni kendiliğinden kodlanmaz.
- `party_help`: source `party_count`, `outer_tick`, `final_tick`; flag anahtarlı `feature_ticks`, `predicate_returns`, `request_returns`, `post_request_ticks`. Swift için `swift_globals` ve sıralı `swift_samples` ayrıca gerekir.
- `alarms`: `now_tick`, taze `[slot, karşılaştırma_indeksi, ansi_hex]` listesi `name_samples`; ayrı `no_loot` ve `devil_item` normal dönüşlerini içeren `alarm_returns`.

Adres/flag haritası anahtarları decimal veya `0x` biçiminde olabilir. JSON sayıları gerçek integer olmalıdır. İsim örneği verilmemesi eşya yokluğu değildir. `independently_verified` gibi doğrulama iddiaları kabul edilmez. Veri okuma, bellek yazma, clock sorgusu, mesaj, alarm ve süreç kapatma bu araçta yürütülmez.

Aşağıdaki **sentetik örnek**, kaynak Buff yardım bayrağı açık, diğer yardım bayrakları ve Devil alarmı kapalı, NoLoot alarmı açıkken kullanılabilir. Önceki guard koşullarının geçmesi, mode0 ve saatin kapanma koşuluna uymaması gerekir. Panelden metin `+++` olsa da ANSI baytları ayrıca açıkça verilir:

```json
{
  "initial_state": {
    "timers": {"0x553cb4": 0, "0x553cbc": 0},
    "last_activity_qword": 1
  },
  "observed_ansi_hex": {
    "frmMain/MainTab/SheetDiger/GroupBox9/txtHelpChatBuff": "2b2b2b"
  },
  "party_help": {
    "party_count": 2,
    "outer_tick": 10000,
    "feature_ticks": {"0x103": 10000},
    "predicate_returns": {"0x103": 1},
    "request_returns": {"0x103": true},
    "post_request_ticks": {"0x103": 10001},
    "final_tick": 10002
  },
  "alarms": {
    "now_tick": 600001,
    "alarm_returns": {"no_loot": true}
  }
}
```

Model bu örnekte bir yardım çağrısı ve NoLoot alarm isteği planlar. Mesaj/alarm gönderildiği, helper'ın gerçekte döndüğü veya oyunun uyumlu olduğu sonucunu üretmez.


## Maden callback kontrol bağı

Motor denemeleri → Maden içinde panel ayarları ve **Callback içinde panel kontrol modelini kullan** seçilir. Bu seçenek kendi callback yolunu açar; eski callback kilit örneği kutusunun ayrıca seçilmesi gerekmez. Önceki kuyruk/helper normal dönüşleri ve clock hâlâ sentetik örneklerdir. Yeni seçenek kontrol yordamının tamamlanmasını dışarıdan işaretlemez; tipli yerel model üretir.

**Kontrol giriş gözlemi JSON**, `ControlGuardObservation` alanlarını kullanır. Örneğin:

```json
{"np_462718": 1, "coins_46258c": 100000, "level_462670": 80}
```

Gerekirse `stop_returned` ve `town_returned` ayrı boolean olarak verilir. `{}` sorguları bilinmeyen bırakır. Maden hedef ID/adet/mesafe alanları NP/coin/level yerine kullanılmaz. Saat/party devam gözlemleri yukarıdaki ortak kontrol alanlarından, yardım/alarm örnekleri bu belgedeki JSON biçiminden alınır. Her bölüm yalnız kaynakta ulaşıldığında okunur. Kontrol erken dönerse sonraki yardım JSON'u okunmaz; termination çağrı planı normal dönüş sayılmaz.

**Kontrol sonrası kilit JSON** ve **Ara bölüm sonrası kilit JSON** ayrı ve tam kayıt ister:

```json
{"byte": 1, "duration_ms": 2000, "started_ms": 1000}
```

Boş alan kilit sıfır demek değildir. İlk kayıt kontrol/helper'lardan sonraki timer girişini, ikinci kayıt timer ile maden arasındaki henüz çözülmemiş segmentin sonrasını temsil eder. Birincisi süre dolmasıyla sıfırlansa bile ikincisi kendiliğinden doldurulmaz. BYTE 0–255, diğerleri unsigned DWORD olmalıdır. **Örnek ara bölüm normal döndü** ve yanındaki **mode DWORD** da ayrı gözlemlerdir; şu an maden devamı yalnız mode2 için modellenmiştir. Bu kayıtlar bir oyun bellek yakalaması değildir.

Kontrol state'i bu callback denemesi için ayrı tutulur. JSON `initial_state` yalnız sıfırlama sonrası ilk ulaşılan yardım/alarm aşamasında alınır. Sonraki kilit/segment/mode/maden eksikse bilinen timer değişiklikleri yalnız `prospective_state` içindedir. Tam yerel zincir tamamlanınca kabul edilir. Kontrol sayfasındaki bağımsız deneme state'i değişmez.
