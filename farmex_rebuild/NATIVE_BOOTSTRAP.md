# Yerel PE başlangıç doğrulaması

23 Ekim ek kanıtı: özgün Loader işçisinin152 talimatı/431 byte'ı, kendi sentetik
görüntümüzde değiştirilmeden15 native senaryoyu geçti.
[Özgün işçi testi](SOURCE_LOADER_WORKER_NATIVE.md). Aşağıdaki16 Ekim deneyi
bağımsız yeniden yazılmış hazırlayıcıya aittir; kapsamlar ayrı korunur.

16 Ekim 2026. Kendi HP/MP DLL'imiz, kendi x86 test programının özel bellek alanına yerleştirilerek başlatıldı. Windows `LoadLibrary` bu DLL için kullanılmadı. Üretim oyun bağlantısı henüz doğrulanmadı.

## Kaynakla kurulan bağ

Orijinal Loader'ın `0041e558` işçisinin 152 assembly kaydı, SHA256 `97d946ddec5df814e0042384b78b711c029f136aa6c43701910fd21cef5a0775` dosyasının baytlarıyla yeniden karşılaştırıldı. Ghidra kaydı `Ghidra_Loader_baglanti_ek_zincir.json` dosyasındadır; REA Evidence veya canlı çağrı izi değildir. Özgün işçi bu testte çalıştırılmadı.

İşçi görüntü tabanı farkını hesaplar, relocation tablosundaki sıfır olmayan girdilerin düşük 12 bitini kullanarak DWORD adresleri düzeltir, import lookup tablosunu çözer ve giriş noktasını `(modül, 1, 0)` argümanlarıyla çağırır. Import descriptor sonunu `OriginalFirstThunk == 0` ile bulur; genel bir PE yükleyicisindeki bütün durumları desteklediği sonucu çıkarılmaz. Relocation türünü ayrıca ayırmaz. Kendi DLL'imizde sıfır dolgu dışındaki bütün girdiler HIGHLOW olduğundan bu özel örnekte aynı düzeltme işlemi geçerlidir.

## Çalıştırılan bağımsız örnek

`native/local_bootstrap_fixture.c` yalnız derleme sırasında içine gömülen kendi DLL baytlarını kullanır. DLL SHA256 değeri `4510845e33931b26da0381adfa12e414c4ef72d9c0206728952f6ecfe1903c3a`, dosya boyutu 10752 bayttır. Derleme betiği bu kimliği zorunlu tutar; çalışma anında DLL yolu veya hedef PID kabul edilmez. Üretilen EXE ve gömülü bayt başlığı kaynak ZIP'ine eklenmez.

Doğrulanan sonuçlar:

- Tercih edilen `0x10000000` yerine farklı yerel tabanda başlatma; belleğin türü `MEM_PRIVATE`.
- 116 HIGHLOW düzeltmesi ve 43 import çözümlemesi; sayılar DLL dosyasından ayrı hesapla karşılaştırıldı.
- Yalnız sistem dizinindeki `kernel32.dll` ve `msvcrt.dll` bağımlılıkları; DLL bölümlerine ayrı yerel korumalar.
- PE giriş noktasının normal attach dönüşü; kendi süreç verisinden 24 baytlık HP/MP okuması.
- Üretim API'sinin kendi test programını yanlış süreç olarak reddetmesi; bu yolda bellek okuması sıfır.
- Kritik bölüm başlatıldıktan sonra 84 baytlık sentetik çerçeve yayını; 64 bit Python'un `FILE_MAP_READ` ile HP 250/500 ve MP 100/300 alması.
- Python okuyucusu kapandıktan sonra detach çağrısı; paylaşım alanının artık bulunmaması.

Okuyucu sonucu `fixture_candidate`, bağımsız doğrulama değeri `false` kaldı. DLL Windows yükleyici listesine kaydedilmedi. `DisableThreadLibraryCalls` dönüşü bu deneyde ölçülmedi; normal Windows yükleyicisinin TLS/modül kayıt hizmetlerinin eşdeğeri olduğu iddia edilmez. TLS, gecikmeli import, CLR ve farklı PE biçimleri destek kapsamı dışındadır.

Derleme örneği, önceden hazırlanmış ve yukarıdaki kimlikle eşleşen kendi DLL'imizi gerektirir:

```powershell
.\native\build_local_bootstrap_fixture.ps1 -CompilerPath 'C:\tools\tcc\tcc.exe' -BridgePath 'C:\work\own\farmex_vitals_bridge.dll' -OutputDirectory 'C:\work\own-bootstrap'
```

Çalışma kaydı üst çıktı dizinindeki `FarmexBot_yerel_PE_baslangic_testi.json`, yeniden doğrulama betiği çalışma dizinindeki `work/verify_local_bootstrap.py` dosyasıdır. Bu native test için Python birim testleri ve UI tekrar çalıştırılmadı; önceki 1679 birim testi ve UI sonucu kendi önceki kapsamıdır.

## Canlı bağlantıda kalanlar

Yerel başlangıç, orijinal Loader'ın süreçler arası taşıma yolunu sınamaz. Test oyun süreci seçmez; oyuna modül taşımaz, thread açmaz, bellek okumaz veya yazmaz. Oyunda verilen erişim hakları, gerçek HP/MP alanları, thread/hook hazırlığı, oyun çağrılarının ABI'si ve sunucu sonuçları hâlâ doğrulanmalıdır. Bu deneyin geçmesi mevcut VM_READ engelini çözmüş sayılmaz.

Orijinal modülün VCL/Borland bağımlılıklarının ve initializer etkilerinin yerine bu küçük DLL konulmadı. Bağımsız DLL'imizin yerel başlatılabilirliği ile orijinal modülün bütün çalışma ortamı ayrı kanıtlardır.
