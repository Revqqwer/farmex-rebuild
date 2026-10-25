# Spirit of Genie taraması ve yerel kayıt

21 Ekim 2026. `genie_recovery.py`, `004ca588` normal yolunu modeller. Kaynak mutlak envanter yuvaları14..41içinde her yuvada taze00463670isim sonucu ile `Spirit of Genie` literal'ini karşılaştırır. İki geçici nesnenin temizliği, karşılaştırma sonucuna göre dallanmadan önce tamamlanır. Eşleşmede aynı yuvadan ayrıca taze004634a4item-IDsonucu alınır. Bu sonuç isim metadata'sından veya yuva numarasından türetilmez.

İlk isim eşleşmesinde tarama biter. O yuvadaki freshID0ise sonraki aynı isimli eşya aranmaz; false yola gidilir. Tam yokluk,28yuvanın ayrı gözlemlerini gerektirir. Eksik gözlem boş eşya veya eşleşme yokluğu sayılmaz. Getter0sonucunun gerçek boş eşya mı, başarısız okuma mı olduğunu model ayıramaz.

Kaynak equality wrapper'ı `SETZ AL; AND EAX,1` ile fullDWORD0/1üretir. İç sıralama yardımcıları dış RTL `_LStrCmp` bayraklarını kullanır; bu audit RTL gövdesini çözmez. Varsayılan model ayrı name-byte snapshot'ı ve gözlenmiş comparisonEAX0/1ister. `owned_byte_compare=True` açıkça seçilirse kendi fixture adapter'ımız byte/uzunluk eşitliği kullanır; casefold veya NUL kesmesi yapmaz ve native comparison alanını tüketmez. Bu seçim gerçek RTL/native eşdeğerlik sertifikası değildir.

NonzeroIDiçin kaynak7baytlık `97 01 01 00 00 00 00` template'ini kopyalar, offset3..6alanına fullDWORDitemIDyazar ve delay0ile004c7710'a verir. Kayıtta yuva numarası kodlanmaz. Bu kaynak template gözlemidir;7baytın gerçek oyun/sunucu protokolündeki etkisi bağımsız doğrulanmadı.

`GenieRecoveryFrame` sabit contextDWORD, karşılaştırma seçimi ve kendi kuyruğuyla başlar. Tüketilen slot/name/compare prefix'i saklanır; geç IDgelince önceki eşleşme değişmez. Bilinen gate, tick beklerken korunur. Kopyalanmış kayıt veya enqueue normal dönüşü geç return-span boşluğunda tekrarlanmaz. Mevcut kuyruk prefix'i tutulur. Bunlar kendi seri yerel sözleşmemizdir; source thread/heap/stack davranışının tamamı değildir.

Enqueue helper'ı normal döndükten sonra kaynak yalnız `MOV AL,1` yapar; üstEAXbilinmiş sayılmaz. Gate0kopyayı atlamış olsa da bu düşük AL1olabilir. Dolayısıyla AL1“Genie doldu” veya “sunucu kabul etti” değildir. No-match/freshID0false yolunda fullEAX0kaynakta açıkça üretilir. Her durumda ayrı return-span normal gözlemi gerekir; model gerçek FS/heap/protection değişikliği yapmaz.

`work/audit_genie_recovery.py`, eski/güncel yenileme gövdesini, item-IDgetter'ını, equality/ordering wrapper'larını ve iki RTL karşılaştırma yardımcısını toplam402talimat kaydıyla doğrular. Kaynak template/literal/import kimlikleri ve sürümler arası açık helper adres eşlemeleri ayrıca kontrol edilir. Kaynak `outputs/FarmexBot_genie_yenileme_kaniti.json`; korunmuş Ghidra/PE kanıtıdır, yeni REA Evidence değildir.

11yeni test exact7byte/IDpatch'i, son yuvayı ve28yokluk gözlemini, ilk matchID0durmasını, cleanup-before-ID'yi, açık owned compare/NUL farkını, gate0AL1ayrımını, geç gate/tick/normal/return devamını ve stale prefix'i kapsar. Tam koşu `GENIE_RECOVERY_VALIDATION.json` dosyasındadır. Genel Genie worker bu sonucu henüz typed child olarak tüketmez; orada004ca588sınırı hâlâ opaque'dir. UI/native C değişmedi; UI yeniden test edilmedi. Gerçek eşya tüketimi, yenileme ve canlı uyumluluk açık kalır.
