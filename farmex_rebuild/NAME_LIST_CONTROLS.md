# İsim listesi paneli ve kaynak ekleme akışı

18 Ekim güncellemesi: Clear/DeleteSelected VCL gövdelerinin sınırlı normal
akışları ve dört Richard caller bağı [VCL_LIST_MUTATION.md](VCL_LIST_MUTATION.md)
içinde modellendi. Önceki “body kanıtı yok” notu tarihsel durumu anlatır;
gerçek yüklü dispatch/native mutation etkileri hâlâ doğrulanmadı.

Güncelleme:0046601c normal UI duplicate scan ve typed text-add bağı artık
[TARGET_NAME_CHAIN.md](TARGET_NAME_CHAIN.md) içinde modellenmiştir. Önceki
explicit AL boşluğu bu scoped modelle daraldı; ANSI/RTL/native etkiler ve
hedef düğmelerinin canlı adapter'ı tamamlanmış sayılmaz.

18 Ekim 2026. `source_name_add.py`, beyaz0042400c/kara00424180 text ekleme
caller'ını açık normal-span/AL gözlemleriyle modeller. İki sürümde718
talimat kaydı doğrulandı; rapor `outputs/FarmexBot_isim_ekleme_caller_kod_kaniti.json`,
üretici `work/audit_source_name_add.py`. Kayıtlar duplicate helper0046601c
ve inequality wrapper505d4c'yi de içerir; helper'ın tüm iç semantiği
uygulandı veya native yürütüldü anlamına gelmez. Bu REA Evidence değildir.

İlk getter ve string cleanupları sonrası saklanan nonempty AL0 ise dönüş
olur.505d4c eşitlik wrapper'ının düşük AL'ını AND/CMP/SBB/NEG ile normalize
ederek tersler; boş literaller disk üzerinde NUL'dur. İkinci taze getter,
Unicode→ANSI dönüşümü ve0046601c duplicate kontrolü sonrası saklanan AL
nonzero ise ekleme atlanır. İki guard'ın normal span dönüşü ve normalize
AL gözlemleri ayrıdır; cleanup dönüşü karşılaştırma sonucu sayılmaz.

Ekleme yolunda input **üçüncü kez** okunur. Son metin önceki getter'larla
aynı, hâlâ nonempty veya duplicate-free varsayılmaz. Model üçüncü metni
kullanır; bu anda boş veya mevcut isim de olabilir. Virtual Add+cleanup
normal span'ından sonra own prospective UI listesine eklenir; ardından
0046c3b8 refresh gelir. Optional bound refresh eksikse plan tamamlanmaz;
tam bound plan için de bağımsız `refresh_returned=True` gerekir. Erken
skip yolu kullanılmamış bound planı çalıştırılmış göstermez. Partial
`.state` girişte kalır; `.prospective` native rollback veya bellek kanıtı
değil, own deneme projeksiyonudur.

## Kendi panelindeki davranış

`name_list_controls.py` ve `panel_ui.py`, beyaz/kara listede **EKLE** ve
**Temizle** düğmelerini etkinleştirir. Çift tıklama seçili tek ismi siler;
seçim yoksa değişiklik yapmaz. Diğer liste korunur. Metin girdisi ve liste
widget'ı ortak profile state'ine bağlıdır; profil save/load ile saklanır.
Girdi alanı eklemeden sonra temizlenmez. Hedef karakterden isim alma hâlâ
oyun adapter'ı gerektirdiğinden etkin değildir.

Bu panel stable kullanıcı girdisi için **kendi UTF16 eşitlik politikasını**
kullanır. Tam boş metin eklenmez; aynı UTF16 dizisi tekrar eklenmez; case,
whitespace ve normalization korunur. Kullanıcının Unicode metni kendi
profilinde kayıpsız tutulur; native ANSI codepage varsayılıp dönüştürülmez.
Bu yüzden RTL/locale/ANSI roundtrip veya değişen native getter'lar için
tam eşdeğerlik iddiası yoktur. Raw source modeli bu gözlemleri ayrı tutar.

Sonraki disk runtime incelemesi13C/148 tablolarını Clear/DeleteSelected
exportlarına bağladı; ayrıntı [SOURCE_NAME_CFG.md](SOURCE_NAME_CFG.md).
Bu native method body veya gerçek yüklü dispatch kanıtı değildir. Orijinal
CFG save/load formatı da bu profil JSON formatıyla eşdeğer sayılmaz.

13 yeni test dahil **2305 test geçti (7.613 saniye)**. Guard boşlukları,
üçüncü getter değişimi, bound refresh dönüşü, Unicode/case/whitespace,
tek duplicate occurrence silme ve no-op seçimler sınandı. Gizli UI kontrolü
1037 kontrol/11 form/18 sekme ve mevcut senaryolarda geçti. Yeni own düğme,
seçim, case/empty/duplicate ve profil save/load assert'leri de geçti; kayıt
`NAME_LIST_CONTROLS_VALIDATION.json` içindedir. Oyun belleğine erişim veya orijinal
uygulamaya input yapılmadı; canlı uyumluluk açık.
