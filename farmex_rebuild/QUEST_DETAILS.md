# Görev ayrıntıları — yerel API aşaması

`QuestDetailsFrame`, kaynak `004b4848` → `004d5738` akışının başlık ve
satır güncellemelerini modeller. Gerçek liste tıklamasına henüz bağlı değildir.
Tam yerel test sonucu `QUEST_DETAILS_VALIDATION.json` içindedir.

Seçili görünür satırın caption'ı StrToInt ile koleksiyon indeksine çevrilir.
Görünür sıra numarası doğrudan kayıt indeksi sayılmaz. Negatif seçim ayrıntıları
korur; negatif/bozuk caption farklıdır, kayıt0 veya boş başarıya çevrilmez.
Kendi kayıt/kolon sınırı dışı durumlar native bellek veya getter hatası
uydurulmadan eksik bırakılır.

Önce sütun0 başlığı `Level : ` ve signed32 sayısal metinle, sonra sütun1 başlığı
görev adıyla güncellenir. PE import kimlikleri bu çağrıların TListColumns.GetItem
ve TListColumn.SetCaption olduğunu doğrular. Bunlar eski ayrıntı satırlarına
yazma değildir. Başlık atamaları ve temizlikleri bittikten sonra satırlar silinir.

Kaynak normal akışında şu dört satır eklenir:

| Başlık | Alt alan |
|---|---|
| NPC: | Kayıttaki NPC adı |
| - | Görev |
| boş | boş |
| - | Ödül |

Bu etiketler gerçek gereksinim/ödül listesi değildir; bu gövdede kanıtlanmamış
veri sorgusu veya script çözümlemesi eklenmedi. Aradaki boş Add çağrısı korunur.
Seviye, görev adı ve NPC alanları farklı aşamalarda yeniden okunur; daha önceki
alanın temizlik boşluğu sonraki alanın gözlemini erken tüketmez.

Native helper normal dönüşleri, scalar sonuçlar ve Unicode dönüşümleri ayrı
gözlemlerdir. Açık seçimle mevcut scalar modeli kullanılabilir. Görev/NPC
adları ve iki Türkçe literal için bağımsız kod sayfası veya açık Unicode sonucu
gerekir. Null/bilinmeyen byte alanı boş string kabul edilmez.

Eksik dönüş veya düzeltilebilir yerel dönüşüm hatasında yazılmış başlık/satır
öneki korunur ve devamda tekrar eklenmez. Haricî ayrıntı görünümü değişikliği
çatışma olarak kalır. Bu kendi yaşam döngüsü/snapshot politikasıdır; native
VCL, refcount, formatter, getter exception veya SEH eşliğini kanıtlamaz.

16 yeni testle toplam4873 Python testi geçti. Yeni GUI koşulmadı; önceki4857
aşamasının901 kod kaynağı ve GUI log hash'leri değişmedi. Yeni iki dosya
API/test ekidir. İki saklanan PE'de664 instruction kaydı ve kolon import/literal
baytları doğrulandı; yeni REA decompile veya canlı oyun çalışması yapılmadı.
