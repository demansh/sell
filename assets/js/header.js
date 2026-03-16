(function () {
  const header = document.querySelector('.site-header');
  if (!header) return;

  let lastY = window.scrollY;

  window.addEventListener('scroll', function () {
    const currentY = window.scrollY;
    if (currentY < lastY || currentY <= 0) {
      header.classList.remove('site-header--hidden');
    } else {
      header.classList.add('site-header--hidden');
    }
    lastY = currentY;
  }, { passive: true });
})();
