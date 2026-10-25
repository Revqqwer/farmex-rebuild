# Özgün Loader işçisinin kendi belleğimizde çalıştırılması

23 Ekim 2026. Loader SHA256
`97d946ddec5df814e0042384b78b711c029f136aa6c43701910fd21cef5a0775`
içindeki `0041e558` işçisinin 152 talimatı, toplam 431 byte olarak aynen
çıkarıldı. Hiçbir CALL operandı veya başka byte değiştirilmedi. Doğrudan
dallar gövde içinde kalıyor; dört çağrı da context/stack işaretçilerinden dolaylı.
Kod ayrı kendi sayfamızda RX yapılarak çalıştırıldı.

Önceki [kopyalanan worker](COPIED_WORKER.md) deneyindeki 3772 byte bağımsız
yeniden yazılmış işçiye ek kanıttır. Bu yeni deney özgün 431 byte'ı çalıştırır;
Loader'ın tüm dış süreç aktarma zincirini veya orijinal DLL'leri çalıştırmaz.

Kendi programımız 4096 byte sentetik görüntü ayırır. 24 byte context;
görüntü, NT başlığı, relocation ve import adresleri ile yalnız kendi iki API
sarmalayıcımızı taşır. Kütüphane/sembol çözümleyicileri kontrollü sahte sonuç
verir; gerçek DLL yüklemez. Sentetik giriş noktası kendi callback'imize gider
ve `(görüntü,1,0)` argümanlarını denetler. Dış PID, yol veya payload girdisi yoktur.

15 native senaryo geçti:

- Boş tablolar/giriş noktası yok: EAX1.
- Giriş callback'i true, false ve `0x12345678`: aynı tam EAX geri döner.
- Kütüphane, ad ve ordinal çözüm hataları: EAX0; sonraki giriş çağrılmaz.
- Ad ve ordinal42 başarısı: IAT yalnız kendi export adresimizle dolar.
- Pozitif/negatif taban farkı, sıfır relocation girdileri ve birleşik relocation→import→entry akışı.
- Tür1 relocation girdisinde de kaynak DWORD ekler; genel tür doğrulaması yapmaz.
- OriginalFirstThunk sıfırsa descriptor sonu sayılır; FirstThunk fallback'i uygulanmaz.

Bu 15 sayı native senaryodur; 3860 Python testine eklenmedi. Python çalışma
dosyaları önceki paket manifestiyle aynı olduğundan tam Python/UI testleri
tekrarlanmadı; mevcut sonuçlar kendi eski kapsamlarında korundu.

152 talimatın kaynak gövdesi doğrulandı; tüm talimatların/path'lerin native
kapsama ölçümü yapılmadı. Bozuk tablolar, exception, sınırsız döngüler, gerçek
Windows import çözümü, orijinal DLL attach'i, uzak aktarım, askıda oyun başlangıcı,
güncel oyun adresleri ve canlı HP/MP bu deneyle doğrulanmaz. Oyun erişim hakkı
engelini kaldırmaz. Kendi görüntü sayfamız RWX; worker sayfası RX'tir. EXE ve
ham kaynak DLL dosyaları dağıtım paketine eklenmez.
