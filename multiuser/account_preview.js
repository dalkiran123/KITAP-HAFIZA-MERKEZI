/* Read-only account preview for the existing full book interface.
 * Does not overwrite localStorage or post book data to the server.
 */
(() => {
  'use strict';
  const ready = () => {
    const panel = document.createElement('section');
    panel.id = 'account-preview';
    panel.setAttribute('aria-label', 'Hesap ve sunucu kontrolü');
    panel.style.cssText = 'margin:14px auto;padding:14px;max-width:900px;border:1px solid #7588db;border-radius:14px;background:#17285b;color:white;font:14px system-ui';
    const heading = document.createElement('strong');
    heading.textContent = 'Hesap ve cihaz senkronizasyonu';
    const status = document.createElement('p');
    status.textContent = 'Sunucu hesabı kontrol ediliyor…';
    const form = document.createElement('form');
    form.style.cssText = 'display:flex;flex-wrap:wrap;gap:8px';
    const username = document.createElement('input');
    username.placeholder = 'Kullanıcı adı';
    username.autocomplete = 'username';
    username.required = true;
    username.style.cssText = 'flex:1;min-width:120px';
    const password = document.createElement('input');
    password.type = 'password';
    password.placeholder = 'Şifre';
    password.autocomplete = 'current-password';
    password.required = true;
    password.style.cssText = 'flex:1;min-width:120px';
    const button = document.createElement('button');
    button.type = 'submit';
    button.textContent = 'Hesaba bağlan';
    form.append(username, password, button);
    const details = document.createElement('details');
    details.style.cssText = 'margin-top:10px';
    const summary = document.createElement('summary');
    summary.textContent = 'Sunucudaki kitap ve okuma kayıtlarını göster';
    const records = document.createElement('div');
    records.style.cssText = 'max-height:320px;overflow:auto;padding:8px 0;line-height:1.6';
    details.append(summary, records);
    const accountActions = document.createElement('div');
    accountActions.style.cssText = 'display:none;align-items:center;gap:10px;flex-wrap:wrap;margin:10px 0';
    const accountLabel = document.createElement('strong');
    const logoutButton = document.createElement('button');
    logoutButton.type = 'button';
    logoutButton.textContent = 'Çıkış yap / Hesap değiştir';
    logoutButton.style.cssText = 'padding:9px 14px;border:0;border-radius:8px;cursor:pointer;background:#a5d8ff;color:#142650';
    accountActions.append(accountLabel, logoutButton);
    panel.append(heading, status, form, accountActions, details);
    details.hidden = true;
    const main = document.querySelector('main') || document.body;
    main.insertBefore(panel, main.firstChild);

    async function json(path, options) {
      const response = await fetch(path, { credentials: 'same-origin', cache: 'no-store', ...options });
      const data = await response.json();
      if (!response.ok) throw Error(data.error || 'HTTP ' + response.status);
      return data;
    }
    async function inspect() {
      const user = await json('/me');
      const [books, reads, ratings] = await Promise.all([
        json('/my/sync'), json('/my/reading'), json('/my/ratings')
      ]);
      accountLabel.textContent = 'Hesap #' + user.user_id + ' · ' +
        (user.role === 'admin' ? 'Yönetici' : 'Okuyucu');
      accountActions.style.display = 'flex';
      status.textContent = 'Hesap #' + user.user_id + ': sunucuda ' +
        books.books.length + ' kitap, ' + reads.reading.length + ' okuma kaydı, ' +
        ratings.ratings.length + ' puan. Yerel kitaplık değiştirilmedi. Otomatik senkronizasyon henüz etkin değil.';
      // Show server records separately. Never write to localStorage here:
      // server shelf entries contain progress state, not full book summaries.
      records.replaceChildren();
      const section = (title, items, format) => {
        const h = document.createElement('strong');
        h.textContent = title + ' (' + items.length + ')';
        h.style.cssText = 'display:block;margin-top:12px';
        records.append(h);
        if (!items.length) {
          const empty = document.createElement('p');
          empty.textContent = 'Kayıt bulunamadı';
          records.append(empty);
          return;
        }
        const list = document.createElement('ol');
        list.style.cssText = 'padding-left:22px;margin:5px 0';
        for (const item of items) {
          const li = document.createElement('li');
          li.textContent = format(item);
          list.append(li);
        }
        records.append(list);
      };
      const catalog = Array.isArray(window.KITAP_CATALOG) ? window.KITAP_CATALOG : [];
      const bookTitle = bookId => {
        const id = String(bookId || '');
        const isbn = id.match(/^catalog-(97[89][0-9]{10})$/);
        if (isbn) {
          const match = catalog.find(book => String(book.isbn || '').replace(/[^0-9]/g, '') === isbn[1]);
          if (match) return match.name + ' (' + id + ')';
        }
        if (id.startsWith('catalog-')) {
          try {
            const decoded = decodeURIComponent(id.slice(8).replace(/%20/g, ' '));
            if (decoded && decoded !== id.slice(8)) return decoded;
          } catch (_) {}
        }
        return id;
      };
      section('Kitaplık kayıtları', books.books, item =>
        bookTitle(item.book_id) + ' · revizyon ' + String(item.revision) +
        (item.state && item.state.done ? ' · tamamlandı' : ''));
      section('Okuma geçmişi', reads.reading, item =>
        bookTitle(item.book_id) + ' · ' + String(item.completed_at));
      section('Kitap puanları', ratings.ratings, item =>
        bookTitle(item.book_id) + ' · ' + String(item.score) + '/10');
      details.hidden = false;
      form.hidden = true;
      form.style.display = 'none';
    }
    logoutButton.addEventListener('click', async () => {
      logoutButton.disabled = true;
      try {
        const csrf = await json('/csrf');
        await json('/logout', {
          method: 'POST',
          headers: { 'X-CSRF-Token': csrf.csrf_token }
        });
        // Do not delete any local books. They are browser-wide until full
        // per-user storage isolation is implemented.
        accountActions.style.display = 'none';
        details.hidden = true;
        details.open = false;
        records.replaceChildren();
        username.value = '';
        password.value = '';
        form.hidden = false;
        form.style.display = 'flex';
        status.textContent = 'Çıkış yapıldı. Başka hesapla giriş yapabilirsiniz. ' +
          'Dikkat: Bu tarayıcıdaki yerel kitaplar henüz kullanıcıya özel ayrılmıyor.';
      } catch (error) {
        status.textContent = 'Çıkış yapılamadı: ' + error.message;
      } finally {
        logoutButton.disabled = false;
      }
    });
    form.addEventListener('submit', async event => {
      event.preventDefault();
      button.disabled = true;
      try {
        // If already signed in, do not submit credentials again.
        // The server requires a session-bound CSRF token for every authenticated POST.
        let signedIn = false;
        try {
          await json('/me');
          signedIn = true;
        } catch (_) {}
        if (!signedIn) {
          await json('/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: username.value, password: password.value })
          });
        }
        password.value = '';
        await inspect();
      } catch (error) {
        status.textContent = 'Bağlantı kurulamadı: ' + error.message;
      } finally {
        button.disabled = false;
      }
    });
    inspect().catch(() => {
      accountActions.style.display = 'none';
      form.hidden = false;
      form.style.display = 'flex';
      status.textContent = 'Sunucu hesabına bağlanarak kayıt sayılarını karşılaştırabilirsiniz. Yerel kitaplar korunur.';
    });
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', ready, { once: true });
  else ready();
})();
