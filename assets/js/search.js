// 1. Логика фильтрации (та же, что была раньше)
const searchInput = document.getElementById('searchInput');
if (searchInput) {
  searchInput.addEventListener('input', function(e) {
    const query = e.target.value.toLowerCase().trim();
    const posts = document.querySelectorAll('.post-card');
    let hasResults = false;

    posts.forEach(post => {
      const content = post.dataset.content || "";
      const author = post.dataset.author || "";
      if (content.includes(query) || author.includes(query)) {
        post.style.display = 'block';
        hasResults = true;
      } else {
        post.style.display = 'none';
      }
    });
    // Тут можно добавить логику noResultsMsg из прошлого шага
  });
}

// 2. Фикс для клавиатуры: чтобы инпут не перекрывался на некоторых Android-браузерах
window.visualViewport.addEventListener('resize', () => {
  const container = document.querySelector('.search-container');
  if (container) {
    // Поднимаем контейнер, если клавиатура открыта
    container.style.bottom = `${window.innerHeight - window.visualViewport.height + 20}px`;
  }
});