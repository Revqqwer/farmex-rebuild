# RTL liste metni, satır ayrıştırma ve BOM sırası

Sonraki aşama: Base constructor/ACP/BOM varsayılanları ve geçerli veri için
yerel CFG panel adapter'ı [NAME_CFG_CODEC.md](NAME_CFG_CODEC.md) içinde
eklendi. Aşağıdaki ilk aşama sınırlamaları bu yeni kanıtla daraldı; gerçek
yüklü codec/fallback ve tam native uyumluluk hâlâ açık.

18 Ekim 2026. Sabit RTL260 SHA7d98acb8fade7f09... girdisinde13 seçilmiş
export metodu Ghidra ile çözümlendi;704 talimat kaydı korunmuş dosya
baytlarıyla eşleşti. Kaynak `outputs/Ghidra_RTL_liste_dosya_metotlari.json`,
kanıt `outputs/FarmexBot_RTL_liste_metin_kod_kaniti.json`, üretici
`work/audit_delphi_list_text.py`. Ghidra işi başarıyla terminal oldu;
bekleyen bir analiz işi bu aşamada yoktur. Program/BPL çalıştırılmadı.
Bu yerel Ghidra kanıtıdır; REA Evidence ve canlı uyumluluk değildir.

`delphi_list_text.py` üç dar normal-text alt modeli sunar. Bunlar bütün
RTL metodlarının veya orijinal CFG import/export'unun tamamı değildir.

## SetTextStr ortak CRLF yolu

Runtime LineBreak CRLF ise SetTextStr UTF16 word'lerini ilk NUL'a kadar
tarar. CR, LF ve CRLF ayraçlarını kabul eder. Ardışık ayraçlar boş satır
üretir; son ayraç tek başına ek bir son boş satır üretmez. Örnek:
`a\r\n\r\n` iki satırdır: `a` ve boş string. Boş metin hiç satır üretmez.
Case, boşluk ve yinelenen isimler korunur. Unicode kod birimleriyle
işlendiğinden supplementary karakterler ve surrogate dizileri ayrıştırma
sırasında Python codepoint uzunluğuna göre yanlış bölünmez.

LineBreak CRLF değilse kaynak ayrı AnsiStrPos yoluna gider; mevcut model
bu dalı tahmini `split()` ile doldurmaz, eksik gözlem olarak bildirir.
CompareStr ve AnsiStrPos kimlikleri PE exportlarından eşleşti; bütün locale
ve pointer/exception davranışları çözüldü sayılmaz.

## GetTextStr iki geçişi

Kaynak count'u bir kez alır; ilk geçişte item UTF16 uzunluklarıyla toplam
uzunluğu hesaplar, ikinci geçişte item'ları **yeniden** alıp kopyalar.
Runtime+0C LineBreak alanıdır. Runtime+1E flags BYTE'ının mask4 biti son
satır sonunu belirler. `plan_stable_get_text` açık
`stable_same_invocation=True` sözleşmesiyle yalnız kendi sabit satırlarını
modeller; gerçek native mutation veya ilk/ikinci getter eşliği kanıtı
üretmez. Gömülü NUL burada length-based metnin parçası olarak kalır;
SetTextStr'ye sonraki verildiğinde PChar taraması NUL'da durabilir.

Boş liste ve trailing-bit kapalıyken kaynak hesaplama LineBreak uzunluğunu
negatife çıkarabilir. Alt model bunu sessizce0'a düzeltmez; native negatif
UStrFromPWCharLen yolu açık bırakılır. DWORD/heap/overflow ve exception
akışları tam emüle edilmez.

## SaveToStream kodlama ve BOM

SaveToFile(filename), nesnenin+4 encoding alanını overload'a geçirir.
SaveToStream encoding parametresi NULL ise+8 default encoding alanına
geçer. Runtime+1E flags BYTE'ının **mask2** biti GetPreamble sonucunu yazma
kararını verir; mask4 ile aynı şey değildir. GetBytes sonucu ve gerekiyorsa
GetPreamble baytları ayrıca sağlanır. Nonempty preamble önce, data sonra
yazılır. Veri boş olsa da data write çağrısı planda korunur; empty preamble
ayrı write üretmez. Seçilen encoding veya byte çıktısı bilinmiyorsa UTF8/
ANSI varsayımı yapılmaz.

LoadFromStream tarafında buffer encoding detection ve GetString dönüşümü
görülür; seçilen encoding object's runtime kimliği, default codepage/BOM
seçimi ve gerçek decode/fallback sonuçları henüz modellenmiş değildir.
Bu nedenle yeni API dosya açmaz ve CFG import/export tamamlandı denmez.

12 yeni test dahil **2325 test geçti (8.256 saniye)**; text/CFG odaklı20 test
geçti. Mixed newline, ardışık/trailing boş satır, NUL, UTF16 uzunluğu,
stability gereksinimi, mask2/4 ayrımı, bilinmeyen encoding ve preamble/data
sırası denetlendi. UI/native kod değişmedi; bu aşamada smoke tekrarlanmadı.
Gerçek process/runtime bağlama, özel delimiter ve CFG dosya adapter'ı açık.
