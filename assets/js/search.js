document.getElementById('searchInput').addEventListener('input', function(e) {
  const query = e.target.value.toLowerCase();
  const posts = document.querySelectorAll('.post-card');

  posts.forEach(post => {
    const content = post.getAttribute('data-content');
    const author = post.getAttribute('data-author');
    
    if (content.includes(query) || author.includes(query)) {
      post.style.display = 'block';
    } else {
      post.style.display = 'none';
    }
  });
});