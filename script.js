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

function updateSlide() {
    if (!slideImg) return;

    // 1. Fade out completely
    slideImg.style.opacity = '0';
    
    // 2. Wait for the transition to finish (matching the 0.2s CSS transition)
    window.setTimeout(() => {
        // 3. Change image src to load the new slide
        slideImg.src = getSlidePath(currentSlideIndex);
        slideImg.alt = `Слайд презентации проекта ${currentSlideIndex + 1} из ${TOTAL_SLIDES}`;
        
        // 4. Fade back in only after the browser has fully loaded the new image
        slideImg.onload = () => {
            slideImg.style.opacity = '1';
            slideImg.onload = null; // Clear listener
        };
    }, 200);

    document.querySelectorAll('.indicator').forEach((indicator, index) => {
        indicator.classList.toggle('active', index === currentSlideIndex);
        indicator.setAttribute('aria-selected', index === currentSlideIndex ? 'true' : 'false');
    });
}

function changeSlide(direction) {
    currentSlideIndex = (currentSlideIndex + direction + TOTAL_SLIDES) % TOTAL_SLIDES;
    updateSlide();
}

function setSlide(index) {
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