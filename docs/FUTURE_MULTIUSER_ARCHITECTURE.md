# Telefon-öncelikli kullanım ve gelecekte çok kullanıcılı geçiş

## Bugünkü ürün sözleşmesi
- Tek cihaz ve tek kullanıcı; giriş ekranı veya sunucu bağımlılığı yok.
- Kitaplar, okuma/dinleme geçmişi, puanlar, istekler ve video izleme ilerlemesi mevcut tarayıcı localStorage alanında kalır.
- Mevcut localStorage anahtarları yeniden adlandırılmaz veya sessizce silinmez.
- Kitap ve video katalogları herkese açık, sürümlenebilir içerik olarak kalır; kişisel ilerleme kayıtları katalog dosyalarına yazılmaz.
- Otomatik içerik üretimi ile kişisel ilerleme verileri birbirinden bağımsız tutulur.

## Gelecekte hedeflenen mantıksal veri modeli (henüz uygulanmadı)
- users: id, username, password_hash, created_at, status.
- catalog_items: id, kind (book/video), title, category, source_url, license, published_at, version.
- user_progress: user_id, item_id, mode (read/listen/watch), seconds_consumed, percent, updated_at.
- user_ratings: user_id, book_id, score, updated_at.
- user_activity: id, user_id, item_id, event_type, occurred_at.
- user_requests: id, user_id, title, status, created_at.
- UNIQUE(user_id,item_id,mode) gibi kısıtlar tekrar eden ilerleme kayıtlarını önler.

## Geçiş koşulları
1. Geçişten önce tarayıcı verilerinin kullanıcıya indirilebilir JSON yedeği ve geri yükleme testi hazırlanır.
2. Mevcut anahtarları yalnızca okuyan, sürümlü bir içe aktarma adaptörü yazılır; örnek kayıtlar ve eksik alanlar test edilir.
3. Kullanıcı hesabı oluşturulup doğrulandıktan sonra cihaz kayıtları kullanıcı onayıyla hesaba aktarılır. Anonim cihaz verisi otomatik olarak başka hesapla eşleştirilmez.
4. Sunucuda şifreler düz metin tutulmaz; güçlü parola karması, TLS, oturum yönetimi ve kullanıcı bazlı yetkilendirme gerekir.
5. Kullanıcı bazlı izlenme sayısı ancak merkezi sunucu olayı doğrulamasıyla gösterilir. Yerel açılma sayısı global izlenme sayısı değildir.
6. Geçiş aşamalı ve geri alınabilir olmalıdır. Eski tek kullanıcılı mod, yeni sistem doğrulanana kadar çalışır.

## Şimdilik yapılmayacaklar
- Kullanıcı hesabı oluşturma veya giriş zorunluluğu.
- Telefon kayıtlarını otomatik olarak bir sunucuya gönderme.
- Merkezi veritabanı kurma, kullanıcıları birleştirme veya veri taşıma.
- Test edilmemiş özellikleri tamamlandı diye raporlama.
