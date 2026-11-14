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
    panel.append(heading, status, form);
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
      status.textContent = 'Hesap #' + user.user_id + ': sunucuda ' +
        books.books.length + ' kitap, ' + reads.reading.length + ' okuma kaydı, ' +
        ratings.ratings.length + ' puan. Yerel kitaplık değiştirilmedi. Otomatik senkronizasyon henüz etkin değil.';
      form.hidden = true;
    }
    form.addEventListener('submit', async event => {
      event.preventDefault();
      button.disabled = true;
      try {
        await json('/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username: username.value, password: password.value })
        });
        password.value = '';
        await inspect();
      } catch (error) {
        status.textContent = 'Bağlantı kurulamadı: ' + error.message;
      } finally {
        button.disabled = false;
      }
    });
    inspect().catch(() => {
      status.textContent = 'Sunucu hesabına bağlanarak kayıt sayılarını karşılaştırabilirsiniz. Yerel kitaplar korunur.';
    });
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', ready, { once: true });
  else ready();
})();
