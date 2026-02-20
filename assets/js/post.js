// Carousel drag-to-scroll for desktop
const carousel = document.querySelector('.post-carousel');

if (carousel) {
  // Dot indicators
  const dotsContainer = document.querySelector('.carousel-dots');
  if (dotsContainer) {
    const items = carousel.querySelectorAll('.carousel-item');
    items.forEach((_, i) => {
      const dot = document.createElement('div');
      dot.className = 'carousel-dot' + (i === 0 ? ' active' : '');
      dotsContainer.appendChild(dot);
    });

    const dots = dotsContainer.querySelectorAll('.carousel-dot');
    carousel.addEventListener('scroll', () => {
      const index = Math.round(carousel.scrollLeft / carousel.clientWidth);
      dots.forEach((d, i) => d.classList.toggle('active', i === index));
    }, { passive: true });
  }


  let isDown = false;
  let startX;
  let scrollLeft;

  carousel.addEventListener('mousedown', (e) => {
    isDown = true;
    carousel.style.cursor = 'grabbing';
    startX = e.pageX - carousel.offsetLeft;
    scrollLeft = carousel.scrollLeft;
  });

  carousel.addEventListener('mouseleave', () => {
    isDown = false;
    carousel.style.cursor = 'grab';
  });

  carousel.addEventListener('mouseup', () => {
    isDown = false;
    carousel.style.cursor = 'grab';
  });

  carousel.addEventListener('mousemove', (e) => {
    if (!isDown) return;
    e.preventDefault();
    const x = e.pageX - carousel.offsetLeft;
    const walk = (x - startX) * 2;
    carousel.scrollLeft = scrollLeft - walk;
  });
}