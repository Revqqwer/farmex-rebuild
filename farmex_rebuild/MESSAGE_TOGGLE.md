# Sıralı mesaj başlat/durdur yolu

23 Ekim 2026. `message_toggle.py`, Richard0045cbac'in post-prologue normal
yolunu ve btnAutoFloodClick004b169c çağıranını planlar. Yeni REA98-talimat
gövdeyle eşleşir. Eski/güncel iki ikilide toggle98, callback12 ve iki VCL
thunk1+1 olmak üzere224 disk kaydı doğrulanır. Native UI/string/SEH veya
mesaj işlemi çalıştırılmaz.

Kaynak düğme yazısını okumadan önce üç DWORD store yapar:

1. context+28=0 (zaman low)
2. context+2c=0 (zaman high)
3. context+24=0 (satır indeksi)

Bu prefix literal/Text/karşılaştırma dönüşleri beklerken de plan olarak
korunur. Vektör satırları burada yeniden derlenmez; boş listeyi önleyen
size/count kapısı da eklenmez.

Önce OTOMATIK FLOOD BASLAT literal'i oluşturulur, ardından mevcut düğme
Text'i okunur ve Unicode karşılaştırma helper'ı çağrılır. Ham EAX düşükAL
sıfır değilse start dalı, sıfırsa stop dalı seçilir. Sadece1 kabulü yoktur.
Karşılaştırma sonucu iki geçici cleanup boyunca PUSH/POP ile korunur.
Model native metin eşitliği algoritmasını tahmin etmez; AL gözlemi ayrıdır.

| Dal | Yeni düğme literal'i | Son BYTE store |
|---|---|---|
| Start yazısıyla eşleşme | OTOMATIK FLOOD DURDUR | context+20=1 |
| Eşleşmeme | OTOMATIK FLOOD BASLAT | context+20=0 |

Yeni literal oluşturma, Text setter normal dönüşü ve yeni literal cleanup
normal dönüşü ayrı girdilerdir. Setter normal döndüğünde kendi UI-update
planı çıkar; cleanup bitmeden çalışma bayrağı store'u çıkmaz. `enabled_byte`
seçilmiş dalın değeridir; gerçek memory/UI değişikliğinin kanıtı değildir.
Son normal sınır45ccd8, native epilog/SEH dışında tutulur.

Callback569910 context'ini geçirir ve561f55 profil gate'i içermez. Own
ClickFrame açık callback entry, tipli çocuk tamamlanması ve ayrı handler
normal dönüşünü ister. Bu gerçek VCL event tıklaması değildir.

12 yeni test; toplam3997 test geçti. UI378 bağlı/145 bağlanmamış olarak
değişmedi. Gerçek panel caption'ından çalışan sınıflandırma/UI trial bağı,
liste API'siyle oturum kompozisyonu, serializer/gerçek gönderim ve canlı
oyun uyumluluğu bu aşamada doğrulanmış değil. Gerçek mesaj gönderilmedi.
