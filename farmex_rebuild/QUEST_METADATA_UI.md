# Görev metadata yolları ve üç gerçek düğme

4744 Python testi; yeni tam GUI: 1037 kontrol, 11 form, 18 sekme.
QUEST_METADATA_UI_VALIDATION.json bu aşamanın kod hash'lerini/kapsamını kaydeder.

Görevler sekmesinin dokuz published olayı iki retained Richard PE'sinde RTTI
adresleriyle eşleştirildi. Dokuz callback'te561f55 guard'ı görülmedi; bu,
yardımcıların hiçbir iç guard'ı olmadığı anlamına gelmez.4190 instruction kaydı
yeniden disk byte'larıyla karşılaştırıldı. Scope bir doğrudan Quest helper
katmanı ve TakeAll'ın nested row helper'ıdır; tüm semantic closure değildir.

Önemli ayrım: Hepsini Al4d5f20, seçili Görevi Al4d5a8c'yi çağırmaz.
Her satır için4d5e8c'yi çağırır. Bu gövde caption'ı StrToInt ile kayıt indeksine
çevirir, geçici Unicode'u temizler ve28byte kaydın entry0 DWORD'unu yerel
değişkene okur. Hepsini İptal Et4d6000 ise her satır için seçili İptal4d5f60
yardımcısını çağırır. O gövde aynı caption/cleanup yolundan sonra kaydın+4 data
pointer'ını, ardından pointer+1c için0045dc44 guarded DWORD sonucunu okur.
Sonuç bu caller'da kullanılmaz. Bu korunmuş normal gövdelerde seçili-Take veya
paket-enqueue çağrısı yoktur. Caption'dan ağ iptal/alma davranışı uydurulmadı.
Bu bulgu orijinalin bütün çalışma zamanında bu seçeneklerin hiçbir etkisi
olamayacağını kanıtlamaz: opaque helper/hook/SEH etkileri ayrıca açıktır.

Üç gerçek düğme kendi QuestMetadataFrame yaşam döngüsüne bağlandı. Sağlayıcı
yoksa kapalıdır; hazır örnek veri gerçek oyun verisi sayılmaz. Sağlayıcı açık
normal-return receipts ve immutable captured database tuple'ı verir. UI row
indeksi ile caption'dan gelen kayıt indeksi ayrıdır; row0 caption1 kayıt1'e
gider. Her child dönüşünden sonra güncel signed row count yeniden okunur.
Kendi64-phase/100ms chunk/FIFO, native UI/thread zamanlaması sertifikası değildir.

Frame setup, caption get, Int32 conversion, Unicode cleanup, guarded helper ve
epilogue normal dönüşleri ayrı gözlemlerdir. Ulaşılan caption/pointer/result
girdileri boşlukta korunur; sonraki tamamlamada eski snapshot gerekmez. Bilinmeyen
alan0/boş kayıt sayılmaz. Geçersiz caption için native exception sonucu tahmin
edilmez. Native unchecked addressing yerine açık fixture tuple sınırı vardır;
out-of-bounds tamamlanmış metadata okuması sayılmaz. Root0 native fault/yardımcı
sonucu uydurularak boş başarıya çevrilmez. Pointer0'dan guarded+1c sonucu ise
ancak açık gözlemle bilinir. Gerçek belleğe hiçbir adres erişimi yapılmaz.

Negative seçili indeks de child frame setup/epilogue sınırlarını korur ve
caption/record okumadan döner. İptal/profil değişimi read trace önekini eski
frame'de tutar; yeni document'e stale capture uygulanmaz. Profil sağlayıcıyı
ve timer'ı sıfırlar. Hiçbir yol ortak action queue'yu değiştirmez; durum mesajı
görev verisinin okunduğunu söyler, sunucuda görev alındı/iptal edildi demez.

GUI testi üç gerçek düğmeyi, row/record ayrımını, entry0 ile guarded1c trace
farkını, no-selection'ı, hidden form'da fresh count ve profil içinden dönen eski
capture'ı sınar.11 unit test ayrıca caption freeze, pointer/read prefix, invalid
caption, null/outside fixture, chunk ve idempotence'i kapsar. Eski seçili-Take
quest_engine.py planı ayrı ve henüz gerçek düğmeye bağlı değildir.

Sıradaki açıklar: Quest refresh/database üretimi, NPC filtreleme, seçili görev
detayları/compare, seçili Take/Give; gerçek kayıt/script edinimi ve native getter/
guard/protection/SEH/hook eşliği. Diğer özellik açıkları ve canlı oyun uyumluluğu
devam eder. Yeni REA decompile veya oyun bellek/ağ/eylem IO yapılmadı; kaynak
retained PE/Ghidra/DFM kanıtıdır. Sayılar tamamlanma yüzdesi/bitmiş fonksiyon
sayısı değildir.
