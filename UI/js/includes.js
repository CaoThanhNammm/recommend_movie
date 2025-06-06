/**
 * Hàm để import các thành phần HTML từ các file khác
 */
document.addEventListener('DOMContentLoaded', async () => {
    // Thêm CSS cho auth-buttons vào tất cả các trang
    const styleElement = document.createElement('style');
    styleElement.textContent = `
        .auth-buttons {
            display: flex;
            gap: 20px; /* Tăng khoảng cách giữa các nút */
        }
    `;
    document.head.appendChild(styleElement);
    
    // Import header
    const headerContainer = document.getElementById('header-container');
    if (headerContainer) {
        try {
            const headerResponse = await fetch('includes/header.html');
            const headerHtml = await headerResponse.text();
            headerContainer.innerHTML = headerHtml;
            
            // Đánh dấu menu hiện tại là active
            const currentPage = window.location.pathname.split('/').pop();
            if (currentPage === 'index.html' || currentPage === '') {
                document.getElementById('nav-home')?.classList.add('active');
            } else if (currentPage === 'movies.html') {
                document.getElementById('nav-movies')?.classList.add('active');
            } else if (currentPage === 'preferences.html') {
                document.getElementById('nav-preferences')?.classList.add('active');
            }
            
            // Khởi tạo các sự kiện cho header
            initHeaderEvents();
            
            // Cập nhật trạng thái đăng nhập
            if (typeof authService !== 'undefined') {
                authService.updateUI();
            }
        } catch (error) {
            console.error('Không thể tải header:', error);
            headerContainer.innerHTML = '<p class="error">Không thể tải header</p>';
        }
    }
    
    // Import footer
    const footerContainer = document.getElementById('footer-container');
    if (footerContainer) {
        try {
            const footerResponse = await fetch('includes/footer.html');
            const footerHtml = await footerResponse.text();
            footerContainer.innerHTML = footerHtml;
        } catch (error) {
            console.error('Không thể tải footer:', error);
            footerContainer.innerHTML = '<p class="error">Không thể tải footer</p>';
        }
    }
});

/**
 * Khởi tạo các sự kiện cho header
 */
function initHeaderEvents() {
    // Xử lý sự kiện đăng xuất
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', (e) => {
            e.preventDefault();
            if (typeof authService !== 'undefined' && authService.logout) {
                authService.logout();
                window.location.href = 'index.html';
            }
        });
    }
    
    // Xử lý hiển thị menu người dùng
    const userMenuBtn = document.getElementById('userMenuBtn');
    const userDropdown = document.getElementById('userDropdown');
    if (userMenuBtn && userDropdown) {
        userMenuBtn.addEventListener('click', () => {
            userDropdown.classList.toggle('active');
        });
        
        // Đóng dropdown khi click ra ngoài
        document.addEventListener('click', (event) => {
            if (!userMenuBtn.contains(event.target) && !userDropdown.contains(event.target)) {
                userDropdown.classList.remove('active');
            }
        });
    }
    
    // Cập nhật trạng thái đăng nhập
    if (typeof authService !== 'undefined') {
        // Đảm bảo rằng authService.updateUI được gọi
        authService.updateUI();
    }
}