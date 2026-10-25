# Hedefi isim listesine ekleme çağrı zinciri

18 Ekim2026. `source_target_add.py`, beyaz00423D5C ve kara00423EB4 düğme
caller'larının normal akışını birleştirir. Önceki target/name/scan kanıtına
son ANSI cleanup noktaları eklendi; iki sürümde990 instruction kaydı yine
disk baytlarıyla doğrulandı. Rapor
`outputs/FarmexBot_hedef_isim_ve_UI_sorgu_kod_kaniti.json`, üretici
`work/audit_target_name_helpers.py`. Bu yerel disk/Ghidra kanıtıdır; REA
Evidence, native helper execution veya canlı UI dispatch kanıtı değildir.

## Üç bağımsız hedef okuması

İlk00462630 değeri nonzero olmalıdır; unsigned TEST/JBE kontrolü signed
pozitiflik denetimi değildir. İlk değer0ise ikinci/üçüncü örnek okunmaz.
İlk nonzero ise ikinci taze DWORD **en çok3000** olmalıdır. İkinci0 kabul
edilir;3001ve unsigned FFFFFFFF reddedilir. Invalid yolunun notice/string
cleanup span'ı ayrıca normal dönmelidir; plan gerçek mesaj kutusu açmaz.

Valid yolda üçüncü taze DWORD00466144 parametresidir. Önceki örneğe eşit
varsayılmaz; helper signed0..2999kabul ettiği için3000/negatif raw değer
empty ANSI fallback'ına gidebilir. Caller burada ayrıca nonempty guard
yapmaz. Empty isim duplicate taramasından geçerse boş UI satırı eklenebilir;
bu davranış metinle ekleme düğmesinin empty guard'ıyla karıştırılmaz.

Raw `target_ids` veya her çağrı için optional `target_id_executions` verilir.
Reached aynı çağrıda raw+bound karışımı reddedilir. Bound ID okuyucusu
complete olsa bile `target_id_returned` receipt'i ayrıca gerekir. Eksik
reader/raw örnek0sayılmaz ve önceki değerle doldurulmaz. Sadece ulaşılan
reader'lar plan trace'inde gösterilir.

## İsim, duplicate, append, refresh

`name_execution` üçüncü ID'ye tam uymalıdır. Raw ANSI output ile karışmaz;
incomplete plan ilerletmez. Tam plan için de ayrı `name_returned=True`
gerekir. Name-by-index helper'ının boş fallback çıktısıb'' geçerli çıktıdır.

`duplicate_execution` aynı helper output ANSI baytlarını kullanmalıdır;
başka string veya raw AL override kabul edilmez. Ayrı helper normal dönüşü
gerekir. Duplicate nonzero ise append ve refresh atlanır, fakat local ANSI
name cleanup hâlâ gerekir. Unvisited alt planlar tüketilmez.

Duplicate0 ise ANSI→Unicode append sonucu ayrı gözlemdir; codepage varsayımı
yapılmaz. Conversion/virtualAdd/geçici cleanup span'ı normal döndükten
sonra own prospective listeye eklenir. Optional bound refresh incomplete
ise durur; complete ise de ayrı refresh dönüşü gerekir. En sonda local
ANSI cleanup doğrulanır. Bu son cleanup eksikse append bilinen own
prospective olarak kalır; `.state` girişte tutulur. Bu native rollback
iddiası değildir.

Plan `.complete`, gerekli normal akış gözlemlerinin supplied own modelde
tam olduğunu gösterir. Heap/locale/exception/concurrency veya gerçek
helper side effect sertifikası değildir. Planın bütün native verification
bayrakları false kalır. Girdiler ve output state immutable'dır.

## Kontrol

18yeni test dahil **2386 test geçti (7.960 saniye)**; parent/ID/name/UIscan
odaklı47 test geçti. Signed/unsigned sınırlar, ikinci0/3000, üçüncü negatif,
eksik örnek, bound input çatışmaları ve bağımsız helper dönüşleri sınandı.
Tam bağlı bir own denemede üç IDreader→index3000empty name→empty-list scan
→boş UI satırı→vector refreshb'' zinciri geçti. Bu sentetik çağrı gözlemidir;
gerçek hedef yakalaması değildir.

UI/native kaynak değişmedi; bu aşamada UI/native smoke tekrarlanmadı.
Kaynak hedef düğmelerinin canlı adapter'ı henüz bağlı değildir ve düğmeler
kendi panelinde hâlâ etkin değildir. Oyun belleğine/koruma API'sine/ağa
erişilmedi. Gerçek runtime/target/name/codepage ve canlı uyumluluk açık.
