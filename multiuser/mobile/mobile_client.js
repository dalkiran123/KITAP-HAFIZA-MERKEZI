/* Same-origin prototype client. Never stores passwords or sessions in localStorage. */
(() => {
  'use strict';
  const el = id => document.getElementById(id);
  const status = (message, error = false) => {
    el('status').textContent = message;
    el('status').className = error ? 'error' : 'ok';
  };
  let revisions = new Map();
  let csrfToken = null;
  async function request(path, method = 'GET', body) {
    const options = { method, credentials: 'same-origin', headers: {} };
    if (body !== undefined) {
      if (csrfToken && path !== '/login' && path !== '/register') {
        options.headers['X-CSRF-Token'] = csrfToken;
      }
      options.headers['Content-Type'] = 'application/json';
      options.body = JSON.stringify(body);
    }
    const response = await fetch(path, options);
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Sunucu hatası (' + response.status + ')');
    return data;
  }
  async function refresh() {
    const data = await request('/my/sync');
    revisions = new Map(data.books.map(book => [book.book_id, book.revision]));
    const list = el('books');
    list.replaceChildren();
    if (!data.books.length) {
      const empty = document.createElement('p');
      empty.textContent = 'Henüz kitap kaydınız yok.';
      list.append(empty);
    }
    for (const book of data.books) {
      const card = document.createElement('article');
      const title = document.createElement('strong');
      title.textContent = book.book_id;
      const details = document.createElement('p');
      details.textContent = (book.state.done ? 'Okundu' : 'Okunmadı') +
        (book.state.notes ? ' · ' + book.state.notes : '');
      const edit = document.createElement('button');
      edit.type = 'button';
      edit.className = 'secondary';
      edit.textContent = 'Düzenle';
      edit.addEventListener('click', () => {
        el('book-id').value = book.book_id;
        el('notes').value = book.state.notes || '';
        el('done').checked = Boolean(book.state.done);
        el('book-id').focus();
      });
      card.append(title, details, edit);
      list.append(card);
    }
  }
  async function enter() {
    const user = await request('/me');
    csrfToken = (await request('/csrf')).csrf_token;
    el('identity').textContent = 'Hesap: ' + user.user_id;
    el('auth').hidden = true;
    el('shelf').hidden = false;
    await refresh();
    status('Kitaplığınız yüklendi.');
  }
  el('login-form').addEventListener('submit', async event => {
    event.preventDefault();
    try {
      await request('/login', 'POST', { username: el('username').value, password: el('password').value });
      el('password').value = '';
      await enter();
    } catch (error) { status(error.message, true); }
  });
  el('register').addEventListener('click', async () => {
    try {
      await request('/register', 'POST', { username: el('username').value, password: el('password').value });
      el('password').value = '';
      await enter();
    } catch (error) { status(error.message, true); }
  });
  el('refresh').addEventListener('click', async () => {
    try { await refresh(); status('Güncel kayıtlar alındı.'); }
    catch (error) { status(error.message, true); }
  });
  el('book-form').addEventListener('submit', async event => {
    event.preventDefault();
    const bookId = el('book-id').value.trim();
    if (!bookId) return;
    try {
      await request('/my/sync', 'POST', {
        book_id: bookId,
        expected_revision: revisions.get(bookId) || 0,
        state: { done: el('done').checked, notes: el('notes').value }
      });
      await refresh();
      status('Kitap kaydedildi.');
    } catch (error) {
      status('Kaydedilemedi: ' + error.message + '. Önce yenileyip değişiklikleri kontrol edin.', true);
    }
  });
  el('logout').addEventListener('click', async () => {
    try {
      await request('/logout', 'POST', {});
      revisions.clear();
      csrfToken = null;
      el('books').replaceChildren();
      el('auth').hidden = false;
      el('shelf').hidden = true;
      status('Çıkış yapıldı.');
    } catch (error) { status(error.message, true); }
  });
  request('/me').then(enter).catch(() => status('Giriş yaparak başlayabilirsiniz.'));
})();
