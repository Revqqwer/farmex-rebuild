# Kaynakla karşılaştırılan RTL Int64 ayrıştırma modeli

Güncelleme: scalar model artık Flood panelinde kullanılıyor. Son bölümdeki “UI değiştirilmedi” ifadesi bu belgenin ilk aşamasına aittir; güncel bağlantı [RTL_INTEGER_PANEL.md](RTL_INTEGER_PANEL.md) dosyasındadır. Yeni native exception gözlemi, orijinal bot catch/unwind eşliği olarak sunulmaz.

`rtl_integer.py`, sabitlenmiş `rtl260.bpl` `_ValInt64` (`5006501c`) scalar normal gövdesini immutable, normal UTF16 string için yeniden kurar. `None` açık null pointer yoludur. Çıktı raw64bit sonuç,1-based Code ve radix/işaret bilgisidir. Code0 başarıdır; başarısız girdide kısmi sonucu başarı diye kullanmaz.

Kurallar doğrudan194 assembly kaydından çıkarıldı: yalnız baştaki U+0020 atlanır; tek +/− alınır; `$`,`x`,`X`,`0x`,`0X` hex seçer. Decimal ASCII0–9, hex ayrıca ASCIIA–F/a–f kabul eder. İlk NUL sonlandırır. Managed string uzunluğu0x lookahead kapısına katılır; embedded NUL sonrasındaki metin otomatik okunmaz. Hata konumu UTF16 code unit bazındadır, Python Unicode code point indeksi değildir.

Her digit öncesi signed high-DWORD ve üst sınır kapıları uygulanır: decimal accumulator en çok `0x0ccccccccccccccc`, hex `0x0fffffffffffffff`. Sonuç low64bit multiply/add ile kurulur. Negatif işaret modulo64 negation'dır. Decimal sonuç sıfır değilken signed işaretin girdiyle eşleşmemesi hata indeksini bir geri alır; hex bu signed-range son kontrolünü yapmaz. Böylece unsigned64 hex ve negatif hex biçimleri decimal'den ayrılır. Çarpma yardımcısı `50064984`14 kayıtta low64bit üç kısmi MUL ve RET8 ile ayrıca incelendi.

`TryStrToInt64`16 kayıtta Val'ın sonucunu **Code hatalı olsa da** QWORD'a yazar, AL'yi Code0'a göre verir. `StrToInt64`21 kayıtta Code nonzero iken ayrı error helper'ına gider. Error helper/native exception yaşam döngüsü ve bot C++ catch landing zinciri burada yürütülmedi. Kaynak bot wrapper'ının fallback yolu ayrı `SourceIntegerFrame` kanıtında kalır; bu modül Delphi exception üretmez veya yakalamaz.

Native doğrulama: hash'i kontrol edilen kendi32bit stream fixture'ı Try ve Val export'larını aynı UTF16 girdilerde çağırdı. Deterministik **8067 girdide** Code, rawQWORD ve başarıAL modelle aynı; her iki çağrıda stack dengesi korundu. Matris decimal/hex sınırları, işaret/prefix/baş-son ayraçlar,2000 leading zero, embeddedNUL, surrogate/Unicode ve1800 seeded rastgele adayı kapsar. Bu sonlu örnek kümesidir; bütün stringler, bellek alias'ları, bozuk metadata, exception veya canlı runtime için tamlık sertifikası değildir.

Statik kanıt: orijinal PE'den birebir `50064000…50095000`200704bayt taşıyıcı çıkarıldı. Ghidra noanalysis/focused export ile3 yordam ve çarpma helper'ı toplam245 instruction kaydı hem taşıyıcı hem orijinal BPL baytlarıyla doğrulandı. Bu ayrı Ghidra kanıtıdır, REA Evidence olarak sunulmaz. REA'nın tam13MB RTL analizi600000ms provider_timeout ile sonlandı; sıradaki aynı tam-modül analiz istekleri iptal edildi. Başarısız cevap korunur.

Bu aşama mevcut Flood UI parser'ını değiştirmez: native exception/fallback ve source model entegrasyonu ayrı adım olarak açık.11 yeni Python testi ve tam4056 test koşusu; önceki tam UI kaynak/log hash kanıtı değişmedi. Native karşılaştırma yalnız kendi sürecimizdedir, oyunda loaded RTL kimliği veya canlı uyumluluk kanıtı değildir.
