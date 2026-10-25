# Diğer sekiz rota türünün panel ad üreticisi

19 Ekim güncellemesi: EnginePage SELL/BUY Unicode adı ve mining ANSI adı artık
bilinen own panel seçiminden alır; SELL bank route için ayrı input factory
eklendi. [ENGINE_ROUTE_INPUTS.md](ENGINE_ROUTE_INPUTS.md) güncel scope'u açıklar.
Aşağıdaki EnginePage fixture notları bu bağdan önceki aşamayı anlatır;
native/helper/start ve canlı yürütme hâlâ açıktır.

18 Ekim2026. Tüm10rota türü artık aynı own klasör kataloğundan doldurulabilir
ve Rota editörüne panel seçimiyle yüklenebilir. Önceki iki Supply/Return
bağına aşağıdaki sekiz alan eklendi. Tablo adresleri source etiketleridir;
Python bunları oyun belleğine yazmaz.

| Tür | Form alanı | Yapı tabanı + offset | ANSI filename global |
|---|---|---|---|
| Mine | de8 |569a98 +5ffc|56fa94|
| SMerchant | cc4 |5697e0 +dc|5698bc|
| BMerchant | d58 |5697e0 +128|569908|
| AntiCR |760|5690f8 +24|56911c|
| Enemy |7f0|5690f8 +3c|569134|
| Notice |7b0|5690f8 +54|56914c|
| PMKONTROL |80c|5690f8 +88|569180|
| Relog |84c|562194 +9c|562230|

Her kontrolün published DropDown event'i aynı supply context5687a8 ve
4e96d4 yardımıyla listeyi doldurur. Change event'i561f55BYTE nonzero ise
ilgili ayar yazıcısını çağırır: Mine4762fc, Merchant41fea4,
Koruma46b928, Relog4576ec. Bu enclosing ayar yordamları yalnız filename
yazmaz; tamamının veya önceki guard'larının çözüldüğü ileri sürülmez.

Bounded getter span'larında doğru form alanı -> gerçek GetText import ->
4073a0Unicode/ANSI dönüşümü -> doğru yapı offset'i -> ANSI assignment sırası
doğrulandı. `work/audit_global_route_panel.py` iki modül sürümünde **1082
instruction kaydını**,8field ve16published event kaydını diskle eşleştirir.
Rapor `outputs/FarmexBot_diger_rota_panel_uretici_kod_kaniti.json`.
Bu Ghidra/disk kanıtıdır; REA Evidence veya native runtime kanıtı değildir.

`ROUTE_COMBO_PATHS`10kontrolü tanımlar. Kendi ConfigurationPanel'i bunların
gerçek runtime seçeneklerini ve seçimini tutar. Profil-v3 aynı biçimde tüm
10comboda seçenek/indeks/klasör/codepage saklar; eski v3iki-combo profilleri
ve v1/v2okunmaya devam eder. Her DropDown yalnız açılan own comboyu yeniler;
diğer seçimleri korur. Native Clear/Add/window mesajları doğrulanmadı.

`compile_panel_route_name` yalnız ulaşılan türün bilinen Unicode Text'ini
ister; eksik Text boş isim sayılmaz. Explicit Windows codec ile kayıpsız
dönüşüm sonrası immutable source-address mapping döner. Diğer türlerin
metinleri gereksiz okunmaz. Rota editörü default panel seçeneğinde bu
mapping'i `plan_global_route_choice` ve mevcut `.R` importer/own runner'a
bağlar. Mine'ın değişen-listesi, üçüncü sayacı ve ayrı check/load directory
akışı korunur. Legacy manual mode ayrı kullanıcı seçeneği olarak durur.

Dört yeni test sekiz türün kontrol/global/filename kimliğini, yalnız ulaşılan
metnin tüketilmesini, unknown-vs-empty ayrımını, immutable output ve explicit
UTF8/1254loss denetimini sınar. Genişletilmiş gizli UI denemesi bütün10türü
gerçek own combo event'iyle seçer, `.R` adımlarını yükler ve profil sonrası
tüm seçimlerin gerçek widget render'ında korunduğunu denetler.

Bu bağ filename seçimini tamamlar; otomatik Mine/merchant/AntiCR/Enemy/
Notice/PM/Relog tetikleyicileri, native ayar helper dönüşleri, global bellek
etkileri, gerçek x87/movement ve oyun içi yürütme için tamamlanma kanıtı
değildir. EnginePage'in ayrı Merchant/Mining denemeleri kendi fixture
girdilerini kullanmaya devam eder. Native erişim engeli bu UI bağlantısıyla
çözülmüş değildir; canlı uyumluluk hâlâ doğrulanmadı.
