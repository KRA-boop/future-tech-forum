/* Shared by FAQ, course self-checks and course menus. */
(() => {
  'use strict';
  const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)');
  const timing = { duration: 680, easing: 'cubic-bezier(.35, 0, .25, 1)', fill: 'both' };
  function initDisclosures(root = document) {
    for (const card of root.querySelectorAll('main details')) {
      if (card.dataset.disclosureReady) continue;
      const summary = card.querySelector(':scope > summary');
      const answer = card.querySelector(':scope > .answer');
      if (!summary || !answer) continue;
      card.dataset.disclosureReady = 'true';
      let slide, fade, glow;
      let opening = card.open;
      const finish = () => {
        card.open = opening;
        slide?.cancel();
        fade?.cancel();
        slide = fade = undefined;
        delete card.dataset.animating;
      };
      summary.addEventListener('click', event => {
        if (!card.animate || reduceMotion.matches) return;
        event.preventDefault();
        const startHeight = card.getBoundingClientRect().height;
        const startOpacity = slide ? Number(getComputedStyle(answer).opacity) : Number(card.open);
        const shown = 'inset(0 0 0 0)';
        const hidden = 'inset(0 100% 0 0)';
        const startClip = slide ? getComputedStyle(answer).clipPath : (card.open ? shown : hidden);
        opening = slide ? !opening : !card.open;
        slide?.cancel();
        fade?.cancel();
        card.open = opening;
        const endHeight = card.getBoundingClientRect().height;
        card.open = true;
        card.dataset.animating = opening ? 'opening' : 'closing';
        slide = card.animate([{ height: startHeight + 'px' }, { height: endHeight + 'px' }], timing);
        fade = answer.animate([
          { opacity: startOpacity, clipPath: startClip },
          { opacity: Number(opening), clipPath: opening ? shown : hidden }
        ], timing);
        glow?.cancel();
        glow = card.animate([
          { boxShadow: '0 0 0 2px rgba(255, 198, 75, .85)' },
          { boxShadow: '0 0 0 6px rgba(255, 198, 75, 1)', offset: .35 },
          { boxShadow: '0 0 0 10px rgba(255, 198, 75, 0)' }
        ], { duration: timing.duration, easing: 'ease-out' });
        slide.onfinish = finish;
      });
      reduceMotion.addEventListener('change', () => {
        if (!reduceMotion.matches) return;
        if (slide) finish();
        glow?.cancel();
      });
      // Settle to natural height if a viewport change interrupts a disclosure.
      addEventListener('resize', () => { if (slide) finish(); }, { passive: true });
    }
  }
  window.YuRallyDisclosures = { init: initDisclosures, duration: timing.duration };
  initDisclosures();
})();
