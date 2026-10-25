# Dört HP/MP getter'ının yerel native doğrulaması

`004611a0`, `004611c0`, `004611e0`, `00461200` yordamlarının 30'ar baytlık
gövdeleri ve `0045dc44` DWORD yardımcısının 48 baytlık gövdesi korunur.
Eski ve yenilenmiş modül kopyalarındaki dört getter'ın baytları aynıdır.
İki modülde toplam 140 komut kaydı ve API import kimliği dosyayla doğrulanır.

`native/vitals_getter_fixture.c`, bu 168 baytı yalnız kendi kod ve veri
sayfalarında çalıştırır. Dört kök yuvası operandı, dört alan ofseti yuvası
operandı, sekiz yardımcı CALL operandı ve bir API CALL operandı taşınır:
17 DWORD operandı. Diğer baytların değişmediği çalışma sırasında denetlenir.
Kod sayfaları çalıştırmadan önce RX yapılır. Özgün DLL yüklenmez.

12 senaryo: dört değer, üst bitleri dolu DWORD, sıfır kök yuvası, sıfır kök
değeri, ilk/ikinci koruma çağrısının kontrollü başarısızlığı, 32 bit adres
toplamının sıfıra veya kendi belleğine sarılması ve iki getter arasında kökün
değişmesi. Başarılı koruma çağrıları gerçek Windows VirtualProtect kullanır;
başarısızlık enjeksiyonu ve kendi sayfamız dışındaki adreslerin reddi test
sarmalayıcısının davranışıdır. Bu adresler Windows API'sine geçirilmez.

Sonuçlar, kök sıfır olsa bile getter'ın ofset eklemeye ve ikinci yardımcıya
devam ettiğini gösterir. Her getter kökü yeniden okur; toplu dört değer için
atomik snapshot garantisi yoktur. DWORD sonucu signed veya dar bir türe
dönüştürülmez. Tüketicilerin signed eşikleri ayrı davranışlardır.

Bu yerel deneyin gerçek oyun erişimi, güncel istemci adres profili, yüklü
oyundaki alan anlamları veya uçtan uca bot eylemleri hakkında kanıtı yoktur.
Dış süreç okuyucusunun ReadProcessMemory ve tutarlılık kontrolleri bu native
getter'larla aynı yöntem değildir; bu aşamada değiştirilmez. Hata/exception,
eşzamanlı değişiklik ve tüm runtime ABI yolları doğrulanmış değildir.

Yalnız fixture için 32 bit Windows derleyicisi gerekir:

```powershell
./native/build_vitals_getter_fixture.ps1 -CompilerPath C:/path/to/tcc.exe -OutputDirectory C:/path/to/owned-fixture
C:/path/to/owned-fixture/vitals_getter_fixture.exe
```

Fixture hedef PID, harici adres veya komut satırı parametresi kabul etmez.
Derlenmiş EXE dağıtım paketine eklenmez. 4.990 Python testi ile 12 native
senaryo ayrı kapsamlar olarak raporlanır; test sayıları toplanmaz.
