# Rota açılır listesi: dosya adı üreticisi

Güncelleme: Kendi klasör adapter'ı, iki dinamik panel combosu, gerçek own
seçim metni→580/584→route-start bağı ve profil-v3 persistansı eklendi.
[ROUTE_CATALOG_UI.md](ROUTE_CATALOG_UI.md) güncel kapsamı açıklar; aşağıdaki
“henüz tamamlanmadı” listesi önceki API-only aşamasına aittir. Native scan,
GetText/Items runtime etkileri ve canlı eşdeğerlik hâlâ açık.

18 Ekim2026. Tedarik/Return DropDown eventleri4ac754/4ac844, form alanı
6f8/88c ve supply context5687a8 ile ortak4e96d4 çağırır. Change eventleri
4aad54/4ac86c yalnız561f55BYTE nonzero iken4e7668 scalar projection çağırır.
4e7668, gerçek GetText importuyla kontrol metinlerini580/584 alanına kopyalar;
profil ItemIndex'i tek başına bu metni üretmez. Canlı event çalıştırılmadı.

## Kaynak akış

4e96d4 önce4e93d8 ile dosya vektörünü yeniler, sonra comboyu virtual13c ile
temizler. Vector count bir kez hesaplanır. Tam0ise `Rota Seciniz !` literal'i
Items virtual3c ile eklenir. Nonzero count için placeholder eklenmez; signed
pozitif döngü kayıtları sırayla Unicode'a dönüştürüp ekler. Negatif hesaplanan
count placeholder yolu değildir. Count/slot getter tazeliği, range-error helper
ve native Items mutasyonları ayrıca modellenmeyi bekler.

4e93d8 önce vector reset yapar, supply+57c ANSI directory üzerinden `_opendir`
çağırır. Pointer0ise readdir/closedir atlanır. Diğer yolda `_readdir` pointer0
olana kadar devam eder; giriş C-string'i signed length>=3 ise son2baytı `.R`
literal'iyle karşılaştırılır. Eşleşen özgün isim, uzantısı korunarak vector'e
eklenir; caller seviyesinde sıralama, tekrar eleme veya entry türü testi yoktur.
Size/capacity unsigned fast/slow insert yolları isim-listesi vektörüne benzer;
bu benzerlik native allocator etkileri için kanıt sayılmaz.

## CRT bağı

Korunmuş CC32260MT.DLL içindeki char_traits.compare doğrudan raw byte memcmp
çağırır. Case folding yoktur: `a.R` geçer, `a.r` geçmez; yalnız `.R` uzunluğu2
olduğu için geçmez. readdir, directory nesnesi+3c filename pointer'ını döndürür;
record başı string olarak yorumlanmaz. Directory magic geçersizken veya next
başarısızken0dönebilir. Kaynak caller errno sorgulamaz; null dönüş kaynak
döngüsünü bitirir ama sağlıklı/tam dosya envanterini tek başına kanıtlamaz.

Richard iki sürüminde1196 instruction kaydı ve published-method kayıtları,
CRT beş export metodunda223 instruction kaydı exact-byte denetiminden geçti.
Late code adresleri-1c taşınırken `.R`/placeholder data adresleri sabit kaldı;
bu yüzden literal adresleri körlemesine kaydırılmadı.

Üreticiler: `work/audit_route_dropdown.py`,
`work/prepare_route_directory_scope.py`, `work/run_route_directory_scope.ps1`,
`work/audit_route_directory_crt.py`. Raporlar
`outputs/FarmexBot_rota_combo_caller_kod_kaniti.json` ve
`outputs/FarmexBot_CRT_rota_dizin_kod_kaniti.json`. Bunlar Ghidra/disk
kanıtıdır; REA Evidence veya current loaded-runtime kanıtı değildir.

## Yerel uygulama ve açık işler

`route_catalog.py` bu byte filename politikasını **own stable projection**
olarak uygular. Girdi, sırayla sağlanmış NUL öncesi C-string baytlarıdır.
Unicode sonucu ve dönüş normal-return receipt'i ayrı gerekir; native codepage
varsayılmaz. Sıra/tekrarlar korunur, hiç kabul edilen ad yoksa placeholder
yalnız explicit enumeration_complete=True ile üretilir. Bu son koşul own
kataloğun tamlığı içindir; native readdir-null davranışına eşit sayılmaz.
Incomplete prefix dosya envanteri tamamlandı olarak sunulmaz.

10test exact extension, byte uzunluğu, sıra/tekrar/uzantı, placeholder/eksik
prefix, codepage sonucu ve conversion boşluklarını sınar. Directory IO yoktur.
Gerçek source scan/caller normal-return modelleri, file enumeration adapter,
runtime dropdown choices/profile persistansı ve GetText→route-start UI bağı
henüz tamamlanmadı. Mevcut RoutePage manual stand-in kaldırılmadı. UI değişmedi;
oyun belleği/işlemi/native execution0, canlı eşdeğerlik doğrulanmadı.
