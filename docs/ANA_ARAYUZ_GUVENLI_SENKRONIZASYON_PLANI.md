# Ana arayüz / çok kullanıcılı entegrasyon planı

Durum: GELİŞTİRME DALINDA. Canlı yayına alınmadı.

## Doğrulanmış temel
- Mevcut `index.html` korunacak; `multiuser/mobile/index.html` onun yerine geçmeyecek.
- `multiuser/web_app.py` yalnızca prototip WSGI sunucusudur.
- `/my/sync` kayıtları `book_id`, `revision` ve `state` içerir. Desteklenen alanlar: `read`, `done`, `listened`, `lastRead`, `lastListened`, `notes`.
- Sunucu tam kitap özetlerini, kapakları, kitap istek geçmişini veya tam ses dosyalarını bu API ile saklamaz.
- Canlı B2B WSGI dosyasına ve `BOOK_DATA` verilerine bu dalda dokunulmaz.

## Uygulama sırası
1. Ana arayüzdeki tüm localStorage anahtarları, kitap şeması, istek geçmişi ve yedekleme akışı envanterlenecek.
2. Kullanıcı giriş ekranı ve sunucu bağlantı durumu, mevcut ana ekrana *ek* olarak geliştirilecek.
3. İlk girişte **salt okunur karşılaştırma**: yerel kitaplar ile `GET /my/sync` kayıtları; kullanıcıya kayıp/çakışma raporu. Otomatik üzerine yazma yok.
4. Yalnızca desteklenen durum alanları, `GET /csrf` ile alınan token ve `expected_revision` kullanılarak gönderilecek.
5. HTTP 409 çakışmasında güncel sunucu kaydı alınacak; otomatik silme veya sessiz son-yazan-kazanır yok.
6. Özet, kapak, istek geçmişi ve ses içerikleri için ayrı veri modeli, boyut sınırları ve migrasyon/test tasarlanacak. O zamana kadar yerel JSON yedeği korunacak.
7. İki kullanıcı izolasyonu, iki cihaz çakışması, yetkisiz istek, CSRF, çıkış, yedek geri yükleme ve regresyon testleri geçmeden yayın yapılmayacak.

## Kabul kriterleri
- Numan34'ün 30 kitap, 25 okuma olayı ve 3 puan kaydı değişmeden kalmalı.
- Yerel 6/20 paragraf özetleri ve 21 kitap isteği geçmişi silinmemeli.
- Mevcut ana arayüzün görünümü ve seslendirme davranışı regresyon testinden geçmeli.
- İkinci cihazda aynı hesaba ait kayıtlar görünmeli; farklı kullanıcıya ait kayıtlar görünmemeli.
- B2B CONTROL WSGI geçişi ayrı, geri dönüşü hazır yayın adımı olmalı.

## Güvenlik
- Oturum çerezi HttpOnly + Secure + SameSite=Strict kalmalı.
- Şifre ve oturum token'ı tarayıcı localStorage'a veya loglara yazılmamalı.
- Gerçek veritabanında otomatik test yapılmamalı; testler geçici SQLite üzerinde çalışmalı.
