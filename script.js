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

    // Update dot indicators immediately (no need to wait for animation)
    document.querySelectorAll('.indicator').forEach((indicator, index) => {
        indicator.classList.toggle('active', index === currentSlideIndex);
        indicator.setAttribute('aria-selected', index === currentSlideIndex ? 'true' : 'false');
    });

    // Skip animation when reduced motion is preferred
    if (prefersReducedMotion) {
        slideImg.src = getSlidePath(currentSlideIndex);
        slideImg.alt = `Слайд презентации проекта ${currentSlideIndex + 1} из ${TOTAL_SLIDES}`;
        isAnimating = false;
        return;
    }

    // Step 1: animate current slide out
    slideImg.classList.add(outClass);

    slideImg.addEventListener('animationend', () => {
        slideImg.classList.remove(outClass);

        // Step 2: swap image source
        slideImg.src = getSlidePath(currentSlideIndex);
        slideImg.alt = `Слайд презентации проекта ${currentSlideIndex + 1} из ${TOTAL_SLIDES}`;

        const animateIn = () => {
            slideImg.classList.add(inClass);
            slideImg.addEventListener('animationend', () => {
                slideImg.classList.remove(inClass);
                isAnimating = false;
            }, { once: true });
        };

        // Step 3: animate in — handle both cached and fresh images
        if (slideImg.complete && slideImg.naturalWidth > 0) {
            animateIn();
        } else {
            slideImg.onload = () => {
                slideImg.onload = null;
                animateIn();
            };
            // Safety fallback if load event never fires (e.g. error)
            slideImg.onerror = () => {
                slideImg.onerror = null;
                isAnimating = false;
            };
        }
    }, { once: true });
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
preloadSlides();
initVideo();
initNavigation();
initReducedMotionListener();