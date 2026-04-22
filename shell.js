/* LA/DP site shell — shared nav, footer, tweaks wiring.
   Loaded after DOM. Populates placeholder elements and manages tweak state. */

(() => {
  // ── Shared bits ─────────────────────────────────
  const NAV = [
    ['Practice', 'practice.html'],
    ['Disciplines', 'disciplines.html'],
    ['Works', 'works.html'],
    ['Journal', 'journal.html'],
    ['Inquire', 'contact.html'],
  ];

  const currentPage = (() => {
    const p = location.pathname.split('/').pop().toLowerCase() || 'index.html';
    return p.replace('.html', '');
  })();

  // ── Nav ─────────────────────────────────────────
  const navHTML = `
    <nav class="nav" aria-label="Primary">
      <div class="nav-inner">
        <a class="nav-wm" href="index.html" aria-label="LA Development Partners home">
          LA<span class="dot">.</span>
        </a>
        <div class="nav-links">
          ${NAV.map(([t, h]) => {
            const slug = h.replace('.html','');
            const cur = (currentPage === slug || (currentPage === 'study' && slug === 'works')) ? ' aria-current="page"' : '';
            return `<a class="nav-link" href="${h}"${cur}>${t}</a>`;
          }).join('')}
        </div>
        <button class="nav-toggle" aria-label="Open menu">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><line x1="3" y1="7" x2="21" y2="7"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="17" x2="21" y2="17"/></svg>
        </button>
      </div>
    </nav>
  `;
  const navSlot = document.getElementById('nav-slot');
  if (navSlot) navSlot.outerHTML = navHTML;

  // Mobile nav overlay
  const overlay = document.createElement('div');
  overlay.className = 'nav-overlay';
  overlay.innerHTML = `
    <button class="nav-overlay-close" aria-label="Close menu">\u00d7</button>
    ${NAV.map(([t, h]) => {
      const slug = h.replace('.html','');
      const cur = (currentPage === slug || (currentPage === 'study' && slug === 'works')) ? ' aria-current="page"' : '';
      return `<a class="nav-overlay-link" href="${h}"${cur}>${t}</a>`;
    }).join('')}
    <div class="nav-overlay-meta">LA/DP — 001 · EST. MMXXV</div>
  `;
  document.body.appendChild(overlay);

  const navToggle = document.querySelector('.nav-toggle');
  const overlayClose = overlay.querySelector('.nav-overlay-close');
  if (navToggle) navToggle.addEventListener('click', () => overlay.classList.add('open'));
  if (overlayClose) overlayClose.addEventListener('click', () => overlay.classList.remove('open'));
  overlay.querySelectorAll('.nav-overlay-link').forEach(l => l.addEventListener('click', () => overlay.classList.remove('open')));
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') overlay.classList.remove('open'); });

  // ── Footer ──────────────────────────────────────
  const footerHTML = `
    <footer class="footer">
      <div class="container">
        <div class="footer-grid">
          <div>
            <div class="footer-head">A practice in<br/><i>building well.</i></div>
            <div class="meta" style="margin-top:28px;">LA/DP — 001 · EST. MMXXV</div>
          </div>
          <div>
            <div class="footer-col-title">The Practice</div>
            <a class="footer-link" href="practice.html">About</a>
            <a class="footer-link" href="disciplines.html">Disciplines</a>
            <a class="footer-link" href="works.html">Works</a>
            <a class="footer-link" href="journal.html">Journal</a>
          </div>
          <div>
            <div class="footer-col-title">Office</div>
            <div class="footer-link">520 Broadway, 2nd Floor</div>
            <div class="footer-link">Santa Monica, CA 90401</div>
            <a class="footer-link" href="mailto:hello@ladevpartners.com">hello@ladevpartners.com</a>
            <div class="footer-link">+1 213 555 0114</div>
          </div>
          <div>
            <div class="footer-col-title">Elsewhere</div>
            <a class="footer-link" href="#">Instagram</a>
            <a class="footer-link" href="#">LinkedIn</a>
            <a class="footer-link" href="#">Press</a>
            <a class="footer-link" href="contact.html">Apprenticeship</a>
          </div>
        </div>
        <div class="footer-bottom">
          <div>© MMXXVI · LA Development Partners</div>
          <div>Los Angeles · 34.04° N · 118.24° W</div>
          <div>v.01 — Considered, always.</div>
        </div>
      </div>
    </footer>
  `;
  const footerSlot = document.getElementById('footer-slot');
  if (footerSlot) footerSlot.outerHTML = footerHTML;

  // ── Placeholder helper ──────────────────────────
  document.querySelectorAll('[data-placeholder]').forEach(el => {
    if (!el.querySelector('.placeholder-label')) {
      const label = document.createElement('div');
      label.className = 'placeholder-label';
      label.textContent = el.dataset.placeholder;
      el.classList.add('placeholder');
      el.appendChild(label);
    }
  });

  // ── Reveal on scroll ────────────────────────────
  const io = new IntersectionObserver((entries) => {
    entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } });
  }, { threshold: 0.08 });
  document.querySelectorAll('.reveal').forEach(el => io.observe(el));

  // ── Tweaks ──────────────────────────────────────
  const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
    "theme": "light",
    "accent": "rust",
    "homeLayout": "A",
    "type": "sans",
    "worksView": "cards"
  }/*EDITMODE-END*/;

  // Load from session so cross-page nav keeps state
  let tweaks = { ...TWEAK_DEFAULTS };
  try {
    const saved = JSON.parse(sessionStorage.getItem('ladp-tweaks') || '{}');
    tweaks = { ...tweaks, ...saved };
  } catch (e) {}

  const applyTweaks = () => {
    document.documentElement.setAttribute('data-theme', tweaks.theme);
    document.documentElement.setAttribute('data-accent', tweaks.accent);
    document.documentElement.setAttribute('data-type', tweaks.type);
    document.documentElement.setAttribute('data-home-layout', tweaks.homeLayout);
    document.documentElement.setAttribute('data-works-view', tweaks.worksView);
    sessionStorage.setItem('ladp-tweaks', JSON.stringify(tweaks));
  };
  applyTweaks();

  // Build tweaks panel
  const panel = document.createElement('div');
  panel.id = 'tweaks-panel';
  const showHomeLayout = currentPage === 'index';
  const showWorksView = currentPage === 'works';
  panel.innerHTML = `
    <div class="tweaks-head">
      <div class="tweaks-title">Tweaks</div>
      <button class="tweaks-close" aria-label="Close">×</button>
    </div>
    <div class="tweaks-body">
      <div class="tweak-row">
        <div class="tweak-label">Theme</div>
        <div class="tweak-choices" data-tweak="theme">
          <button class="tweak-btn" data-value="light">Bone</button>
          <button class="tweak-btn" data-value="dark">Ink</button>
        </div>
      </div>
      <div class="tweak-row">
        <div class="tweak-label">Accent</div>
        <div class="tweak-choices" data-tweak="accent">
          <button class="tweak-swatch" data-value="rust"   style="background:#c2572b"></button>
          <button class="tweak-swatch" data-value="clay"   style="background:#c89a70"></button>
          <button class="tweak-swatch" data-value="forest" style="background:#3f5a3a"></button>
        </div>
      </div>
      <div class="tweak-row">
        <div class="tweak-label">Type Pairing</div>
        <div class="tweak-choices" data-tweak="type">
          <button class="tweak-btn" data-value="sans">Sans</button>
          <button class="tweak-btn" data-value="serif">Serif</button>
          <button class="tweak-btn" data-value="grotesque">Grotesque</button>
        </div>
      </div>
      ${showHomeLayout ? `
      <div class="tweak-row">
        <div class="tweak-label">Home Hero Layout</div>
        <div class="tweak-choices" data-tweak="homeLayout">
          <button class="tweak-btn" data-value="A">A · Editorial</button>
          <button class="tweak-btn" data-value="B">B · Monumental</button>
          <button class="tweak-btn" data-value="C">C · Index</button>
        </div>
      </div>` : ''}
      ${showWorksView ? `
      <div class="tweak-row">
        <div class="tweak-label">Works View</div>
        <div class="tweak-choices" data-tweak="worksView">
          <button class="tweak-btn" data-value="editorial">Editorial Index</button>
          <button class="tweak-btn" data-value="large">Large Type</button>
          <button class="tweak-btn" data-value="cards">Cards</button>
        </div>
      </div>` : ''}
    </div>
  `;
  document.body.appendChild(panel);

  const syncActive = () => {
    panel.querySelectorAll('.tweak-choices').forEach(g => {
      const key = g.dataset.tweak;
      g.querySelectorAll('[data-value]').forEach(b => {
        b.classList.toggle('active', b.dataset.value === tweaks[key]);
      });
    });
  };
  syncActive();

  panel.addEventListener('click', (e) => {
    const b = e.target.closest('[data-value]');
    if (b) {
      const g = b.closest('[data-tweak]');
      const key = g.dataset.tweak;
      tweaks[key] = b.dataset.value;
      applyTweaks();
      syncActive();
      window.parent.postMessage({ type: '__edit_mode_set_keys', edits: { [key]: b.dataset.value } }, '*');
    }
    if (e.target.classList.contains('tweaks-close')) {
      panel.classList.remove('open');
      window.parent.postMessage({ type: '__edit_mode_deactivated_by_page' }, '*');
    }
  });

  window.addEventListener('message', (e) => {
    if (!e.data || typeof e.data !== 'object') return;
    if (e.data.type === '__activate_edit_mode') panel.classList.add('open');
    if (e.data.type === '__deactivate_edit_mode') panel.classList.remove('open');
  });
  window.parent.postMessage({ type: '__edit_mode_available' }, '*');
})();
