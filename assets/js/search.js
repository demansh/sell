// Search filter functionality
const searchInput = document.getElementById('searchInput');

if (searchInput) {
  searchInput.addEventListener('input', function(e) {
    const query = e.target.value.toLowerCase().trim();
    const posts = document.querySelectorAll('.post-card');
    let hasResults = false;

    posts.forEach(post => {
      const content = post.dataset.content || '';
      const author = post.dataset.author || '';

      if (content.includes(query) || author.includes(query)) {
        post.style.display = 'block';
        hasResults = true;
      } else {
        post.style.display = 'none';
      }
    });
  });
}

// Adjust search bar position when keyboard appears (mobile)
if (window.visualViewport) {
  const container = document.querySelector('.search-container');

  function pinToVisualViewport() {
    if (!container) return;
    const vv = window.visualViewport;
    const bottomOffset = window.innerHeight - (vv.offsetTop + vv.height);
    container.style.bottom = (bottomOffset + 20) + 'px';
  }

  window.visualViewport.addEventListener('resize', pinToVisualViewport);
  window.visualViewport.addEventListener('scroll', pinToVisualViewport);
}