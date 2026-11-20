(() => {
  document.querySelectorAll('[data-language]').forEach(link => {
    link.addEventListener('click', () => {
      try { localStorage.setItem('yurally-language', link.dataset.language); } catch (_) {}
      if (location.hash) link.hash = location.hash;
    });
  });
})();
