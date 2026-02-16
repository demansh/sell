function moveCarousel(direction) {
  const carousel = document.getElementById('carousel');
  const scrollAmount = carousel.offsetWidth;
  carousel.scrollBy({
    left: scrollAmount * direction,
    behavior: 'smooth'
  });
}

// Опционально: перетаскивание мышкой (drag-to-scroll)
const slider = document.getElementById('carousel');
let isDown = false;
let startX;
let scrollLeft;

slider.addEventListener('mousedown', (e) => {
  isDown = true;
  startX = e.pageX - slider.offsetLeft;
  scrollLeft = slider.scrollLeft;
});
slider.addEventListener('mouseleave', () => isDown = false);
slider.addEventListener('mouseup', () => isDown = false);
slider.addEventListener('mousemove', (e) => {
  if(!isDown) return;
  e.preventDefault();
  const x = e.pageX - slider.offsetLeft;
  const walk = (x - startX) * 2;
  slider.scrollLeft = scrollLeft - walk;
});