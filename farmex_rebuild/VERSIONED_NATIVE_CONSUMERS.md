# Kaynak sürümünün iksir ve depo tüketicilerine bağlanması

19 Ekim 2026. `VersionedNativeObservation` artık yalnız ayrı registry denemesinde kalmıyor: alternatif iksir, depo item zinciri ve dış depo worker'ın sayfa dalı bu girdiyi tüketiyor. Eski raw fixture yolları korunuyor. UI ve native C değiştirilmedi; mevcut UI'nin kaynak-sürümü seçicisi yoktur.

`plan_alternate_potion` versioned skill gözleminde action ID'nin iksir intent'iyle aynı olmasını ister. Inventory ID ile action ID karıştırılmaz; direct yol için native bağ kabul edilmez. Çıktı `VersionedNativePlan` olarak kaynak hash'i, profil, gerçek helper ve canonical rolü korur. Native result yoksa nonzero sonucu bilinmez kalır; alternatif çağrı direct pakete çevrilmez. Raw `SkillObservation` yolu eski `SkillPlan` çıktısını korur.

`StorageItemObservation.native_observations`, raw veya sürümlü depo girdileri alır. Ulaşılan her çağrıda canonical helper/argüman eşleşir. Sürümlü çıktılar `native_plans` içinde wrapper'ıyla kalır; örneğin kaynak `004fe290`, model rolü `004fe274` olarak ayrı görülebilir. Bu eski adrese çağrı yapıldığı anlamına gelmez.

Bir item çağrısında ulaşılan sürümlü yaprakların kaynak hash'i ve profili aynı olmalıdır. Aynı zincirde raw/versioned karışımı da reddedilir. Ulaşılmayan ikinci gözlemdeki farklı kimlik değerlendirilmez; erken empty-item çıkışında helper-role uyuşmazlığı aranmaz. Bu, tipli girdilerin kendi yapısal doğrulamasını kaldırmaz.

Sürümlü depo girdisinin çağrı veya yazım planı hazır olsa bile `normal_returned=True` ayrıca gerekir. Factory bu alanı açık parametre olarak taşır. Eksikte item sonraki quantity/confirm adımına, dış worker da sonraki slot adımına geçmez. Sayfa helper'ından **önce** gerçekleşen kaynak sayaç artışı prospective sonuçta korunur; eksiklikte geçmiş kaynak adımı geri alınmış gibi gösterilmez. Gerçek oyun belleğine hiçbir yazım yapılmaz.

`storage_worker_step` item alt planındaki kimlikleri korur. Sayfa `0046fdf8` bağında da sürümlü planı saklar ve ayrı helper normal dönüşünü ister. Child planın hazır olması çağrının gerçekten yürüdüğünü, eşya transferini veya server ACK'yi kanıtlamaz.

**10 yeni testle toplam2697 birim testi geçti (7.000s).** Güncel iksir hedefleri, action/domain uyuşmazlığı, slot→quantity→confirm zinciri, eksik normal dönüşler, ulaşılan/ulaşılmayan kimlik karışımı, worker item sayaç kapısı ve page helper kapısı test edildi. Dört modül ayrıca ayrı yeni Python süreçlerinde import edilerek döngüsel import hatası olmadığı kontrol edildi. Yeni testler canlı oyun veya native çağrı testi değildir.

Bağ önceki `FarmexBot_native_profil_surumu_kaniti.json` içindeki76alan/9helper/1022talimatlık kaynak kanıtını kullanır. Bu tur yeni ikili davranış veya canlı trace keşfedildiği iddia edilmez. Tüketicilerin tamamının güncel Richard ile eşdeğerliği, yüklenmiş profil/offset değerleri, hedef ABI'si ve gerçek eylem doğrulaması açık kalır.
