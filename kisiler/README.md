# BOOK CENTER V5.1 — Kişiler altyapısı

Bu dizin **geliştirme prototipidir**. Üretim sistemine entegre edilmemiştir.

## Yerel deneme

```bash
cd kisiler
python people_engine.py init
python people_engine.py tick
python people_engine.py status
python -m unittest -v test_people_engine.py
```

Veriler varsayılan olarak `people.sqlite3` dosyasına yazılır. `BOOKCENTER_PEOPLE_DB` ile konumu belirlenebilir. Bu dosyayı GitHub'a commit etmeyin. SQLite dosyasını erişimi sınırlı, kalıcı bir sunucu dizininde tutun.

## PythonAnywhere planı

1. Ayrı bir sanal ortam ve kalıcı veritabanı dizini oluşturun. Mevcut kitap/belgesel zamanlayıcılarına dokunmayın.
2. Önce `init`, sonra elle bir kez `tick` çalıştırıp `status` çıktısını kontrol edin.
3. Bağımsız scheduled task ile her saat `tick` çalıştırın. PythonAnywhere hesap türünün görev sıklığı sınırlarını kontrol edin.
4. Zamanlayıcı çıktısı ve SQLite yedeği için izleme kurun. Aynı saat için yinelenen çağrı idempotenttir.
5. **Sunucu bağlantısı kurulmadan** tarayıcıdaki kişileri gerçek sunucu botları olarak göstermeyin.

## Mevcut eksikler / yayın engelleri

- Okuma simülasyonu henüz gerçek kitap katalog kimlikleriyle eşleşmiyor. Kitap tamamlama sayısı, 180 dakikalık simüle sürenin yaklaşık eşiğidir; gerçek kitap okunduğu anlamına gelmez.
- Mevcut kullanıcıya ait doğrulanmış kitap sayısı ve süre henüz sunucuya aktarılmıyor.
- Tarayıcı prototipi localStorage kullanıyor; sunucu veritabanına bağlı değil.
- Arkadaşlık ve mesaj tabloları hazır, ancak kimlik doğrulamalı API ve bot yanıt servisi yok.
- Botlar kendi kendine mesaj göndermiyor. Saatlik motor yalnızca simüle okuma etkinliği üretiyor.
- Gerçek kişiler için oturum yönetimi, yetkilendirme, engelleme ve gizlilik önlemleri gerekiyor.
- Saatlik servis henüz PythonAnywhere'de kurulmadı.
- Ana sayfa Arena kartının kaldırılması ve Kişiler butonu eklenmesi henüz yapılmadı.

## Geçiş ve veri güvenliği

Mevcut Arena localStorage anahtarları silinmeyecek. Önce okunabilir yedek alınacak. Bot adları ve uygun etkinlik kayıtları, veri şeması doğrulandıktan sonra bir kez taşınacak. Arena maç puanları yeni okuma ligi puanına dönüştürülmeyecek.

## Kabul testi

- 10 sanal profil, ayrı kimlikler ve ayrı geçmişler.
- Sunucu saatlik tetikleme, tekrar tetiklemede çift sayım yok.
- Sunucu durup açıldığında veriler kalıcı.
- Gerçek katalog kitabı bazlı tekil tamamlanma kayıtları.
- Gerçek kullanıcı istatistikleriyle karşılaştırılabilir okuma ligi.
- Karşılıklı arkadaşlık istekleri ve kalıcı, yetkili sohbet.
- iPhone PWA kapalıyken zamanlayıcıyla yeni etkinlik oluşması.
- Mevcut kitap üretim otomasyonları ve okuma kayıtları değişmeden çalışıyor.

Bu maddelerin tamamı geçmeden ana dala birleştirme ve canlı yayın yapılmamalıdır.
