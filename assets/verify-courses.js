(() => {
  const button = document.getElementById('start');
  const progress = document.getElementById('progress');
  const result = document.getElementById('result');
  const list = document.getElementById('results');
  const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
  const frames = win => new Promise(resolve => win.requestAnimationFrame(() => win.requestAnimationFrame(resolve)));
  const assert = (condition, message) => { if (!condition) throw Error(message); };
  // Sample the browser's real animation clock so background timer throttling
  // cannot turn a correct 680 ms transition into a false failure.
  const sample = (element, time) => {
    for (const animation of element.getAnimations({ subtree: true })) {
      animation.pause();
      animation.currentTime = time;
    }
    element.getBoundingClientRect();
  };
  const settle = async element => {
    const animations = element.getAnimations({ subtree: true });
    const finished = animations.map(a => a.finished.catch(() => {}));
    for (const animation of animations) animation.finish();
    await Promise.all(finished);
    for (let i = 0; i < 100 && element.hasAttribute('data-animating'); i++) await delay(20);
  };
  const coursePath = href => { const url = new URL(href, location.href); return url.origin + url.pathname.replace(/\/$/, ''); };
  async function verify(item, frame, nativeCoursePaths) {
    await new Promise((resolve, reject) => {
      const timer = setTimeout(() => reject(Error('課程載入逾時')), 25000);
      frame.onload = () => { clearTimeout(timer); resolve(); };
      frame.src = item.url + '?verification=20261128-selfcheck-route-1';
    });
    const doc = frame.contentDocument;
    const win = frame.contentWindow;
    doc.body.getBoundingClientRect();
    assert(doc.querySelector('main')?.dataset.course === item.slug, '課程頁不符');
    assert(doc.querySelector('main')?.dataset.language === item.lang, '課程語言不符');
    const cards = doc.querySelectorAll('[data-self-check]');
    assert(cards.length === 1, '自我檢核數量不符');
    const card = cards[0];
    const summary = card.querySelector('summary');
    const answer = card.querySelector(':scope > .answer');
    assert(summary && answer && answer.textContent.trim(), '檢核結構或答案遺漏');
    assert(!summary.querySelector('a') && !summary.closest('a'), '題目包含跳頁連結');
    assert(summary.textContent.trim() === item.question.trim(), '題目與原課程不符');
    assert(card.dataset.disclosureReady === 'true', '未載入動畫');
    assert(!card.open, '初始自我檢核未收合');
    const legacy = [...doc.querySelectorAll('.lesson-body a[href]')].find(a => a.href.startsWith('https://yurally.wordpress.com/category/') || nativeCoursePaths.has(coursePath(a.href)));
    assert(!legacy, '課程連結仍指向無動畫 WordPress 原生路徑：' + (legacy?.href || ''));
    assert(doc.querySelector('#self-check').nextElementSibling === card, '檢核未位於課程原處');
    const switches = [...doc.querySelectorAll('.languages a')];
    assert(switches.length === 4 && switches.every(a => new URL(a.href).pathname.endsWith('/' + item.slug + '/')), '切換語言未對應同一課程');
    const startUrl = win.location.href;
    const closedHeight = card.getBoundingClientRect().height;
    summary.click();
    const animations = card.getAnimations({ subtree: true });
    assert(animations.length === 3, '缺少高度、揭幕或光圈動畫');
    const keyframes = animations.flatMap(a => a.effect.getKeyframes());
    assert(keyframes.some(k => k.clipPath && k.clipPath.includes('100%')), '缺少橫向揭幕');
    assert(keyframes.some(k => k.boxShadow && /255, 198, 75/.test(k.boxShadow)), '缺少金色光圈');
    assert(animations.every(a => a.effect.getTiming().duration === 680), '動畫速度不一致');
    sample(card, 170);
    const middleHeight = card.getBoundingClientRect().height;
    const middleOpacity = Number(win.getComputedStyle(answer).opacity);
    assert(middleHeight > closedHeight && middleOpacity > 0 && middleOpacity < 1, '展開不是平滑過渡');
    await settle(card);
    const openHeight = card.getBoundingClientRect().height;
    assert(card.open && openHeight > closedHeight, '未完成展開');
    summary.click();
    const closingAnimations = card.getAnimations({ subtree: true });
    const closingKeys = closingAnimations.flatMap(a => a.effect.getKeyframes());
    assert(closingAnimations.length === 3 && closingAnimations.every(a => a.effect.getTiming().duration === 680), '收合動畫數量或速度不一致');
    assert(closingKeys.some(k => k.clipPath && k.clipPath.includes('100%')), '收合缺少橫向揭幕');
    assert(closingKeys.some(k => k.boxShadow && /255, 198, 75/.test(k.boxShadow)), '收合缺少金色光圈');
    sample(card, 170);
    assert(card.getBoundingClientRect().height > closedHeight && card.getBoundingClientRect().height < openHeight, '收合不是平滑過渡');
    const closingOpacity = Number(win.getComputedStyle(answer).opacity);
    assert(closingOpacity > 0 && closingOpacity < 1, '收合缺少平滑淡出');
    await settle(card);
    assert(!card.open && Math.abs(card.getBoundingClientRect().height - closedHeight) < 2, '未完成收合');
    summary.click(); sample(card, 160); summary.click(); sample(card, 80); summary.click();
    await settle(card);
    assert(card.open && !card.hasAttribute('data-animating'), '快速反向操作後狀態錯誤');
    summary.click(); await settle(card);
    assert(!card.open && win.location.href === startUrl, '檢核操作發生跳頁');
    const menu = doc.querySelector('.course-menu');
    menu.querySelector('summary').click();
    assert(menu.getAnimations({ subtree: true }).length === 3, '分類下拉未使用相同動畫');
    await settle(menu);
    assert(menu.open && menu.querySelectorAll('.answer a').length === 6, '分類選單未完整展開');
    menu.querySelector('summary').click(); await settle(menu);
    assert(!menu.open, '分類選單未平滑收合');
    assert(doc.documentElement.scrollWidth <= win.innerWidth + 1, '頁面水平溢位');
    return { lang: item.lang, slug: item.slug, viewport: win.innerWidth, checks: 29 };
  }
  button.addEventListener('click', async () => {
    button.disabled = true;
    result.dataset.status = 'running';
    const rows = await fetch('./manifest.json?v=20261120-gold-1').then(r => r.json());
    const nativeCoursePaths = new Set(rows.map(row => coursePath(row.wordpress_url)));
    let next = 0, complete = 0, passed = 0;
    const failed = [];
    const outcomes = [];
    async function worker(workerId) {
      const frame = document.createElement('iframe');
      Object.assign(frame.style, { position: 'fixed', left: (20 + workerId % 2 * 330) + 'px', top: (300 + Math.floor(workerId / 2) * 250) + 'px', width: workerId % 2 ? '390px' : '1200px', height: '960px', border: '0', transform: 'scale(0.25)', transformOrigin: 'top left', pointerEvents: 'none' });
      frame.setAttribute('aria-hidden', 'true');
      frame.tabIndex = -1;
      document.body.append(frame);
      while (next < rows.length) {
        const item = rows[next++];
        let error;
        try { outcomes.push(await verify(item, frame, nativeCoursePaths)); passed++; }
        catch (e) { error = e.message; failed.push({ lang: item.lang, slug: item.slug, error }); }
        complete++;
        const li = document.createElement('li');
        li.dataset.ok = String(!error);
        li.textContent = `${error ? '失敗' : '通過'} · ${item.lang} · ${item.title}${error ? ' · ' + error : ''}`;
        list.append(li);
        progress.textContent = `${complete} / ${rows.length} · 通過 ${passed} · 失敗 ${failed.length}`;
      }
      frame.remove();
    }
    await Promise.all([0, 1, 2, 3].map(worker));
    result.dataset.status = failed.length ? 'failed' : 'passed';
    result.dataset.report = JSON.stringify({ total: rows.length, passed, failed, outcomes });
    result.textContent = failed.length ? `驗證未全部通過：${failed.length} 頁` : `${passed} / ${rows.length} 全部通過：四語課程模板、原位展開與收合、金色光圈、橫向揭幕、分類下拉及所有課程連結皆已驗證。`;
  });
})();
