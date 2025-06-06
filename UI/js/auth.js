// Auth Service
class AuthService {
    constructor() {
        this.token = localStorage.getItem(STORAGE_KEYS.AUTH_TOKEN);
        this.userData = JSON.parse(localStorage.getItem(STORAGE_KEYS.USER_DATA) || 'null');
        
        // Không gọi updateUI ở đây vì header có thể chưa được tải
        // updateUI sẽ được gọi sau khi header được tải trong includes.js
        
        // Add event listeners
        this.addEventListeners();
    }
    
    // Check if user is authenticated
    isAuthenticated() {
        return !!this.token;
    }
    
    // Get auth headers
    getAuthHeaders() {
        return {
            ...API_CONFIG.DEFAULT_HEADERS,
            'Authorization': `Bearer ${this.token}`
        };
    }
    
    // Register a new user
    async register(userData) {
        try {
            console.log('Registering user:', userData.username);
            console.log('API URL:', `${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.REGISTER}`);
            
            // Kiểm tra dữ liệu đầu vào
            if (!userData.username || !userData.email || !userData.password) {
                console.error('Missing required registration data');
                return {
                    success: false,
                    error: 'Vui lòng điền đầy đủ thông tin đăng ký'
                };
            }
            
            // Bỏ qua kiểm tra kết nối API trước khi gửi request vì có thể gây lỗi
            // Sẽ xử lý lỗi kết nối trong phần try-catch chính
            
            // Chuẩn bị dữ liệu đăng ký
            const registerData = {
                username: userData.username.trim(),
                email: userData.email.trim(),
                password: userData.password
            };
            
            console.log('Sending registration data:', JSON.stringify(registerData));
            
            const response = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.REGISTER}`, {
                method: 'POST',
                headers: API_CONFIG.DEFAULT_HEADERS,
                body: JSON.stringify(registerData),
                mode: 'cors'
            });
            
            console.log('Registration response status:', response.status);
            
            // Handle non-JSON responses
            let data;
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                data = await response.json();
            } else {
                const text = await response.text();
                console.warn('Non-JSON response:', text);
                data = { message: text || 'Registration failed with non-JSON response' };
            }
            
            console.log('Registration response data:', data);
            
            if (!response.ok) {
                // Handle specific error cases based on status code
                if (response.status === 409) {
                    // Conflict - username or email already exists
                    throw new Error(data.message || 'Username or email already exists');
                } else if (response.status === 400) {
                    // Bad request - missing required fields
                    throw new Error(data.message || 'Missing required fields');
                } else {
                    // Other errors
                    throw new Error(data.message || `Registration failed with status ${response.status}`);
                }
            }
            
            return { success: true, data };
        } catch (error) {
            console.error('Registration error:', error);
            
            // Provide more helpful error messages
            let errorMessage = error.message;
            if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
                errorMessage = 'Lỗi kết nối: Không thể kết nối đến máy chủ API. Vui lòng kiểm tra xem máy chủ có đang chạy tại ' + API_CONFIG.BASE_URL;
            }
            
            return { success: false, error: errorMessage };
        }
    }
    
    // Login user
    async login(credentials) {
        try {
            console.log('Logging in user:', credentials.username);
            console.log('API URL:', `${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.LOGIN}`);
            
            // Kiểm tra dữ liệu đầu vào
            if (!credentials.username || !credentials.password) {
                console.error('Missing required login credentials');
                return {
                    success: false,
                    error: 'Vui lòng nhập tên đăng nhập và mật khẩu'
                };
            }
            
            // Bỏ qua kiểm tra kết nối API trước khi gửi request vì có thể gây lỗi
            // Sẽ xử lý lỗi kết nối trong phần try-catch chính
            
            // Chuẩn bị dữ liệu đăng nhập
            const loginData = {
                username: credentials.username.trim(),
                password: credentials.password
            };
            
            console.log('Sending login data:', JSON.stringify(loginData));
            
            const response = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.LOGIN}`, {
                method: 'POST',
                headers: API_CONFIG.DEFAULT_HEADERS,
                body: JSON.stringify(loginData),
                mode: 'cors'
            });
            
            console.log('Login response status:', response.status);
            
            // Handle non-JSON responses
            let data;
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                data = await response.json();
            } else {
                const text = await response.text();
                console.warn('Non-JSON response:', text);
                data = { message: text || 'Login failed with non-JSON response' };
            }
            
            console.log('Login response data:', data);
            
            if (!response.ok) {
                // Handle specific error cases based on status code
                if (response.status === 401) {
                    // Unauthorized - invalid credentials
                    throw new Error(data.message || 'Invalid username or password');
                } else if (response.status === 400) {
                    // Bad request - missing required fields
                    throw new Error(data.message || 'Missing username or password');
                } else {
                    // Other errors
                    throw new Error(data.message || `Login failed with status ${response.status}`);
                }
            }
            
            // Save token and user data
            this.token = data.access_token;
            this.userData = data.user;
            
            localStorage.setItem(STORAGE_KEYS.AUTH_TOKEN, this.token);
            localStorage.setItem(STORAGE_KEYS.USER_DATA, JSON.stringify(this.userData));
            
            // Update UI
            this.updateUI();
            
            return { success: true, data };
        } catch (error) {
            console.error('Login error:', error);
            
            // Provide more helpful error messages
            let errorMessage = error.message;
            if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
                errorMessage = 'Lỗi kết nối: Không thể kết nối đến máy chủ API. Vui lòng kiểm tra xem máy chủ có đang chạy tại ' + API_CONFIG.BASE_URL;
            }
            
            return { success: false, error: errorMessage };
        }
    }
    
    // Logout user
    logout() {
        // Clear token and user data
        this.token = null;
        this.userData = null;
        
        localStorage.removeItem(STORAGE_KEYS.AUTH_TOKEN);
        localStorage.removeItem(STORAGE_KEYS.USER_DATA);
        localStorage.removeItem(STORAGE_KEYS.PREFERENCES);
        
        // Update UI
        this.updateUI();
        
        // Redirect to home page
        window.location.href = 'index.html';
    }
    
    // Get user profile
    async getProfile() {
        if (!this.isAuthenticated()) {
            return { success: false, error: 'Not authenticated' };
        }
        
        try {
            const response = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.PROFILE}`, {
                method: 'GET',
                headers: this.getAuthHeaders()
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.message || 'Failed to get profile');
            }
            
            // Update user data
            this.userData = data.user;
            localStorage.setItem(STORAGE_KEYS.USER_DATA, JSON.stringify(this.userData));
            
            // Save preferences
            if (data.preferences) {
                localStorage.setItem(STORAGE_KEYS.PREFERENCES, JSON.stringify(data.preferences));
            }
            
            // Update UI
            this.updateUI();
            
            return { success: true, data };
        } catch (error) {
            console.error('Get profile error:', error);
            return { success: false, error: error.message };
        }
    }
    
    // Update user profile
    async updateProfile(profileData) {
        if (!this.isAuthenticated()) {
            return { success: false, error: 'Not authenticated' };
        }
        
        try {
            const response = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.PROFILE}`, {
                method: 'PUT',
                headers: this.getAuthHeaders(),
                body: JSON.stringify(profileData)
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.message || 'Failed to update profile');
            }
            
            // Update user data
            this.userData = data.user;
            localStorage.setItem(STORAGE_KEYS.USER_DATA, JSON.stringify(this.userData));
            
            // Update UI
            this.updateUI();
            
            return { success: true, data };
        } catch (error) {
            console.error('Update profile error:', error);
            return { success: false, error: error.message };
        }
    }
    
    // Update UI based on auth state
    updateUI() {
        const authButtons = document.getElementById('authButtons');
        const userMenuContainer = document.getElementById('userMenuContainer');
        const usernameElement = document.getElementById('username');
        
        if (this.isAuthenticated() && this.userData) {
            // Hide auth buttons and show user menu
            if (authButtons) authButtons.style.display = 'none';
            if (userMenuContainer) userMenuContainer.style.display = 'block';
            if (usernameElement) usernameElement.textContent = this.userData.username;
        } else {
            // Show auth buttons and hide user menu
            if (authButtons) authButtons.style.display = 'flex';
            if (userMenuContainer) userMenuContainer.style.display = 'none';
        }
    }
    
    // Add event listeners
    addEventListeners() {
        // Chúng ta sẽ không thêm event listeners ở đây vì header có thể chưa được tải
        // Các event listeners sẽ được thêm trong hàm initHeaderEvents của includes.js
    }
    
    // Check if user is authenticated and redirect if not
    requireAuth() {
        if (!this.isAuthenticated()) {
            // Show auth modal
            const authModal = document.getElementById('authCheckModal');
            if (authModal) {
                authModal.classList.add('active');
                
                // Close modal button
                const closeModal = authModal.querySelector('.close-modal');
                if (closeModal) {
                    closeModal.addEventListener('click', () => {
                        authModal.classList.remove('active');
                    });
                }
            } else {
                // Redirect to login page if modal not available
                window.location.href = 'login.html';
            }
            
            return false;
        }
        
        return true;
    }
}

// Initialize auth service
const authService = new AuthService();