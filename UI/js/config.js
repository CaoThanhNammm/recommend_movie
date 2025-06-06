// API Configuration
const API_CONFIG = {
    // You can change this URL if your API is running on a different host or port
    BASE_URL: 'http://127.0.0.1:5000/api', // Đảm bảo API server đang chạy ở địa chỉ này
    ENDPOINTS: {
        // Auth endpoints
        REGISTER: '/auth/register',
        LOGIN: '/auth/login',
        PROFILE: '/auth/profile',
        
        // Movie endpoints
        MOVIES: '/movies',
        MOVIE_DETAIL: '/movies/:id/',
        RATE_MOVIE: '/movies/:id/rate',
        WATCH_MOVIE: '/movies/:id/watch',
        GENRES: '/movies/genres',
        TOP_WEIGHTED: '/movies/top-weighted',
        
        // Recommendation endpoints
        RECOMMENDATIONS_WEIGHTED: '/recommendations/by-weighted-rating',
        RECOMMENDATIONS_PREFERENCES: '/recommendations/by-preferences',
        RECOMMENDATIONS_HISTORY: '/recommendations/by-history-and-preferences',
        RECOMMENDATIONS_PERSONALIZED: '/recommendations/personalized',
        
        // User preferences endpoints
        USER_PREFERENCES: '/preferences',
        UPDATE_PREFERENCES: '/preferences/update',
        CHECK_PREFERENCES: '/preferences/check',
        SAVE_PREFERENCES: '/preferences/save',
        
        // Cast and crew endpoints
        CAST: '/cast',
        CREW: '/crew',
        GENRES_LIST: '/genres'
    },
    DEFAULT_HEADERS: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    },
    TIMEOUT: 10000 // 10 seconds - reduced timeout for faster error feedback
};

// Local storage keys
const STORAGE_KEYS = {
    AUTH_TOKEN: 'cinematch_auth_token',
    USER_DATA: 'cinematch_user_data',
    PREFERENCES: 'cinematch_preferences'
};

// Default image paths
const DEFAULT_IMAGES = {
    POSTER: 'https://via.placeholder.com/300x450?text=No+Poster',
    PROFILE: 'https://via.placeholder.com/150?text=No+Image',
    BACKDROP: 'https://via.placeholder.com/1280x720?text=No+Backdrop'
};

// Image base URL (for TMDB images)
const IMAGE_BASE_URL = 'https://image.tmdb.org/t/p/';
const POSTER_SIZES = {
    SMALL: 'w185',
    MEDIUM: 'w342',
    LARGE: 'w500'
};

// Function to get full image URL
function getImageUrl(path, size = POSTER_SIZES.MEDIUM) {
    if (!path) return DEFAULT_IMAGES.POSTER;
    if (path.startsWith('http')) return path;
    return `${IMAGE_BASE_URL}${size}${path}`;
}

// Function to format API endpoint with parameters
function formatEndpoint(endpoint, params = {}) {
    let formattedEndpoint = endpoint;
    
    // Replace path parameters
    Object.keys(params).forEach(key => {
        formattedEndpoint = formattedEndpoint.replace(`:${key}`, params[key]);
    });
    
    // Add trailing slash for API endpoints that need it
    if (formattedEndpoint.includes('/movies/') && !formattedEndpoint.endsWith('/')) {
        formattedEndpoint += '/';
    }
    
    return formattedEndpoint;
}

// Export configuration
window.API_CONFIG = API_CONFIG;
window.STORAGE_KEYS = STORAGE_KEYS;
window.DEFAULT_IMAGES = DEFAULT_IMAGES;
window.getImageUrl = getImageUrl;
window.formatEndpoint = formatEndpoint;