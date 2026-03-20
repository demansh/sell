document.addEventListener('DOMContentLoaded', () => {
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('sidebar-overlay');
  const hamburger = document.getElementById('hamburger-menu');
  const closeBtn = document.getElementById('close-sidebar');
  const keywordLinks = document.querySelectorAll('.keyword-link');

  function openSidebar() {
    sidebar.classList.add('active');
    overlay.classList.add('active');
    hamburger.classList.add('open');
    document.body.style.overflow = 'hidden'; // Prevent background scrolling
  }

  function closeSidebar() {
    sidebar.classList.remove('active');
    overlay.classList.remove('active');
    hamburger.classList.remove('open');
    document.body.style.overflow = ''; 
  }

  // Toggle/Open
  hamburger.addEventListener('click', () => {
    sidebar.classList.contains('active') ? closeSidebar() : openSidebar();
  });

  // Close actions
  if(closeBtn) closeBtn.addEventListener('click', closeSidebar);
  overlay.addEventListener('click', closeSidebar);

  keywordLinks.forEach(link => {
    link.addEventListener('click', (e) => {
        const targetUrl = new URL(link.href, window.location.origin);
        const query = targetUrl.searchParams.get('q');
        
        // Check if we are currently on the home page (root or index.html)
        const isHomePage = window.location.pathname === '/' || window.location.pathname === '/index.html';

        if (isHomePage) {
        // CASE A: On Home Page - Filter instantly without reload
        e.preventDefault();
        
        if (searchInput) {
            searchInput.value = query;
        }
        
        filterPosts(query);
        history.pushState(null, '', targetUrl);
        closeSidebar();
        } else {
        // CASE B: Not on Home Page - Let the browser navigate to /?q=...
        // The Sidebar will close naturally as the new page loads
        return; 
        }
    });
  });
});

window.addEventListener('popstate', () => {
  const params = new URLSearchParams(window.location.search);
  const query = params.get('q') || '';
  
  if (searchInput) {
    searchInput.value = query;
  }
  filterPosts(query);
});