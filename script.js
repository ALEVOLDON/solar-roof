const TOTAL_SLIDES = 12;
const STAGE_MARKERS = [
    { end: 4.0, buttonId: 'btn-stage-1' },
    { end: 8.0, buttonId: 'btn-stage-2' },
    { end: Infinity, buttonId: 'btn-stage-3' },
];

const projectVideo = document.getElementById('project-video');
const slideImg = document.getElementById('carousel-slide-img');
const indicatorsContainer = document.getElementById('carousel-indicators-container');
const menuToggle = document.getElementById('menu-toggle');
const navLinks = document.getElementById('nav-links');

let currentSlideIndex = 0;
let prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

function getSlidePath(index) {
    const slideNumber = index + 1;
    return `slides/slide_${slideNumber}.webp`;
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

// Track the last navigation direction so animations know which way to fly
let slideDirection = 1; // 1 = forward (→), -1 = backward (←)
let isAnimating = false;

function updateSlide() {
    if (!slideImg || isAnimating) return;
    isAnimating = true;

    const outClass = slideDirection > 0 ? 'slide-out-left'  : 'slide-out-right';
    const inClass  = slideDirection > 0 ? 'slide-in-right'  : 'slide-in-left';
    const newSrc   = getSlidePath(currentSlideIndex);
    const newAlt   = `Слайд презентации проекта ${currentSlideIndex + 1} из ${TOTAL_SLIDES}`;

    // Update dot indicators immediately
    document.querySelectorAll('.indicator').forEach((indicator, index) => {
        indicator.classList.toggle('active', index === currentSlideIndex);
        indicator.setAttribute('aria-selected', index === currentSlideIndex ? 'true' : 'false');
    });

    if (prefersReducedMotion) {
        slideImg.src = newSrc;
        slideImg.alt = newAlt;
        isAnimating = false;
        return;
    }

    // --- Key fix for Android jank ---
    // Pre-decode the next image in a background thread WHILE the exit animation runs.
    // By the time the exit animation finishes, the image is already decoded and
    // setting img.src won't block the main thread.
    const preloadImg = new Image();
    preloadImg.src = newSrc;
    const imageReady = preloadImg.decode().catch(() => { /* ignore decode errors */ });

    // Start exit animation
    slideImg.classList.add(outClass);

    // Wait for exit animation to finish (with a timeout safety net for Android)
    const animOutDone = new Promise(resolve => {
        const timer = setTimeout(resolve, 300); // fallback if animationend doesn't fire
        slideImg.addEventListener('animationend', () => {
            clearTimeout(timer);
            resolve();
        }, { once: true });
    });

    // Only proceed when BOTH: exit animation done AND image decoded
    Promise.all([animOutDone, imageReady]).then(() => {
        slideImg.classList.remove(outClass);
        slideImg.src = newSrc;
        slideImg.alt = newAlt;

        // Double rAF: first frame commits the src swap to layout,
        // second frame starts the entrance animation cleanly
        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                slideImg.classList.add(inClass);

                const timer = setTimeout(() => {
                    slideImg.classList.remove(inClass);
                    isAnimating = false;
                }, 400); // fallback

                slideImg.addEventListener('animationend', () => {
                    clearTimeout(timer);
                    slideImg.classList.remove(inClass);
                    isAnimating = false;
                }, { once: true });
            });
        });
    });
}

function changeSlide(direction) {
    slideDirection = direction;
    currentSlideIndex = (currentSlideIndex + direction + TOTAL_SLIDES) % TOTAL_SLIDES;
    updateSlide();
}

function setSlide(index) {
    // Determine direction from current position so the animation feels natural
    slideDirection = index > currentSlideIndex ? 1 : -1;
    currentSlideIndex = index;
    updateSlide();
}

function toggleMenu(open) {
    if (!navLinks || !menuToggle) return;

    navLinks.classList.toggle('open', open);
    menuToggle.classList.toggle('open', open);
    menuToggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    menuToggle.setAttribute('aria-label', open ? 'Закрыть меню' : 'Открыть меню');
}

function preloadSlides() {
    // Don't preload unnecessarily when the user has requested reduced data usage
    if (prefersReducedMotion) return;

    const preloadedImages = [];
    for (let index = 0; index < TOTAL_SLIDES; index += 1) {
        const img = new Image();
        img.src = getSlidePath(index);
        preloadedImages.push(img);
    }
}

function initTouchSwipe() {
    const container = document.querySelector('.carousel-container');
    if (!container) return;

    let startX = 0;
    let startY = 0;

    container.addEventListener('touchstart', (e) => {
        startX = e.touches[0].clientX;
        startY = e.touches[0].clientY;
    }, { passive: true });

    container.addEventListener('touchend', (e) => {
        const dx = e.changedTouches[0].clientX - startX;
        const dy = e.changedTouches[0].clientY - startY;
        // Swipe only if horizontal movement > 50px and more horizontal than vertical
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
    updateSlide();
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