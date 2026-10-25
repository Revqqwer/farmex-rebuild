# Merchant satıcı metadata üreticisi — çalışma adayı

`merchant_actor_metadata.py`, WORD entity ID'den actor lookup normal dönüşünü, kaynak koordinat çağrılarını ve ad okuma alanlarını mevcut kendi veri modellerine bağlar. Bellek okumaz, koruma değiştirmez veya native çağrı yapmaz. Koordinat float okuyucu dönüşü, `__ftol` normal dönüşü ve EAX sonuçları ayrı açık gözlemlerdir; Python yuvarlaması ile doldurulmazlar.

Kaynak X/Y offsetlerini sırasıyla 0x554008 ve 0x554010 globalinden alır; actor+offset adreslerini 0045ddb8'e verir ve CC32260MT.DLL `__ftol` sonrasında yalnız EAX'i saklar. Üretici bu sıra ve tamamlanan koordinat önekini korur. Actor lookup sıfırsa kaynak koordinat store'larını atlar; yerel değişkenlerin sıfırlandığı kanıtlanmadığından boş isim/sıfır koordinat kaydı uydurulmaz.

Ad için storage offseti 0x553fec, data field offseti 0x553fe8 globalinden gelir. İlk data DWORD okuması inline dalda bile yapılır. Storage unsigned >=16 ise bu DWORD pointer ve storage count kullanılır. Daha küçükse 0x553fe8 yeniden okunur; aynı offset olduğu varsayılmadan actor+freshOffset ve255 byte seçilir. Mevcut `npc_text_request(..., signed_threshold=False)` bu ayrımı sağlar.

Mevcut `replay_text_copy` IsBadReadPtr sonucu, tam captured byte aralığı,512 sınırı ve ilk NUL davranışını uygular. Read-rejected boş isim ile eksik capture aynı şey değildir. Tam512 byte içinde NUL yoksa kaynak overread kapsamı açık kalır. Açık yerel decoder verilmeden nonempty ANSI isimden Unicode satıcı metni üretilmez. Native runtime codepage, string ABI veya heap eşliği iddia edilmez.

`project_merchant_reply_values` bu actor üreticisini item lookup/name üreticisi ve mevcut raw/record/filtre/sütun zincirine bağlar. Dolu slotun actor üreticisi tamamlanmazsa item gözlemleri tüketilmez. Tamamlanmış yerel zincir; özgün interleaved event, native parse/finish dönüşü, gerçek GUI veya oyun etkisi değildir.

10 yeni test ve toplam4169 test geçti (`work/merchant_actor_metadata_full_tests.log`). İki Richard sürümünde4352 talimat kaydı, actor alan operandları, iki koordinat dönüşünde aynı `__ftol` importu ve unsigned isim dalı doğrulandı (`FarmexBot_merchant_actor_metadata_kaniti.json`). Yeni başarılı REA analizi yok; mevcut Ghidra ihracatı kullanıldı.

Bu çalışma adayı henüz son ZIP'e eklenmedi. Son doğrulanmış kaynak ZIP4159 test ve tam GUI1037 kontrol/11form/18sekme sürümüdür; mevcut actor API'si panel kodunu değiştirmedi. Native lookup/read/ftol sonuçlarının gerçek veri üreticileri, kod sayfası/normalizasyon, panel/sıralama/hücre eylemleri ve gerçek oyun uyumluluğu hâlâ açıktır.
