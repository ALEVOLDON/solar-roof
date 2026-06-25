const TOTAL_SLIDES = 12;
const STAGE_MARKERS = [
    { end: 4.0, buttonId: 'btn-stage-1' },
    { end: 8.0, buttonId: 'btn-stage-2' },
    { end: Infinity, buttonId: 'btn-stage-3' },
];

const projectVideo = document.getElementById('project-video');
const slideLayerA = document.getElementById('carousel-slide-a');
const slideLayerB = document.getElementById('carousel-slide-b');
const indicatorsContainer = document.getElementById('carousel-indicators-container');
const menuToggle = document.getElementById('menu-toggle');
const navLinks = document.getElementById('nav-links');

let currentSlideIndex = 0;
let activeLayer = slideLayerA;
let idleLayer = slideLayerB;
let isTransitioning = false;
let prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

const slideCache = new Map();

function getSlidePath(index) {
    return `slides/slide_${index + 1}.webp`;
}

function updateIndicators(index) {
    document.querySelectorAll('.indicator').forEach((indicator, indicatorIndex) => {
        const isActive = indicatorIndex === index;
        indicator.classList.toggle('active', isActive);
        indicator.setAttribute('aria-selected', isActive ? 'true' : 'false');
    });
}

async function loadSlideIntoImage(image, src, alt) {
    if (slideCache.has(src)) {
        image.src = src;
        image.alt = alt;
        return;
    }

    const preload = new Image();
    preload.src = src;

    try {
        await preload.decode();
    } catch {
        // decode() is not supported everywhere; the browser will still paint eventually
    }

    image.src = src;
    image.alt = alt;
    slideCache.set(src, true);
}

function swapLayers() {
    const previousActive = activeLayer;
    activeLayer = idleLayer;
    idleLayer = previousActive;
}

function showSlide(index) {
    if (!activeLayer || !idleLayer || isTransitioning) return;

    const newSrc = getSlidePath(index);
    const newAlt = `Слайд презентации проекта ${index + 1} из ${TOTAL_SLIDES}`;

    if (activeLayer.src.includes(newSrc)) {
        updateIndicators(index);
        return;
    }

    isTransitioning = true;
    updateIndicators(index);

    loadSlideIntoImage(idleLayer, newSrc, newAlt).then(() => {
        idleLayer.classList.add('is-visible');

        if (prefersReducedMotion) {
            activeLayer.classList.remove('is-visible');
            swapLayers();
            isTransitioning = false;
            return;
        }

        let finished = false;
        const finish = () => {
            if (finished) return;
            finished = true;
            activeLayer.classList.remove('is-visible');
            swapLayers();
            isTransitioning = false;
        };

        idleLayer.addEventListener('transitionend', finish, { once: true });
        window.setTimeout(finish, 280);
    });
}

function changeSlide(direction) {
    currentSlideIndex = (currentSlideIndex + direction + TOTAL_SLIDES) % TOTAL_SLIDES;
    showSlide(currentSlideIndex);
}

function setSlide(index) {
    currentSlideIndex = index;
    showSlide(currentSlideIndex);
}

function jumpToStage(seconds, element) {
    if (!projectVideo) return;

    projectVideo.currentTime = seconds;
    projectVideo.play().catch(() => {});

    if (element) {
        document.querySelectorAll('.timeline-btn').forEach((btn) => {
            btn.classList.remove('active');
            btn.setAttribute('aria-selected', 'false');
        });
        element.classList.add('active');
        element.setAttribute('aria-selected', 'true');
    }

    document.getElementById('timeline')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function updateTimelineButtons(time) {
    const activeStage = STAGE_MARKERS.find((stage) => time < stage.end);
    if (!activeStage) return;

    const activeButton = document.getElementById(activeStage.buttonId);
    if (!activeButton || activeButton.classList.contains('active')) return;

    document.querySelectorAll('.timeline-btn').forEach((btn) => {
        btn.classList.remove('active');
        btn.setAttribute('aria-selected', 'false');
    });
    activeButton.classList.add('active');
    activeButton.setAttribute('aria-selected', 'true');
}

function toggleMenu(open) {
    if (!navLinks || !menuToggle) return;

    navLinks.classList.toggle('open', open);
    menuToggle.classList.toggle('open', open);
    menuToggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    menuToggle.setAttribute('aria-label', open ? 'Закрыть меню' : 'Открыть меню');
}

function preloadSlides() {
    for (let index = 0; index < TOTAL_SLIDES; index += 1) {
        const src = getSlidePath(index);
        const img = new Image();
        img.src = src;
        img.decode?.().then(() => {
            slideCache.set(src, true);
        }).catch(() => {
            slideCache.set(src, true);
        });
    }
}

function initTouchSwipe() {
    const container = document.querySelector('.carousel-container');
    if (!container) return;

    let startX = 0;
    let startY = 0;

    container.addEventListener('touchstart', (event) => {
        startX = event.touches[0].clientX;
        startY = event.touches[0].clientY;
    }, { passive: true });

    container.addEventListener('touchend', (event) => {
        const dx = event.changedTouches[0].clientX - startX;
        const dy = event.changedTouches[0].clientY - startY;

        if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy)) {
            changeSlide(dx < 0 ? 1 : -1);
        }
    }, { passive: true });
}

function initCarousel() {
    if (!indicatorsContainer) return;

    for (let index = 0; index < TOTAL_SLIDES; index += 1) {
        const indicator = document.createElement('button');
        indicator.type = 'button';
        indicator.classList.add('indicator');
        indicator.setAttribute('role', 'tab');
        indicator.setAttribute('aria-label', `Перейти к слайду ${index + 1}`);
        indicator.setAttribute('aria-selected', index === 0 ? 'true' : 'false');
        if (index === 0) indicator.classList.add('active');
        indicator.addEventListener('click', () => setSlide(index));
        indicatorsContainer.appendChild(indicator);
    }

    document.getElementById('carousel-prev-btn')?.addEventListener('click', () => changeSlide(-1));
    document.getElementById('carousel-next-btn')?.addEventListener('click', () => changeSlide(1));
}

function initVideo() {
    if (!projectVideo) return;

    if (prefersReducedMotion) {
        projectVideo.removeAttribute('autoplay');
        projectVideo.pause();
    } else {
        projectVideo.setAttribute('autoplay', '');
        projectVideo.play().catch(() => {});
    }

    projectVideo.addEventListener('timeupdate', () => {
        updateTimelineButtons(projectVideo.currentTime);
    });

    document.querySelectorAll('.timeline-btn').forEach((button) => {
        button.addEventListener('click', (event) => {
            const seconds = Number(button.dataset.seconds || 0);
            jumpToStage(seconds, event.currentTarget);
        });
    });

    document.getElementById('hero-video-link')?.addEventListener('click', (event) => {
        event.preventDefault();
        jumpToStage(0, document.getElementById('btn-stage-1'));
    });
}

function initNavigation() {
    menuToggle?.addEventListener('click', () => {
        toggleMenu(!navLinks.classList.contains('open'));
    });

    document.querySelectorAll('.nav-links a').forEach((link) => {
        link.addEventListener('click', () => toggleMenu(false));
    });

    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') {
            toggleMenu(false);
        }

        if (event.key === 'ArrowLeft') {
            changeSlide(-1);
        }

        if (event.key === 'ArrowRight') {
            changeSlide(1);
        }
    });

    document.addEventListener('click', (event) => {
        if (!navLinks?.classList.contains('open')) return;
        const target = event.target;
        if (target === menuToggle || menuToggle?.contains(target) || navLinks.contains(target)) return;
        toggleMenu(false);
    });
}

function initReducedMotionListener() {
    const motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    motionQuery.addEventListener('change', (event) => {
        prefersReducedMotion = event.matches;
        if (prefersReducedMotion && projectVideo) {
            projectVideo.pause();
            projectVideo.removeAttribute('autoplay');
        }
    });
}

initCarousel();
initTouchSwipe();
preloadSlides();
initVideo();
initNavigation();
initReducedMotionListener();