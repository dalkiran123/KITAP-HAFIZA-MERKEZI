# BOOK CENTER V5.1: Sanal Yaşam sunucu kurulumu

Bu servis **mevcut BOOK CENTER uygulamasından ayrıdır**. Kurulum, yayın ve zamanlanmış görev başlatma işlemleri henüz yapılmamıştır.

## 1. Ayrı veritabanı
PythonAnywhere üzerinde özel, dışarıdan erişilemeyen bir dizin seçin:

```bash
export BOOKCENTER_PEOPLE_DB=/home/USERNAME/private_bookcenter/people.sqlite3
mkdir -p /home/USERNAME/private_bookcenter
cd /home/USERNAME/KITAP-HAFIZA-MERKEZI/kisiler
python deploy_check.py
python people_engine.py init
```

`USERNAME` yerini gerçek PythonAnywhere kullanıcı adıyla değiştirin. Mevcut uygulama veritabanının yolunu **kullanmayın**.

## 2. Önce elle test

```bash
python scheduled_world.py
python people_engine.py status
```

Tekrarlanan çağrıda aynı saat ve güne ait olaylar yeniden oluşmamalıdır. `scheduled_world.py` işlem çakışmalarını önlemek için kilit dosyası kullanır. Süreç çökerse kalmış kilit dosyasını silmeden önce çalışan süreç olup olmadığını doğrulayın.

## 3. Ayrı WSGI uygulaması

Yeni ve ayrı bir PythonAnywhere web uygulamasında `people_api.application` WSGI callable'ını kullanın. API yalnızca GET ile veri sunar; profil güncelleme veya mesaj yazma uç noktası açılmaz. Üretimde HTTPS kullanın.

## 4. Zamanlanmış görev

PythonAnywhere Scheduled Tasks üzerinden uygun plana göre saatlik şu komutu tanımlayın:

```bash
cd /home/USERNAME/KITAP-HAFIZA-MERKEZI/kisiler && BOOKCENTER_PEOPLE_DB=/home/USERNAME/private_bookcenter/people.sqlite3 python scheduled_world.py
```

**Önemli:** Bu adımlar talimattır, otomatik kurulmuş değildir. PythonAnywhere hesap erişimi, uygulama alan adı, plan ve görev sınırları doğrulanmadan çalıştırmayın.

## 5. GitHub Pages bağlantısı

API erişilebilir ve test edilmişse `kisiler/config.json` dosyasındaki `apiBase` alanına yalnızca doğrulanmış HTTPS sunucu adresini yazın. Daha önce kullanılmış bir alan adını tahmin etmeyin. Kişisel bilgileri veya özel karakter hikâyelerini halka açık API'de yayımlamayın. Mevcut servis, yalnızca kurgusal ve herkese açık olması uygun veriler için tasarlanmıştır.

## 6. Geri dönüş

Yeni görevi durdurun ve yeni WSGI uygulamasını kapatın. Eski BOOK CENTER dosyalarını, mevcut kitap otomasyonlarını ve veritabanlarını değiştirmeyin. Ayrı sanal yaşam veritabanını silmeden önce yedek alın.
