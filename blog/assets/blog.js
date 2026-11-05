// MYTH 博客脚本：主题切换 / 移动端菜单 / 滚动阴影 / 入场动画
(function () {
    'use strict';
    window.__blogReady = true;

    // ===== 主题切换（与主页共用 localStorage 的 theme 键）=====
    var themeToggle = document.getElementById('themeToggle');
    var prefersDark = window.matchMedia('(prefers-color-scheme: dark)');

    function setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
    }

    if (themeToggle) {
        themeToggle.addEventListener('click', function () {
            var current = document.documentElement.getAttribute('data-theme');
            setTheme(current === 'dark' ? 'light' : 'dark');
        });
    }
    prefersDark.addEventListener('change', function (e) {
        if (!localStorage.getItem('theme')) {
            setTheme(e.matches ? 'dark' : 'light');
        }
    });

    // ===== 移动端菜单 =====
    var navToggle = document.getElementById('navToggle');
    var navLinks = document.getElementById('navLinks');
    if (navToggle && navLinks) {
        navToggle.addEventListener('click', function () {
            navLinks.classList.toggle('open');
        });
        navLinks.addEventListener('click', function (e) {
            if (e.target.tagName === 'A') navLinks.classList.remove('open');
        });
    }

    // ===== 滚动阴影 =====
    var navbar = document.getElementById('navbar');
    function onScroll() {
        if (!navbar) return;
        navbar.classList.toggle('scrolled', window.scrollY > 10);
    }
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();

    // ===== 入场动画（滚动触发 + 定时兜底，不依赖 IntersectionObserver）=====
    var faders = document.querySelectorAll('.fade-up');
    function revealInView() {
        var vh = window.innerHeight;
        for (var i = 0; i < faders.length; i++) {
            var el = faders[i];
            if (el.classList.contains('visible')) continue;
            var r = el.getBoundingClientRect();
            if (r.top < vh - 40 && r.bottom > 0) el.classList.add('visible');
        }
    }
    window.addEventListener('scroll', revealInView, { passive: true });
    window.addEventListener('resize', revealInView);
    window.addEventListener('load', revealInView);
    revealInView();
    setTimeout(revealInView, 200);
    setTimeout(revealInView, 1200);
    // 保险：3 秒后无论如何全部显示，内容永不隐身
    setTimeout(function () {
        for (var i = 0; i < faders.length; i++) faders[i].classList.add('visible');
    }, 3000);
})();
