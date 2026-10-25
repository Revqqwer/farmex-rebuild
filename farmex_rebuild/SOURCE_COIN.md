# Coin okuyucusunun kendi gözlem modeli

Güncel bağ: BUY ve SELL hazırlıkları da aşağıdaki ayrı coin gözlemini kabul eder.
Önceki sayılar ilk okuyucu modelinin tarihsel sonuçlarıdır.

## Hazırlık tüketicileri

`BuySetupObservation.coin_inputs` ve `SellSetupObservation.coin_inputs`,
`SourceCoinObservation` alır. Ham `coins_dword` aynı anda verilemez. Sonuçta
ayrı `coin_plan` saklanır; başarı/başarısızlık/null kökeni kaybolmaz. Bu bağ,
source coin yardımcısının mevcut gözlem modelini çağırır; native API çalıştırmaz.

BUY, önce liste hazırlığını ve boş-yuva sonucunu tamamlar, sonra coin zincirini
ister. Free-threshold başarısızlık kararı bile coin okumasından sonra gelir.
SELL, önce liste ve cost/count yardımcısını tamamlar; count0olsa dahi coin
okuması önce gelir. Önceki bir dal eksikse sonraki coin gözlemleri işlenmez.
Eksik coin zinciri sonraki bütçe/eşik kararını tamamlanmış saydırmaz.

Her çağrı kendi `coin_inputs` örneğini alır. Alarm planının coin'i veya önceki
setup sonucu otomatik taşınmaz. Aynı sayının yeniden gözlenmesi mümkündür, ancak
bu kendi fixture varsayımıdır; gerçek belleğin sabit kaldığının kanıtı değildir.
Control guard, NPC purchase ve BUY opening gibi diğer tüketiciler bu bağın dışında
kalır. Workbench hazırlık kontrolleri hâlâ ayrı ham EAX örneği kullanır; detaylı
guarded-zincir UI alanları eklenmedi.

Birleşik SELL senaryosu100maliyet+1000gözlenen coin=1100toplamını artık explicit
guarded root/offset/API-return/değer örneklerinden üretir. Kapanış, session ve slot
için üç yerel kayıt korunur; gönderim yoktur. `work/verify_sell_model_flow.py`
raporu `setup_coins_from_explicit_guarded_reader_samples` alanını taşır.

9 yeni tüketici testiyle **1983 test geçti** (8.558 saniye). Mevcut BUY hazırlık
604ve SELL liste/setup1162talimat kayıtlı auditleri tekrar geçti; bunlar yeni
benzersiz kapsam toplamları değildir. BUY panel ve SELL maliyet hedefli gizli
arayüz kontrolleri de geçti. UI bu aşamada değiştirilmedi; genel smoke tekrarlanmadı.
Native koruma, bellek producer'ları ve canlı uyumluluk açık kalır.

## Okuyucu modeli

18 Ekim 2026: `source_coin.py`, `0046258c` yardımcısının iki `0045dc44` çağrısını
ve guarded DWORD yardımcısının normal dönüş dallarını modeller. Bellek okumaz,
koruma değiştirmez ve VirtualProtect çağırmaz. Bütün sayılar dışarıdan verilen
kendi test gözlemleridir; adreslerin oyun oturumunda geçerli olduğu kanıtlanmaz.

Coin zinciri global553e7c → guarded DWORD root → taze global553ff0 offset →
guarded DWORD(root+offset) → EAX'tır. Adres toplamı DWORD'da sarılır. İlk helper
sonucu0olsa da caller ikinci offset/helper çağrısını atlamaz. Root hatasını
otomatik olarak bütün zincirin erken dönüşüne çevirmek kaynakla eşdeğer değildir.

`plan_guarded_dword` kaynakta şu normal akışı planlar:

1. Argüman0ise API gözlemi gerekmeden EAX0.
2. Nonzero adres için VirtualProtect(address,4,40hex,&old) çağrı planı.
3. Verilen API EAX sonucu0ise EAX0; veri değeri okunmaz.
4. API EAX nonzero ise ayrı DWORD değer gözlemi gerekir.

API sonucu veya değer eksikse0uydurulmaz. Null dönüşü, protection-failure dönüşü
ve gerçek gözlenen0ayrı status'tür; coin caller'ı sayısal sonucu kullansa da own
plan kökeni saklar. Gövdede normal dönüş öncesi protection-restore çağrısı yoktur;
modele kaynakta olmayan restore işlemi eklenmez. Bunlar gerçek koruma değişikliği
veya başarı kanıtı değildir. Fault/trap, eşzamanlı bellek değişimi ve API yan
etkileri emüle edilmez.

`SellCoinAlarmObservation.coin_inputs`, bu zinciri coin alarm prefix'ine bağlar.
Ham `coins_dword` ile aynı anda verilemez. Alarm kapalıysa zincir yürütülmez;
açıksa eksik root/API/değer örneği referans karşılaştırmasına geçirmez.
`sell_coin_alarm_from_panel(...,coin_inputs=...)` aynı bağ için tam QWORD panel
referansını korur. Workbench hâlâ ayrı ham coin EAX örneği alır; detaylı guarded
zincir için yeni UI kontrolü yoktur. Bu alan API kapsamıdır. Başka coin tüketicileri
bu değişiklikle otomatik olarak bu modele bağlanmış sayılmaz.

`work/audit_source_coin.py`, iki sabit hash'li dosyada iki gövdenin toplam
**74 talimat kaydını** baytlarıyla doğrular. Global/root/offset sırası, null ve
failure dalları, size4/40hex argümanları ve gerçek VirtualProtect import kimliği
ayrıca kontrol edilir. Rapor `outputs/FarmexBot_coin_okuyucu_kod_kaniti.json`.
Ghidra statik kanıtıdır; REA Evidence veya native yürütme değildir. Örtüşen
talimatlar benzersiz fonksiyon tamamlanma toplamı olarak toplanmaz.

9 yeni test dahil **1974 test geçti** (7.005 saniye). Null, API failure, gerçek0,
ilk hata sonrası ikinci okuma, DWORD wrap, eksik değer ve alarm bağının erken
ilerlememesi sınandı. Mevcut coin alarmı hedefli gizli UI testi de tekrar geçti;
UI kodu bu aşamada değişmedi. Native koruma/oyun okuması ve canlı uyumluluk açık.
