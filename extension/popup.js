/**
 * @file popup.js
 * @description Logic điều khiển giao diện Popup của Chrome Extension Muse2API.
 *
 * Mục đích:
 *   Trích xuất trạng thái đăng nhập (Cookies) của muse.ai trong trình duyệt hiện tại
 *   và gửi HTTP POST đồng bộ sang máy chủ backend muse2api.
 *
 * Điểm mấu chốt:
 *   Sử dụng chrome.cookies API thay vì document.cookie vì các cookie phiên cốt lõi
 *   (hatch_sess, hatch_vml) mang cờ httpOnly. Chỉ có extension permissions mới đọc được.
 */

const $ = (id) => document.getElementById(id);
const STORE = 'muse2api_ext_cfg';

const ESSENTIAL = ['hatch_sess', 'hatch_vml'];

/* ================= Ngôn ngữ giao diện / UI language =================
 * Tiếng Việt ('vi') là ngôn ngữ mặc định; hỗ trợ chuyển đổi sang Tiếng Anh ('en') và Tiếng Trung ('zh'). */
const LANG_STORE = 'muse2api_lang';
const LANG = (() => {
  try {
    const v = localStorage.getItem(LANG_STORE);
    if (v === 'vi' || v === 'en' || v === 'zh') return v;
  } catch (e) {}
  return 'vi';
})();

/**
 * Thiết lập ngôn ngữ giao diện và nạp lại popup.
 * @param {string} v - Mã ngôn ngữ ('vi', 'en' hoặc 'zh').
 */
function setLang(v) {
  try { localStorage.setItem(LANG_STORE, v); } catch (e) {}
  location.reload();
}

const I18N_MAP = {
  en: {
    'Muse2API Nhập Cookie': 'Muse2API Cookie Import',
    'Đồng bộ phiên đăng nhập muse.ai trong trình duyệt này sang dịch vụ muse2api chỉ với 1 cú nhấp chuột.':
      'Sync the muse.ai login session from this browser to your muse2api service in one click.',
    'Địa chỉ dịch vụ (BASE URL)': 'Service URL (BASE URL)',
    'Nhãn tài khoản (có thể để trống)': 'Account label (optional)',
    'Ví dụ: muse-main': 'e.g. muse-main',
    'Đọc và nhập tài khoản': 'Read and import',
    'Vui lòng điền Địa chỉ dịch vụ trước': 'Please enter the service URL first',
    'Vui lòng điền API Key trước': 'Please enter the API Key first',
    'Đang đọc Cookie của muse.ai…': 'Reading muse.ai cookies…',
    'Không tìm thấy Cookie nào của muse.ai.\nVui lòng mở và đăng nhập https://muse.ai/ trên trình duyệt này trước, sau đó quay lại bấm lần nữa.':
      'No muse.ai cookies found.\nOpen and log in to https://muse.ai/ in this browser first, then click again.',
    'Đọc được {n} Cookie nhưng thiếu mục cốt lõi: {missing}\nTrình duyệt này chưa đăng nhập thành công. Hãy đăng nhập đến khi thấy giao diện trò chuyện rồi thử lại.':
      'Read {n} cookies, but missing core items: {missing}\nThis browser has not logged in successfully yet. Log in until you can see the chat interface, then try again.',
    'Đọc được {n} Cookie, đang tải lên {base} …': 'Read {n} cookies, uploading to {base} …',
    'API Key không đúng (dịch vụ trả về 401).\nVui lòng vào đầu tab "Hồ chứa tài khoản" trên trang quản trị để sao chép đúng API Key.':
      'Invalid API Key (the service returned 401).\nCopy the correct API Key from the top of the "Account Pool" tab on the admin page.',
    'Nhập thất bại: HTTP {status}\n{body}': 'Import failed: HTTP {status}\n{body}',
    '(tự động)': '(auto)',
    'không rõ': 'unknown',
    '✓ Nhập thành công\nNhãn tài khoản: {label}\nID tài khoản: {id}\nSố lượng Cookie: {count}\nCó hiệu lực đến: {expires}\n':
      '✓ Imported successfully\nAccount label: {label}\nAccount ID: {id}\nCookie count: {count}\nValid until: {expires}\n',
    '\nLưu ý: {warning}': '\nNote: {warning}',
    'Đã xảy ra lỗi: {msg}\n\nNguyên nhân thường gặp:\n· Điền sai địa chỉ dịch vụ hoặc dịch vụ chưa khởi động\n· Địa chỉ không phải https (hoặc chứng chỉ chưa được tin cậy)\n· Trình duyệt chặn yêu cầu khác nguồn gốc (CORS)':
      'Something went wrong: {msg}\n\nCommon causes:\n· The service URL is wrong or the service is not running\n· The URL is not https (or the certificate is not trusted)\n· The browser blocked the cross-origin request',
    'Không phân tích được bất kỳ cookie nào, vui lòng kiểm tra định dạng': 'No cookies could be parsed; please check the format',
    'Thiếu Authorization: Bearer <key>': 'Missing Authorization: Bearer <key>',
    'API key không hợp lệ': 'Invalid API key',
  },
  zh: {
    'Muse2API Nhập Cookie': 'Muse2API Cookie 导入',
    'Đồng bộ phiên đăng nhập muse.ai trong trình duyệt này sang dịch vụ muse2api chỉ với 1 cú nhấp chuột.':
      '把当前浏览器里 muse.ai 的登录态，一键同步到你的 muse2api 服务。',
    'Địa chỉ dịch vụ (BASE URL)': '服务地址（BASE URL）',
    'Nhãn tài khoản (có thể để trống)': '账号标签（可留空）',
    'Ví dụ: muse-main': '例如 muse-main',
    'Đọc và nhập tài khoản': '读取并导入',
    'Vui lòng điền Địa chỉ dịch vụ trước': '请先填服务地址',
    'Vui lòng điền API Key trước': '请先填 API Key',
    'Đang đọc Cookie của muse.ai…': '正在读取 muse.ai 的 Cookie…',
    'Không tìm thấy Cookie nào của muse.ai.\nVui lòng mở và đăng nhập https://muse.ai/ trên trình duyệt này trước, sau đó quay lại bấm lần nữa.':
      '没读到 muse.ai 的 Cookie。\n请先在这个浏览器里打开并登录 https://muse.ai/ ，再回来点一次。',
    'Đọc được {n} Cookie nhưng thiếu mục cốt lõi: {missing}\nTrình duyệt này chưa đăng nhập thành công. Hãy đăng nhập đến khi thấy giao diện trò chuyện rồi thử lại.':
      '读到 {n} 条 Cookie，但缺核心项：{missing}\n说明这个浏览器还没登录成功。请登录到能看到聊天界面再试。',
    'Đọc được {n} Cookie, đang tải lên {base} …': '读到 {n} 条 Cookie，正在上传到 {base} …',
    'API Key không đúng (dịch vụ trả về 401).\nVui lòng vào đầu tab "Hồ chứa tài khoản" trên trang quản trị để sao chép đúng API Key.':
      'API Key 不对（服务返回 401）。\n请到管理页「账号池」页顶部复制正确的 API Key。',
    'Nhập thất bại: HTTP {status}\n{body}': '导入失败：HTTP {status}\n{body}',
    '(tự động)': '(自动)',
    'không rõ': '未知',
    '✓ Nhập thành công\nNhãn tài khoản: {label}\nID tài khoản: {id}\nSố lượng Cookie: {count}\nCó hiệu lực đến: {expires}\n':
      '✓ 导入成功\n账号标签：{label}\n账号 ID：{id}\nCookie 条数：{count}\n有效期到：{expires}\n',
    '\nLưu ý: {warning}': '\n注意：{warning}',
    'Đã xảy ra lỗi: {msg}\n\nNguyên nhân thường gặp:\n· Điền sai địa chỉ dịch vụ hoặc dịch vụ chưa khởi động\n· Địa chỉ không phải https (hoặc chứng chỉ chưa được tin cậy)\n· Trình duyệt chặn yêu cầu khác nguồn gốc (CORS)':
      '出错了：{msg}\n\n常见原因：\n· 服务地址填错或服务没启动\n· 这个地址不是 https（或证书不被信任）\n· 浏览器拦截了跨域请求',
    'Không phân tích được bất kỳ cookie nào, vui lòng kiểm tra định dạng': '未解析到任何 cookie，请检查格式',
    'Thiếu Authorization: Bearer <key>': '缺少 Authorization: Bearer <key>',
    'API key không hợp lệ': 'API key 无效',
  },
};

const I18N_HTML_MAP = {
  en: {
    steps: '<b>Before you start, check two things:</b><br>\n'
      + '    1. You are logged in to <a href="https://muse.ai/" target="_blank"\n'
      + '       style="color:#4f8cff">muse.ai</a> in <b>this browser</b> (you can see the chat interface).<br>\n'
      + '    2. The service URL and API Key above are filled in (you can copy them from the top of the "Account Pool" tab on the muse2api admin page).',
    foot: 'This extension does only one thing: it uses the browser\'s <code>chrome.cookies</code> API to read muse.ai\n'
      + '    cookies (including the httpOnly ones) and POSTs them to the service URL you entered.\n'
      + '    Nothing is collected or uploaded to any third-party server.',
  },
  zh: {
    steps: '<b>用之前先确认两件事：</b><br>\n'
      + '    1. 你已经在<b>这个浏览器</b>里登录了 <a href="https://muse.ai/" target="_blank"\n'
      + '       style="color:#4f8cff">muse.ai</a>（能看到聊天界面）。<br>\n'
      + '    2. 上面的服务地址和 API Key 已填好（在 muse2api 管理页「账号池」页顶部可以复制）。',
    foot: '本扩展只做一件事：用浏览器的 <code>chrome.cookies</code> 接口读取 muse.ai 的\n'
      + '    Cookie（能读到 httpOnly 的那些），POST 到你填的服务地址。\n'
      + '    不收集、不上传到任何第三方服务器。',
  },
};

const I18N_PATTERNS_MAP = {
  en: [
    [/^Thiếu cookie cốt lõi: (.*), tài khoản này có thể không tạo được nội dung$/s, 'Missing core cookies: $1; this account may not be able to generate'],
  ],
  zh: [
    [/^Thiếu cookie cốt lõi: (.*), tài khoản này có thể không tạo được nội dung$/s, '缺少核心 cookie：$1，该账号可能无法生成'],
  ],
};

/**
 * Hàm dịch chuỗi i18n hỗ trợ thay thế biến định dạng {varName}.
 * @param {string} s - Chuỗi nguồn cần dịch.
 * @param {Object} [vars] - Object chứa các cặp key-value thay thế.
 * @returns {string} Chuỗi sau khi được dịch và điền biến.
 */
function t(s, vars) {
  let out = s;
  const dict = I18N_MAP[LANG];
  const pats = I18N_PATTERNS_MAP[LANG] || [];
  if (dict && typeof s === 'string') {
    if (Object.prototype.hasOwnProperty.call(dict, s)) out = dict[s];
    else for (const [re, rep] of pats) if (re.test(s)) { out = s.replace(re, rep); break; }
  }
  if (vars) out = out.replace(/\{(\w+)\}/g, (m, k) => (k in vars ? String(vars[k]) : m));
  return out;
}

/**
 * Cập nhật ngôn ngữ cho các phần tử DOM trong popup.html.
 */
function applyLang() {
  $('langSel').value = LANG;
  if (LANG === 'vi') return;
  document.documentElement.lang = LANG === 'zh' ? 'zh-CN' : 'en';
  document.title = t(document.title);
  const htmlMap = I18N_HTML_MAP[LANG] || {};
  document.querySelectorAll('[data-i18n]').forEach((el) => {
    const html = htmlMap[el.dataset.i18n];
    if (html) el.innerHTML = html;
  });
  document.querySelectorAll('[data-i18n-text]').forEach((el) => {
    el.textContent = t(el.textContent.trim());
  });
  document.querySelectorAll('[placeholder]').forEach((el) => {
    el.placeholder = t(el.placeholder);
  });
}

/**
 * Hiển thị thông báo log trạng thái lên giao diện popup.
 * @param {string} html - Nội dung HTML hoặc chuỗi văn bản cần hiển thị.
 * @param {string} [cls] - Tên class CSS áp dụng ('ok', 'bad', 'warn').
 */
function log(html, cls) {
  const el = $('log');
  el.className = 'show';
  el.innerHTML = cls ? `<span class="${cls}">${html}</span>` : html;
}

/**
 * Chuẩn hóa URL máy chủ muse2api (loại bỏ dấu gạch chéo cuối và hậu tố /v1).
 * @param {string} v - URL đầu vào.
 * @returns {string} URL đã chuẩn hóa.
 */
function normBase(v) {
  let s = (v || '').trim();
  if (!s) return '';
  if (!/^https?:\/\//i.test(s)) s = 'https://' + s;
  s = s.replace(/\/+$/, '');
  s = s.replace(/\/v1$/i, '');
  return s;
}

/**
 * Nạp cấu hình đã lưu từ chrome.storage.local hoặc tự động phát hiện nếu tab hiện tại là trang Admin.
 */
async function loadCfg() {
  const o = await chrome.storage.local.get(STORE);
  const c = o[STORE] || {};
  if (c.base) $('base').value = c.base;
  if (c.key) $('key').value = c.key;
  if (c.label) $('label').value = c.label;
  if (!c.base) {
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      const u = tab && tab.url ? new URL(tab.url) : null;
      if (u && /\/admin/.test(u.pathname)) {
        $('base').value = u.origin;
        const k = new URLSearchParams(u.search).get('key');
        if (k) $('key').value = k;
      }
    } catch (e) { /* Bỏ qua lỗi */ }
  }
}

/**
 * Lưu cấu hình dịch vụ vào bộ nhớ chrome.storage.local.
 */
async function saveCfg() {
  await chrome.storage.local.set({
    [STORE]: {
      base: normBase($('base').value),
      key: $('key').value.trim(),
      label: $('label').value.trim(),
    },
  });
}

/**
 * Trích xuất toàn bộ cookies của domain muse.ai qua chrome.cookies API.
 * @returns {Promise<{cookies: Object.<string, string>, expires: Object.<string, number>}>}
 */
async function grabCookies() {
  const all = await chrome.cookies.getAll({ domain: 'muse.ai' });
  const out = {}, exp = {};
  for (const c of all) {
    const dom = (c.domain || '').replace(/^\./, '');
    if (!dom.endsWith('muse.ai')) continue;
    out[c.name] = c.value;
    if (c.expirationDate) exp[c.name] = Math.floor(c.expirationDate);
  }
  return { cookies: out, expires: exp };
}

/**
 * Xử lý sự kiện nhấn nút "Đọc và nhập tài khoản".
 */
async function run() {
  const base = normBase($('base').value);
  const key = $('key').value.trim();
  const label = $('label').value.trim();

  if (!base) return log(t('Vui lòng điền Địa chỉ dịch vụ trước'), 'bad');
  if (!key) return log(t('Vui lòng điền API Key trước'), 'bad');

  $('go').disabled = true;
  log(t('Đang đọc Cookie của muse.ai…'));

  try {
    const { cookies, expires } = await grabCookies();
    const names = Object.keys(cookies);
    if (!names.length) {
      return log(t('Không tìm thấy Cookie nào của muse.ai.\nVui lòng mở và đăng nhập '
                 + 'https://muse.ai/ trên trình duyệt này trước, sau đó quay lại bấm lần nữa.'), 'bad');
    }
    const missing = ESSENTIAL.filter((n) => !(n in cookies));
    if (missing.length) {
      log(t('Đọc được {n} Cookie nhưng thiếu mục cốt lõi: {missing}\n'
          + 'Trình duyệt này chưa đăng nhập thành công. Hãy đăng nhập đến khi thấy giao diện trò chuyện rồi thử lại.',
          { n: names.length, missing: missing.join(LANG === 'zh' ? '、' : ', ') }), 'warn');
      return;
    }

    log(t('Đọc được {n} Cookie, đang tải lên {base} …', { n: names.length, base }));

    const r = await fetch(base + '/admin/accounts', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + key,
      },
      body: JSON.stringify({ label, cookies, expires }),
    });

    const text = await r.text();
    let data;
    try { data = JSON.parse(text); } catch (e) { data = { raw: text }; }

    if (r.status === 401) {
      return log(t('API Key không đúng (dịch vụ trả về 401).\n'
                 + 'Vui lòng vào đầu tab "Hồ chứa tài khoản" trên trang quản trị để sao chép đúng API Key.'), 'bad');
    }
    if (!r.ok) {
      const body = typeof data.detail === 'string' ? t(data.detail) : text.slice(0, 300);
      return log(t('Nhập thất bại: HTTP {status}\n{body}', { status: r.status, body }), 'bad');
    }

    const a = (data.added && data.added[0]) || {};
    await saveCfg();
    log(t('✓ Nhập thành công\nNhãn tài khoản: {label}\nID tài khoản: {id}\nSố lượng Cookie: {count}\nCó hiệu lực đến: {expires}\n', {
          label: a.label || label || t('(tự động)'),
          id: a.id || '?',
          count: a.cookie_count || names.length,
          expires: a.expires_at ? new Date(a.expires_at * 1000).toLocaleString() : t('không rõ'),
        })
        + (data.warning ? t('\nLưu ý: {warning}', { warning: t(data.warning) }) : ''), 'ok');
  } catch (e) {
    log(t('Đã xảy ra lỗi: {msg}\n\nNguyên nhân thường gặp:\n'
        + '· Điền sai địa chỉ dịch vụ hoặc dịch vụ chưa khởi động\n'
        + '· Địa chỉ không phải https (hoặc chứng chỉ chưa được tin cậy)\n'
        + '· Trình duyệt chặn yêu cầu khác nguồn gốc (CORS)', { msg: e && e.message ? e.message : String(e) }), 'bad');
  } finally {
    $('go').disabled = false;
  }
}

// Khởi tạo giao diện
applyLang();
$('langSel').addEventListener('change', (e) => setLang(e.target.value));
$('go').addEventListener('click', run);
loadCfg();
