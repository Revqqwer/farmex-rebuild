# NPC rota isim üreticisi

4575 Python testi geçti;8 yeni test. Kayıt ROUTE_NPC_NAME_VALIDATION.json.

API route_npc_name.py, açık nonzero actor adresinden storage ofseti/guarded DWORD ve ayrı helper dönüşünü tüketir. Kaynak ANSI/std başlangıç adımları ayrı normal gözlemler ister. Signed storage<16 için inline adres ve255 byte, diğer dal için ayrı guarded pointer ve ham storage kopya uzunluğu kullanılır. Inline dalı pointer okumaz; negatif signed storage da inline dalındadır.

512 byte sıfır şablon ve fallback NUL kaynakta doğrulandı. Açık IsBadReadPtr sonucu/copy byte aralığından ilk NUL'a kadar ANSI byte'ları çıkarılır; Unicode decoder gerekmez. Copy, ANSI assignment, geçici cleanup ve std assignment normal gözlemleri birbirinden bağımsızdır. Son capture NpcClickFrame'e bağlanarak DC Sundries satırı testi geçmiştir. Geç User Trade Unicode dönüşümü ayrı kalır.

>512 okunabilir kopya veya512 byte içinde NUL olmaması unresolved kalır. Okunamayan alan kaynak fallback'iyle boş isim verebilir; bunun normal helper/string dönüşleri yine ayrıca gerekir. Belleğe erişilmez ve koruma değiştirilmez.

2471 instruction kaydı yeniden doğrulandı; güncel helper importları LStrAsg ile geç UStrFromLStr ayrımını gösterir. Yeni GUI çalıştırılmadı:332-modül closure/log hashleri4567 tam GUI ile aynıdır, yeni dosyalar closure dışındadır. Bu API otomatik veri sağlayıcısı değildir. Native RTL/copy/SEH ve canlı oyun doğrulaması açık kalır.
