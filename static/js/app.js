(function () {
  const key = 'theme';
  const root = document.documentElement;
  const btn = document.getElementById('theme-toggle');

  function applyTheme(value) {
    root.setAttribute('data-theme', value);
    if (!btn) return;
    btn.setAttribute('aria-pressed', value === 'dark' ? 'true' : 'false');
  }

  // 讀取偏好
  const saved = localStorage.getItem(key);
  if (saved === 'dark' || saved === 'light') {
    applyTheme(saved);
  } else {
    applyTheme('auto'); // 跟隨系統
  }

  if (btn) {
    btn.addEventListener('click', () => {
      const current = root.getAttribute('data-theme') || 'auto';
      const next = current === 'dark' ? 'light' : (current === 'light' ? 'auto' : 'dark');
      localStorage.setItem(key, next);
      applyTheme(next);
    });
  }
})();
