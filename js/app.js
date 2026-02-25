const STEPS = [
  { icon: '📚', label: '核心命题', key: 'coreProposition' },
  { icon: '🦴', label: '概念拓扑', key: 'topology' },
  { icon: '🧠', label: '认知同化', key: 'assimilation' },
  { icon: '⚔️', label: '破坏重塑', key: 'destruction' },
  { icon: '🔨', label: '事上磨练', key: 'practice' },
  { icon: '🌱', label: '跨界生发', key: 'crossDomain' },
];

const state = {
  view: 'home',
  bookId: null,
  activeStep: 0,
  observer: null,
  searchQuery: '',
  gardenScene: null,
};

/* ========== INIT ========== */

function init() {
  renderHome();
  bindEvents();
  initSearch();
  updateBookCount();

  if (typeof GardenScene !== 'undefined') {
    state.gardenScene = new GardenScene();
  }

  animateHomeEntrance();
}

function bindEvents() {
  document.getElementById('back-btn').addEventListener('click', goHome);

  document.addEventListener('keydown', (e) => {
    if (e.key === '/' && state.view === 'home' && document.activeElement.tagName !== 'INPUT') {
      e.preventDefault();
      document.getElementById('search-input').focus();
    }
    if (e.key === 'Escape') {
      if (state.view === 'home') {
        const input = document.getElementById('search-input');
        if (document.activeElement === input) {
          if (input.value) {
            clearSearch();
          } else {
            input.blur();
          }
        }
      } else {
        goHome();
      }
    }
  });
}

/* ========== SEARCH ========== */

function initSearch() {
  const input = document.getElementById('search-input');
  const clearBtn = document.getElementById('search-clear');

  input.addEventListener('input', (e) => {
    state.searchQuery = e.target.value;
    clearBtn.classList.toggle('hidden', !e.target.value);
    handleSearch(e.target.value);
  });

  clearBtn.addEventListener('click', clearSearch);
}

function clearSearch() {
  const input = document.getElementById('search-input');
  input.value = '';
  state.searchQuery = '';
  document.getElementById('search-clear').classList.add('hidden');
  handleSearch('');
  input.focus();
}

function handleSearch(query) {
  const books = window.BOOKS || [];
  const q = query.trim().toLowerCase();

  const filtered = q
    ? books.filter(b =>
        b.title.toLowerCase().includes(q) ||
        b.originalTitle.toLowerCase().includes(q) ||
        b.author.toLowerCase().includes(q) ||
        b.authorEn.toLowerCase().includes(q)
      )
    : books;

  renderHome(filtered);
  updateBookCount(filtered.length, books.length, !!q);

  const noResults = document.getElementById('no-results');
  const footer = document.querySelector('.site-footer');
  const grid = document.getElementById('book-grid');

  if (filtered.length === 0 && q) {
    noResults.classList.remove('hidden');
    footer.classList.add('hidden');
    grid.classList.add('hidden');
  } else {
    noResults.classList.add('hidden');
    footer.classList.remove('hidden');
    grid.classList.remove('hidden');
  }

  if (typeof gsap !== 'undefined' && filtered.length > 0) {
    gsap.fromTo('.book-card',
      { opacity: 0, y: 24 },
      { opacity: 1, y: 0, duration: 0.35, stagger: 0.04, ease: 'power2.out' }
    );
  }
}

function updateBookCount(shown, total, isFiltered) {
  const el = document.getElementById('book-count');
  const books = window.BOOKS || [];
  if (!isFiltered) {
    el.textContent = `共 ${total || books.length} 本书`;
  } else {
    el.textContent = `找到 ${shown} / ${total} 本`;
  }
}

/* ========== GSAP ANIMATIONS ========== */

function animateHomeEntrance() {
  if (typeof gsap === 'undefined') return;

  const cards = document.querySelectorAll('.book-card');

  const tl = gsap.timeline({
    onComplete: () => {
      cards.forEach(c => { c.style.opacity = ''; c.style.transform = ''; });
    }
  });
  tl.fromTo('.site-tag',
      { opacity: 0, y: -10 },
      { opacity: 1, y: 0, duration: 0.6, ease: 'power2.out' })
    .fromTo('.site-title',
      { opacity: 0, y: 20 },
      { opacity: 1, y: 0, duration: 0.8, ease: 'power2.out' }, '-=0.3')
    .fromTo('.site-subtitle',
      { opacity: 0 },
      { opacity: 1, duration: 0.6, ease: 'power2.out' }, '-=0.4')
    .fromTo('.search-container',
      { opacity: 0, y: 10 },
      { opacity: 1, y: 0, duration: 0.5, ease: 'power2.out' }, '-=0.3')
    .fromTo('.book-card',
      { opacity: 0, y: 40 },
      { opacity: 1, y: 0, duration: 0.5, stagger: 0.07, ease: 'power2.out' }, '-=0.2')
    .fromTo('.site-footer',
      { opacity: 0 },
      { opacity: 1, duration: 0.4, ease: 'power2.out' }, '-=0.2');

  setTimeout(() => {
    cards.forEach(c => {
      if (parseFloat(getComputedStyle(c).opacity) < 0.5) {
        c.style.opacity = '1';
        c.style.transform = '';
      }
    });
  }, 3000);
}

function transitionToBook(callback) {
  if (typeof gsap === 'undefined') {
    callback();
    return;
  }

  const overlay = document.getElementById('page-transition');
  overlay.classList.add('active');

  gsap.fromTo(overlay,
    { opacity: 0 },
    {
      opacity: 1,
      duration: 0.35,
      ease: 'power2.in',
      onComplete: () => {
        callback();
        gsap.to(overlay, {
          opacity: 0,
          duration: 0.4,
          delay: 0.05,
          ease: 'power2.out',
          onComplete: () => overlay.classList.remove('active'),
        });
      },
    }
  );
}

function transitionToHome(callback) {
  if (typeof gsap === 'undefined') {
    callback();
    return;
  }

  const overlay = document.getElementById('page-transition');
  overlay.classList.add('active');

  gsap.fromTo(overlay,
    { opacity: 0 },
    {
      opacity: 1,
      duration: 0.3,
      ease: 'power2.in',
      onComplete: () => {
        callback();
        gsap.to(overlay, {
          opacity: 0,
          duration: 0.4,
          delay: 0.05,
          ease: 'power2.out',
          onComplete: () => {
            overlay.classList.remove('active');
            if (typeof gsap !== 'undefined') {
              gsap.fromTo('.book-card',
                { opacity: 0, y: 30 },
                { opacity: 1, y: 0, duration: 0.4, stagger: 0.05, ease: 'power2.out' }
              );
            }
          },
        });
      },
    }
  );
}

function setupScrollAnimations() {
  if (typeof gsap === 'undefined' || typeof ScrollTrigger === 'undefined') return;

  gsap.registerPlugin(ScrollTrigger);

  document.querySelectorAll('.step-section').forEach(section => {
    gsap.from(section, {
      scrollTrigger: {
        trigger: section,
        start: 'top 85%',
        once: true,
      },
      duration: 0.7,
      opacity: 0,
      y: 30,
      ease: 'power2.out',
    });
  });
}

/* ========== NAVIGATION ========== */

function goHome() {
  transitionToHome(() => {
    state.view = 'home';
    state.bookId = null;
    state.activeStep = 0;
    if (state.observer) {
      state.observer.disconnect();
      state.observer = null;
    }
    document.getElementById('home-view').classList.remove('hidden');
    document.getElementById('book-view').classList.add('hidden');
    window.scrollTo(0, 0);

    if (state.gardenScene) state.gardenScene.setDimmed(false);

    if (state.searchQuery) {
      handleSearch(state.searchQuery);
    }
  });
}

function openBook(bookId) {
  transitionToBook(() => {
    state.view = 'book';
    state.bookId = bookId;
    state.activeStep = 0;

    const book = getBook(bookId);
    if (!book) return;

    document.getElementById('home-view').classList.add('hidden');
    document.getElementById('book-view').classList.remove('hidden');
    document.getElementById('book-view').style.setProperty('--book-accent', book.accent);

    document.getElementById('book-title').textContent = book.title;
    document.getElementById('book-author').textContent = `${book.author} \u00B7 ${book.date}`;

    renderSidebar();
    renderAllSteps();
    window.scrollTo(0, 0);

    if (state.gardenScene) state.gardenScene.setDimmed(true);

    requestAnimationFrame(() => {
      setupScrollObserver();
      setupScrollAnimations();
    });
  });
}

function getBook(id) {
  return (window.BOOKS || []).find(b => b.id === id);
}

/* ========== RENDER HOME ========== */

function renderHome(filteredBooks) {
  const grid = document.getElementById('book-grid');
  const allBooks = window.BOOKS || [];
  const books = filteredBooks || allBooks;

  grid.innerHTML = books.map((book) => {
    const globalIdx = allBooks.indexOf(book);
    return `
    <div class="book-card" data-book-id="${book.id}" style="--card-accent: ${book.accent}">
      <span class="card-icon">${book.icon}</span>
      <h2 class="card-title"><span class="card-number">${String(globalIdx + 1).padStart(2, '0')}.</span> ${book.title}</h2>
      <p class="card-original-title">${book.originalTitle}</p>
      <p class="card-author">${book.author} (${book.authorEn})</p>
      <p class="card-question">${book.coreProposition.question}</p>
      <p class="card-date">内化于 ${book.date}</p>
    </div>
  `;
  }).join('');

  grid.querySelectorAll('.book-card').forEach(card => {
    card.addEventListener('click', () => openBook(card.dataset.bookId));
    card.addEventListener('mousemove', (e) => {
      const rect = card.getBoundingClientRect();
      card.style.setProperty('--mouse-x', ((e.clientX - rect.left) / rect.width * 100) + '%');
      card.style.setProperty('--mouse-y', ((e.clientY - rect.top) / rect.height * 100) + '%');
    });
  });
}

/* ========== SIDEBAR ========== */

function renderSidebar() {
  const sidebar = document.getElementById('journey-sidebar');
  sidebar.innerHTML = STEPS.map((s, i) => `
    <a class="sidebar-step${i === 0 ? ' active' : ''}" data-step="${i}" href="#step-${i}">
      <span class="sidebar-icon">${s.icon}</span>
      <span class="sidebar-label">${s.label}</span>
      <span class="sidebar-num">${i + 1}</span>
    </a>
  `).join('');

  sidebar.querySelectorAll('.sidebar-step').forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const idx = parseInt(link.dataset.step);
      const target = document.getElementById('step-' + idx);
      if (target) {
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });
}

function setActiveSidebar(stepIndex) {
  if (state.activeStep === stepIndex) return;
  state.activeStep = stepIndex;

  document.querySelectorAll('.sidebar-step').forEach((el, i) => {
    el.classList.toggle('active', i === stepIndex);
  });
}

/* ========== SCROLL OBSERVER ========== */

function setupScrollObserver() {
  if (state.observer) state.observer.disconnect();

  const sections = document.querySelectorAll('.step-section[id]');
  if (!sections.length) return;

  const headerHeight = 60;

  state.observer = new IntersectionObserver((entries) => {
    let topMost = null;
    let topMostTop = Infinity;

    sections.forEach(sec => {
      const rect = sec.getBoundingClientRect();
      const top = rect.top - headerHeight;
      if (top < 200 && rect.bottom > headerHeight + 100) {
        if (top < topMostTop || (top <= 0 && top > topMost?.top)) {
          topMost = { el: sec, top };
          topMostTop = Math.abs(top);
        }
      }
    });

    if (!topMost) {
      let closest = null;
      let closestDist = Infinity;
      sections.forEach(sec => {
        const rect = sec.getBoundingClientRect();
        const dist = Math.abs(rect.top - headerHeight);
        if (dist < closestDist) {
          closestDist = dist;
          closest = sec;
        }
      });
      topMost = closest ? { el: closest } : null;
    }

    if (topMost) {
      const idx = parseInt(topMost.el.id.replace('step-', ''));
      setActiveSidebar(idx);
    }
  }, {
    rootMargin: `-${headerHeight}px 0px -40% 0px`,
    threshold: [0, 0.1, 0.3, 0.5]
  });

  sections.forEach(sec => state.observer.observe(sec));

  window.addEventListener('scroll', handleScrollForSidebar, { passive: true });
}

function handleScrollForSidebar() {
  const sections = document.querySelectorAll('.step-section[id]');
  const headerHeight = 60;

  let current = 0;
  sections.forEach((sec, i) => {
    const rect = sec.getBoundingClientRect();
    if (rect.top <= headerHeight + 150) {
      current = i;
    }
  });

  setActiveSidebar(current);
}

/* ========== RENDER ALL STEPS ========== */

function renderAllSteps() {
  const book = getBook(state.bookId);
  if (!book) return;

  const content = document.getElementById('book-content');
  let html = '';

  STEPS.forEach((stepInfo, i) => {
    html += `<div class="step-section" id="step-${i}">`;
    html += `<p class="step-label">${stepInfo.icon} STEP ${i + 1}</p>`;

    switch (i) {
      case 0: html += renderCoreProposition(book); break;
      case 1: html += renderTopology(book); break;
      case 2: html += renderAssimilation(book); break;
      case 3: html += renderDestruction(book); break;
      case 4: html += renderPractice(book); break;
      case 5:
        html += renderCrossDomain(book);
        html += renderClosing(book);
        break;
    }

    html += `</div>`;

    if (i < STEPS.length - 1) {
      html += `<div class="step-divider">\u25C7</div>`;
    }
  });

  content.innerHTML = html;
  bindExpandables();
}

/* ========== STEP RENDERERS ========== */

function renderCoreProposition(book) {
  const cp = book.coreProposition;
  return `
    <h2 class="step-title">核心命题</h2>
    <div class="core-question">${cp.question}</div>
    <div class="meta-answer">${cp.metaAnswer}</div>
    <div class="core-summary">${cp.summary}</div>
  `;
}

function renderTopology(book) {
  return `
    <h2 class="step-title">概念拓扑</h2>
    <div class="topology-container">${book.topology}</div>
  `;
}

function renderAssimilation(book) {
  const a = book.assimilation;
  let html = `<h2 class="step-title">认知同化</h2>`;
  html += `<div class="assimilation-intro">${a.intro}</div>`;

  a.principles.forEach((p, i) => {
    html += `
      <div class="principle-card expandable">
        <div class="principle-header expand-trigger">
          <span class="principle-number">${i + 1}</span>
          <span class="principle-title">${p.title}</span>
          <span class="principle-toggle">\u25BC</span>
        </div>
        <div class="principle-body">${p.content}</div>
      </div>
    `;
  });

  if (a.coreInsight) {
    html += `<div class="insight-box"><p>${a.coreInsight}</p></div>`;
  }
  return html;
}

function renderDestruction(book) {
  const d = book.destruction;
  let html = `<h2 class="step-title">破坏与重塑</h2>`;

  d.beliefs.forEach(b => {
    html += `
      <div class="belief-card">
        <div class="belief-old">
          <p class="belief-old-label">旧有信念 \u2014 必须崩塌</p>
          <p class="belief-old-text">\u201C${b.old}\u201D</p>
        </div>
        <div class="belief-destruction">${b.destruction}</div>
      </div>
    `;
  });

  if (d.newModels && d.newModels.length > 0) {
    html += `<h3 style="font-family:var(--font-serif);font-size:1.1rem;letter-spacing:3px;margin:36px 0 16px;">必须重塑的思维模型</h3>`;
    d.newModels.forEach(m => {
      html += `
        <div class="new-model-card">
          <p class="model-label">${m.label}</p>
          <div class="model-transition">
            <span class="model-old">${m.oldModel}</span>
            <span class="model-arrow">\u2192</span>
            <span class="model-new">${m.newModel}</span>
          </div>
        </div>
      `;
    });
  }

  if (d.cost) {
    html += `<div class="cost-section"><h3>代价</h3>${d.cost}</div>`;
  }
  return html;
}

function renderPractice(book) {
  const p = book.practice;
  let html = `<h2 class="step-title">事上磨练</h2>`;

  p.scenarios.forEach(s => {
    html += `
      <div class="scenario-card expandable">
        <div class="scenario-header expand-trigger">
          <span class="scenario-icon">${s.icon || '\uD83C\uDFAF'}</span>
          <span class="scenario-title">${s.title}</span>
          <span class="scenario-toggle">\u25BC</span>
        </div>
        <div class="scenario-body">
          ${s.content}
          ${s.coreMethod ? `<div class="scenario-core"><p><strong>核心心法：</strong>${s.coreMethod}</p></div>` : ''}
        </div>
      </div>
    `;
  });

  if (p.toolkit) {
    html += `<div class="toolkit-section"><h3>通用工具包</h3>${p.toolkit}</div>`;
  }
  return html;
}

function renderCrossDomain(book) {
  const c = book.crossDomain;
  let html = `<h2 class="step-title">跨界生发</h2>`;

  c.connections.forEach(conn => {
    html += `
      <div class="cross-card expandable">
        <div class="cross-header expand-trigger">
          <span class="cross-icon">${conn.icon || '\uD83D\uDD17'}</span>
          <div class="cross-title-group">
            <p class="cross-field">${conn.field}</p>
            <p class="cross-title">${conn.title}</p>
          </div>
          <span class="cross-toggle">\u25BC</span>
        </div>
        <div class="cross-body">${conn.content}</div>
      </div>
    `;
  });

  if (c.ultimateInsight) {
    html += `<div class="ultimate-insight"><h3>终极洞察</h3>${c.ultimateInsight}</div>`;
  }
  return html;
}

function renderClosing(book) {
  if (!book.closing) return '';
  const cl = book.closing;
  let html = `<div class="closing-section">`;

  if (cl.quotes) {
    cl.quotes.forEach(q => {
      html += `<p class="closing-quote">\u201C${q.text}\u201D</p>`;
      html += `<p class="closing-author">\u2014 ${q.author}</p>`;
    });
  }

  if (cl.reflection) {
    html += `<div class="closing-reflection">${cl.reflection}</div>`;
  }

  html += `</div>`;
  return html;
}

function bindExpandables() {
  document.querySelectorAll('.expandable').forEach(card => {
    const trigger = card.querySelector('.expand-trigger');
    if (trigger) {
      trigger.addEventListener('click', () => card.classList.toggle('open'));
    }
  });
}

document.addEventListener('DOMContentLoaded', init);
