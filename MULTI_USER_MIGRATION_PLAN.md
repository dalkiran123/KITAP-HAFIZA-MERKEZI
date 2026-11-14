# Çok Kullanıcılı Kitap Hafıza Merkezi - Güvenli Geçiş Tasarımı

Durum: Tasarım ve hazırlık. CANLIYA ALINMADI.
Hedef: En fazla 100 kayıtlı hesap; mevcut çalışan sürüm, kitaplar, sesler ve telefon verileri korunur.

## Mevcut durum
- GitHub deposu public ve statik index.html / catalog.js içeriyor.
- V2-PLAN.md kullanıcı verilerinin tarayıcı localStorage üzerinde tutulduğunu belirtiyor.
- GitHub Pages tek başına güvenli kullanıcı kimlik doğrulama, sunucu veritabanı veya senkronizasyon sağlamaz.
- Public GitHub'a kullanıcı verisi, şifre, veritabanı veya yedek yüklenmeyecek.

## Güvenli uygulama aşamaları
1. Mevcut main commit'ini sabitle; canlı sürümle otomatik dağıtımı doğrula. Kod yedeği ile telefon verisi yedeğini ayrı al.
2. Telefon verileri için mevcut localStorage anahtarlarını değiştirmeden, dışa aktarma ve içe aktarma doğrulama testi oluştur. Kullanıcının cihazındaki veriler izinsiz silinmez.
3. Güvenli backend seç ve erişimini doğrula. 100 hesap sınırını sunucuda uygula. Parolaları Argon2id veya eşdeğer güçlü adaptif algoritmayla hashle; oturumları güvenli cookie ile yönet. Yönetici yetkisi yalnızca sunucuda doğrulanır.
4. Merkezi veri modeli: users, books, reading_events, ratings, requests, progress, audit_events. Kullanıcıya ait satırlar user_id ile ayrılır. Kitap içeriği ortak kalır.
5. Kullanıcı girişinden sonra tek seferlik idempotent veri aktarımı: önce önizleme ve sayım, sonra onaylı aktarım, ardından karşılaştırma ve geri alma imkânı. Mevcut localStorage en azından geçiş kabulüne kadar korunur.
6. Admin: kullanıcı sayısı, etkinlik, okuma sıralaması, kitap üretim ve seslendirme hata durumları. Kullanıcı şifreleri asla gösterilmez.
7. GitHub Actions testleri: statik regresyon, auth/role izolasyonu, 100 kayıt sınırı, eşzamanlı güncelleme, veri aktarımı, yedek geri yükleme. Canlıya otomatik yayın ancak doğrulanmış yayın bağlantısı ve başarılı testlerle.
8. 100 kayıtlı kullanıcı ile 100 eşzamanlı kullanıcı farklı kapasite hedefleridir. Yük testi ayrıca yapılır.

## Yayına alma koşulları
- Mevcut canlı sistemin kodu ve telefon verisi için geri dönüş yolu kanıtlandı.
- Yeni backend, alan adı, ücretsiz kota ve erişim doğrulandı.
- Admin ilk hesabı güvenli kurulum yoluyla oluşturuldu; hiçbir varsayılan parola repoya yazılmadı.
- Kullanıcı verisi aktarım testi ve iki cihazdan eşitleme geçti.
- Saatlik kitap üretim planları ve mevcut kitap kataloğu etkilenmedi.
- Bu koşullar sağlanana kadar main branch değiştirilmez.
