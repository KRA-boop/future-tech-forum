(() => {
  document.querySelectorAll('[data-language]').forEach(link => {
    link.addEventListener('click', () => {
      try { localStorage.setItem('yurally-language', link.dataset.language); } catch (_) {}
      if (location.hash) link.hash = location.hash;
    });
  });
})();

// Keep all lesson videos together after the written lesson and self-check.
(() => {
  const lesson = document.querySelector('main[data-course] .lesson-body');
  if (!lesson) return;
  const groups = [];
  for (const video of lesson.querySelectorAll('figure.course-video, figure.wp-block-embed-youtube')) {
    if (!lesson.contains(video)) continue;
    const guide = video.closest('.yurally-video-guide');
    if (guide) { if (!groups.includes(guide)) groups.push(guide); continue; }
    let start = video;
    while (start.previousElementSibling && !/^H[1-6]$/.test(start.tagName)) start = start.previousElementSibling;
    if (!/^H[1-6]$/.test(start.tagName)) start = video;
    const section = document.createElement('section');
    section.className = 'wp-block-group yurally-video-guide';
    section.style.cssText = 'margin-top:20px;background:#082b38;border:1px solid #28505a;color:#F3FAFB';
    let node = start;
    while (node) {
      const next = node.nextElementSibling;
      if (node !== start && (/^H[1-6]$/.test(node.tagName) || node.matches('details,.wp-block-buttons'))) break;
      section.append(node);
      node = next;
    }
    groups.push(section);
  }
  for (const group of groups) lesson.append(group);
})();

// Localized YuRally wordmark on the standalone lesson pages.
(() => {
  const main = document.querySelector('main[data-course][data-language]');
  if (!main || main.querySelector('.yurally-course-brand')) return;
  const names = {zh:'羽你同行 YuRally', en:'Rally Together YuRally', ja:'羽根とともに YuRally', ko:'배드민턴과 함께 YuRally'};
  const language = main.dataset.language;
  const brand = document.createElement('a');
  brand.className = 'yurally-course-brand';
  brand.href = 'https://yurally.wordpress.com/' + (language === 'zh' ? '' : language + '/');
  brand.textContent = names[language] || names.zh;
  brand.style.cssText = 'display:inline-block;color:#8de2d4;font-size:24px;font-weight:650;line-height:1.3;text-decoration:none';
  main.prepend(brand);
})();
