# Kendi x86 ValLong stream fixture'ı

`build_rtl_integer32_fixture.ps1`, hash-pinned TinyCC ile `rtl_integer32_fixture.c` dosyasını derler. Ortak EAX/EDX çağrı ve static refcount=-1 UnicodeString header hazırlığı önceki `rtl_integer_fixture.c` içinden kullanılır. Derlenmiş executable kaynak ZIP'e eklenmez.

Program tek argüman olarak mutlak pinned standart RTL yolunu kabul eder. stdin her satırında UTF16 little-endian hex alır; `-` nil, boş satır nonnull boş string'dir. En fazla4000UTF16 birimi kabul edilir. Modül yüklenen path'i denetler ve Initialize export'unu bir kez çağırır. Her native ValLong çağrısından EAX, Code ve ESP dengesi JSON satırı olarak çıkar. Başka PID/handle/bot modülü veya ağ hedefi alınmaz.

Fixture SHA256: `4f5c90c06b04e5398b84d7011c3d91ce42f5b745c4e17024989aaaef33201579`. RTL SHA256: `7d98acb8fade7f0920c0f544eaf5525afaf8c8c1afb82e77544cf29ac75eddd8`. Çalışma dizinindeki `check_rtl_integer32_native.py`, deterministic seed32 ile2000-case girdiyi ve native trace'i üretip model EAX/Code eşliğini denetler. Nil, UTF16 surrogate, NUL, taşma ve hex/decimal işaret durumları matrise dahildir.

Doğrulama bu kendi scalar çağrılarına aittir. Program StrToInt exception mekanizmasını emüle etmez ve özgün bot callback'ini çalıştırmaz. Üst kapsam `RTL_INTEGER32.md` içindedir.
