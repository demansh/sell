// Search filter functionality
const searchInput = document.getElementById('searchInput');

function repositionPremium(container) {
  const premiumCard = container.querySelector('[data-premium="true"]');
  if (!premiumCard || premiumCard.style.display === 'none') return;

  const visibleRegular = [...container.querySelectorAll('.post-card:not([data-premium="true"])')]
    .filter(c => c.style.display !== 'none');

  if (visibleRegular.length > 0) {
    visibleRegular[0].insertAdjacentElement('afterend', premiumCard);
  } else {
    container.prepend(premiumCard);
  }
}

function filterPosts(query) {
  const normalized = query.toLowerCase().trim();
  const container = document.getElementById('postsContainer');
  container.querySelectorAll('.post-card').forEach(post => {
    const title = post.dataset.title.toLowerCase() || '';
    const keywords = post.dataset.keywords || '';
    const isMatch = title.includes(normalized) || keywords.includes(normalized);
    post.style.display = (normalized === '' || isMatch) ? 'block' : 'none';
  });
  repositionPremium(container);
}

if (searchInput) {
  const params = new URLSearchParams(window.location.search);
  const initialQuery = params.get('q') || '';
  if (initialQuery) {
    searchInput.value = initialQuery;
    filterPosts(initialQuery);
  }

  searchInput.addEventListener('input', function(e) {
    const query = e.target.value;
    filterPosts(query);
    const url = new URL(window.location);
    if (query.trim()) {
      url.searchParams.set('q', query);
    } else {
      url.searchParams.delete('q');
    }
    history.replaceState(null, '', url);
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
