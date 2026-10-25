# İsim CFG çağrıları ve yükleme sırası

18 Ekim 2026. `source_name_cfg.py`,004603fc load yardımcısının normal çağrı
akışını açık gözlemlerle modeller. İki Richard sürümünde470 talimat kaydı,
iki filename literali, obje alanları ve `_fopen`/`_fclose` importları
doğrulandı. Kanıt `outputs/FarmexBot_isim_CFG_caller_kod_kaniti.json`,
üretici `work/audit_name_cfg_callers.py`. Bu disk/Ghidra/PE kanıtıdır;
REA Evidence veya canlı orijinal çalışma izi değildir.

Profil path yapısında base+4 ile filename suffix'i birleştirilir. Kara
`AntiCRBlackList.cfg` base+2C, beyaz `AntiCRWhiteList.cfg` base+30 alanına
bağlanır. Kaydetme span'ı0042f419..0042f4e4, beyaz3D4 ardından kara3F0
Items üzerinden virtual80'i çağırır. Yükleme span'ı00440514..00440547 de
beyaz ardından kara için004603fc çağırır. Büyük parent yordamların diğer
ayarları bu dar scope'tan tamamlanmış sayılmaz.

Kurulu disk BPL'leri çalıştırılmadan export/VMT eşlemesi yapıldı:

| Disk sınıfı | Slot | Export eşleşmesi |
|---|---|---|
| VCL TListBox/TCustomListBox | 13C | Clear |
| VCL TListBox/TCustomListBox | 148 | DeleteSelected |
| RTL TStrings/TStringList | 6C | LoadFromFile(filename) |
| RTL TStrings/TStringList | 80 | SaveToFile(filename) |

Kaynak runtime envanteri `outputs/FarmexBot_VCL_liste_runtime_envanteri.json`.
RTL SHA7d98acb8fade7f09..., VCL SHA84ea9ebbdc4570cb... girdileri analiz
dizininde hash ile sabitlendi; kaynak ZIP'e konulmaz. Disk class tablosu
eşlemesi gerçek oyunda yüklü modül/private Items class override kimliğini
ve method body etkilerini kanıtlamaz. Bununla önceki13C/148 belirsizliği
disk runtime için daraldı; tüm native dispatch sertifikası verilmiş değildir.

## Önemli yükleme davranışı

004603fc önce ANSI path copy, sonra **Clear** çağırır. Ardından0045e754
`_fopen(path,"r")` yapar. FILE pointer0 ise AL0 döner. Nonzero ise `_fclose`
normal dönmelidir; integer close sonucu kontrol edilmez ve AL1 yazılır.
Bu ayrı helper'ın normal dönüşü CFG caller'ında da ayrıca gözlemlenir.

AL0 yolunda final path cleanup sonrası dönüş olur: kaynak eski listeyi
koruyarak dosyayı atlamaz, temizleme zaten önce gerçekleşmiştir. AL1 ise
ANSI path→Unicode conversion, virtual6C LoadFromFile, Unicode cleanup ve
final ANSI cleanup normal dönüşleri gerekir. Model post-load satırları
ayrı Unicode tuple olarak ister; başarılı load dönüşünden hayali satırlar
veya boş içerik çıkarılmaz. Gerçek format/encoding henüz bu API'de okunmaz.

Tam olmayan plan `.state` girişini tutar; bilinen clear/load projeksiyonunu
`.prospective` içinde gösterir. Bu own deneme ayrımı native rollback
iddiası değildir. `_fopen` sonucu bilinmiyorsa missing-file sayılmaz;
readable boş dosya ile okunamayan dosyanın `probe_al` sonuçları ayrıdır.

Sekiz yeni test dahil **2313 test geçti (11.481 saniye)**; CFG/add/list
odaklı30 test geçti. Clear-before-probe, eksik normal dönüşler, FILE pointer
boşluğu, duplicate/space sırası, empty load ve cleanup sonrası prospective
alanları denetlendi. UI/native kod değişmedi; önceki tam UI smoke bu
aşamada tekrarlanmadı.

RTL LoadFromFile/SaveToFile ve stream metodları için sabit dosya üzerindeki
Ghidra çözümlemesi13 metotta tamamlandı;704 talimat baytı ayrıca doğrulandı.
Dar text/newline/BOM alt modelleri [DELPHI_LIST_TEXT.md](DELPHI_LIST_TEXT.md)
içindedir. Aktif encoding/codec ve kaynak CFG import/export adapter'ı,
gerçek runtime bağlama ve canlı oyun uyumluluğu açık. Bu modül dosya veya
oyun belleği okuma/yazma yapmaz.
