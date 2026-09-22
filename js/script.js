// Crowsons Distribution — interactions

document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('year').textContent = new Date().getFullYear();

  /* ---------- Sticky nav shadow ---------- */
  const nav = document.getElementById('nav');
  const onScroll = () => {
    nav.classList.toggle('is-scrolled', window.scrollY > 12);
  };
  onScroll();
  window.addEventListener('scroll', onScroll, { passive: true });

  /* ---------- Magnetic buttons ---------- */
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (!prefersReducedMotion) {
    document.querySelectorAll('.btn-primary').forEach(btn => {
      btn.addEventListener('mousemove', (e) => {
        const rect = btn.getBoundingClientRect();
        const x = e.clientX - rect.left - rect.width / 2;
        const y = e.clientY - rect.top - rect.height / 2;
        btn.style.transition = 'transform 0.15s ease';
        btn.style.transform = `translate(${x * 0.22}px, ${y * 0.22 - 2}px)`;
      });
      btn.addEventListener('mouseleave', () => {
        btn.style.transition = 'transform 0.35s var(--ease)';
        btn.style.transform = 'translate(0, 0)';
      });
    });
  }

  /* ---------- Hero globe parallax ---------- */
  const heroGlobe = document.querySelector('.hero-globe');
  const heroSection = document.querySelector('.hero');
  if (heroGlobe && heroSection && !prefersReducedMotion) {
    window.addEventListener('scroll', () => {
      const rect = heroSection.getBoundingClientRect();
      if (rect.bottom < 0 || rect.top > window.innerHeight) return;
      heroGlobe.style.transform = `translateY(${rect.top * -0.12}px)`;
    }, { passive: true });
  }

  /* ---------- Tilt-on-hover cards ---------- */
  if (!prefersReducedMotion) {
    document.querySelectorAll('.service-card, .pillar, .feat-card').forEach(card => {
      card.addEventListener('mousemove', (e) => {
        const rect = card.getBoundingClientRect();
        const px = (e.clientX - rect.left) / rect.width - 0.5;
        const py = (e.clientY - rect.top) / rect.height - 0.5;
        card.style.transition = 'transform 0.1s ease';
        card.style.transform = `perspective(700px) rotateX(${py * -6}deg) rotateY(${px * 6}deg) translateY(-4px)`;
      });
      card.addEventListener('mouseleave', () => {
        card.style.transition = 'transform 0.4s var(--ease)';
        card.style.transform = '';
      });
    });
  }

  /* ---------- Mobile drawer ---------- */
  const navToggle = document.getElementById('navToggle');
  const drawer = document.getElementById('mobileDrawer');

  const closeDrawer = () => {
    drawer.classList.remove('is-open');
    navToggle.setAttribute('aria-expanded', 'false');
    document.body.classList.remove('no-scroll');
  };

  navToggle.addEventListener('click', () => {
    const isOpen = drawer.classList.toggle('is-open');
    navToggle.setAttribute('aria-expanded', String(isOpen));
    document.body.classList.toggle('no-scroll', isOpen);
  });

  drawer.querySelectorAll('a').forEach(a => a.addEventListener('click', closeDrawer));

  /* ---------- Active nav link on scroll ---------- */
  const sections = document.querySelectorAll('section[id]');
  const navLinks = document.querySelectorAll('.nav-links a');
  const navIndicator = document.getElementById('navIndicator');

  const moveIndicator = () => {
    const activeLink = document.querySelector('.nav-links a.active');
    if (!activeLink || !navIndicator) return;
    navIndicator.style.width = `${activeLink.offsetWidth}px`;
    navIndicator.style.transform = `translateX(${activeLink.offsetLeft - 6}px)`;
  };

  const sectionObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const id = entry.target.getAttribute('id');
        navLinks.forEach(link => {
          link.classList.toggle('active', link.getAttribute('href') === `#${id}`);
        });
        moveIndicator();
      }
    });
  }, { rootMargin: '-45% 0px -50% 0px' });

  sections.forEach(section => sectionObserver.observe(section));
  moveIndicator();
  window.addEventListener('resize', moveIndicator);
  navLinks.forEach(link => link.addEventListener('mouseenter', () => {
    navIndicator.style.width = `${link.offsetWidth}px`;
    navIndicator.style.transform = `translateX(${link.offsetLeft - 6}px)`;
  }));
  document.querySelector('.nav-links').addEventListener('mouseleave', moveIndicator);

  /* ---------- Scroll reveal ---------- */
  const revealEls = document.querySelectorAll('.reveal, .reveal-stagger');
  const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('is-visible');
        revealObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.15 });

  revealEls.forEach(el => revealObserver.observe(el));

  /* ---------- FAQ accordion ---------- */
  document.querySelectorAll('.faq-item').forEach(item => {
    const q = item.querySelector('.faq-q');
    const a = item.querySelector('.faq-a');

    q.addEventListener('click', () => {
      const isOpen = item.classList.contains('is-open');

      document.querySelectorAll('.faq-item.is-open').forEach(open => {
        if (open !== item) {
          open.classList.remove('is-open');
          open.querySelector('.faq-a').style.maxHeight = null;
        }
      });

      item.classList.toggle('is-open', !isOpen);
      a.style.maxHeight = !isOpen ? `${a.scrollHeight}px` : null;
    });
  });

  /* ---------- Contact form (Netlify Forms) ---------- */
  const form = document.getElementById('contactForm');
  const success = document.getElementById('formSuccess');
  const errorBox = document.getElementById('formError');

  const encode = (data) =>
    Object.keys(data)
      .map(key => `${encodeURIComponent(key)}=${encodeURIComponent(data[key])}`)
      .join('&');

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    if (!form.checkValidity()) {
      form.reportValidity();
      return;
    }

    errorBox.classList.remove('is-visible');
    const data = Object.fromEntries(new FormData(form).entries());

    fetch('/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: encode(data),
    })
      .then(() => {
        success.classList.add('is-visible');
        form.reset();
        setTimeout(() => success.classList.remove('is-visible'), 6000);
      })
      .catch(() => {
        errorBox.classList.add('is-visible');
      });
  });
});
