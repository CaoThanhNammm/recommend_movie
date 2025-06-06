// Utility functions for the application

// Format date to readable string
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

// Format runtime to hours and minutes
function formatRuntime(minutes) {
    if (!minutes) return 'N/A';
    
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    
    if (hours === 0) return `${mins}m`;
    if (mins === 0) return `${hours}h`;
    
    return `${hours}h ${mins}m`;
}

// Format currency with commas and $ sign
function formatCurrency(amount) {
    if (!amount) return 'N/A';
    
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        maximumFractionDigits: 0
    }).format(amount);
}

// Generate star rating HTML
function generateStarRating(rating, maxRating = 5) {
    if (!rating) return 'No rating';
    
    const fullStars = Math.floor(rating);
    const halfStar = rating % 1 >= 0.5;
    const emptyStars = maxRating - fullStars - (halfStar ? 1 : 0);
    
    let starsHTML = '';
    
    // Full stars
    for (let i = 0; i < fullStars; i++) {
        starsHTML += '<i class="fas fa-star"></i>';
    }
    
    // Half star
    if (halfStar) {
        starsHTML += '<i class="fas fa-star-half-alt"></i>';
    }
    
    // Empty stars
    for (let i = 0; i < emptyStars; i++) {
        starsHTML += '<i class="far fa-star"></i>';
    }
    
    return starsHTML;
}

// Truncate text with ellipsis
function truncateText(text, maxLength = 100) {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    
    return text.substring(0, maxLength) + '...';
}

// Create movie card HTML
function createMovieCard(movie) {
    if (!movie) {
        console.error('Invalid movie data:', movie);
        return '';
    }
    
    // Ensure movie has required properties
    const movieData = {
        id: movie.id || movie.movie_id || 0,
        title: movie.title || 'Unknown Title',
        poster_path: movie.poster_path || null,
        vote_average: movie.vote_average || 0,
        release_date: movie.release_date || '',
        genres: movie.genres || []
    };
    
    // Extract year from release date
    const year = movieData.release_date ? new Date(movieData.release_date).getFullYear() : '';
    
    // Get genres (first 2)
    let genres = '';
    if (movieData.genres && movieData.genres.length > 0) {
        // Handle different genre formats (object with name or string)
        genres = movieData.genres.slice(0, 2).map(g => {
            const genreName = typeof g === 'string' ? g : (g.name || '');
            return `<span class="movie-genre">${genreName}</span>`;
        }).join('');
    }
    
    // Create HTML
    return `
        <div class="movie-card" data-id="${movieData.id}">
            <div class="movie-poster">
                <img src="${getImageUrl(movieData.poster_path)}" alt="${movieData.title}">
                <div class="movie-rating">${movieData.vote_average ? movieData.vote_average.toFixed(1) : 'N/A'}</div>
            </div>
            <div class="movie-info">
                <h3 class="movie-title">${movieData.title}</h3>
                <div class="movie-year">${year}</div>
                <div class="movie-genres">${genres}</div>
                <div class="movie-actions">
                    <button class="watch-later" title="Add to watch later">
                        <i class="far fa-bookmark"></i>
                    </button>
                    <a href="movie.html?id=${movieData.id}" class="btn btn-primary">Chi tiết</a>
                </div>
            </div>
        </div>
    `;
}

// Show loading spinner
function showLoading(container) {
    container.innerHTML = `
        <div class="loading-spinner">
            <i class="fas fa-spinner fa-spin"></i>
            <span>Loading...</span>
        </div>
    `;
}

// Show error message
function showError(container, message = 'Something went wrong. Please try again.') {
    container.innerHTML = `
        <div class="error-message">
            <i class="fas fa-exclamation-circle"></i>
            <p>${message}</p>
            <button class="btn btn-primary retry-btn">Retry</button>
        </div>
    `;
    
    // Add retry button event listener
    const retryBtn = container.querySelector('.retry-btn');
    if (retryBtn) {
        retryBtn.addEventListener('click', () => {
            // Dispatch a custom event that can be caught by the page script
            container.dispatchEvent(new CustomEvent('retry'));
        });
    }
}

// Show empty state
function showEmptyState(container, message = 'No results found.') {
    container.innerHTML = `
        <div class="empty-state">
            <i class="fas fa-film"></i>
            <p>${message}</p>
        </div>
    `;
}

// Debounce function for search inputs
function debounce(func, delay = 300) {
    let timeout;
    
    return function(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), delay);
    };
}

// Parse URL parameters
function getUrlParams() {
    const params = {};
    const queryString = window.location.search;
    const urlParams = new URLSearchParams(queryString);
    
    for (const [key, value] of urlParams.entries()) {
        params[key] = value;
    }
    
    return params;
}

// Make API request with error handling
async function apiRequest(endpoint, options = {}) {
    try {
        console.log("Original endpoint:", endpoint);
        
        // Normalize endpoint URL to ensure it works with the API
        let normalizedEndpoint = endpoint;
        
        // For endpoints with query parameters, make sure there's a trailing slash before the query
        if (normalizedEndpoint.includes('/?')) {
            normalizedEndpoint = normalizedEndpoint.replace('/?', '?');
        }
        
        // Add trailing slash to prevent redirects which can cause CORS issues with preflight requests
        // Only add if there's no query string and no trailing slash already
        if (!normalizedEndpoint.includes('?') && !normalizedEndpoint.endsWith('/')) {
            normalizedEndpoint += '/';
        }
        
        // Special handling for movie details endpoint
        if (normalizedEndpoint.match(/\/movies\/\d+$/)) {
            normalizedEndpoint += '/';
        }
        
        endpoint = normalizedEndpoint;
        const fullUrl = `${API_CONFIG.BASE_URL}${endpoint}`;
        console.log('Making API request to:', fullUrl);
        
        // Add auth token if user is authenticated
        const headers = authService.isAuthenticated() 
            ? authService.getAuthHeaders() 
            : API_CONFIG.DEFAULT_HEADERS;
        
        // Set up request options
        const requestOptions = {
            method: options.method || 'GET',
            headers: { 
                ...headers, 
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                ...options.headers 
            },
            mode: 'cors', // Explicitly set CORS mode
            credentials: 'include', // Changed to 'include' to support cookies if needed
            ...options
        };
        
        // Don't override our carefully constructed headers and credentials
        delete requestOptions.headers;
        
        // Merge headers properly
        requestOptions.headers = { 
            ...headers, 
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            ...options.headers 
        };
        
        console.log('Request options:', JSON.stringify(requestOptions));
        
        // Add body for non-GET requests
        if (options.body && requestOptions.method !== 'GET') {
            requestOptions.body = JSON.stringify(options.body);
        }
        
        // Make request with timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), API_CONFIG.TIMEOUT);
        
        requestOptions.signal = controller.signal;
        
        try {
            // Make the actual request
            const response = await fetch(fullUrl, requestOptions);
            console.log('Response status:', response.status);
            console.log('Response headers:', [...response.headers.entries()]);
         
            clearTimeout(timeoutId);
            
            // Check if response is ok before trying to parse JSON
            if (!response.ok) {
                let errorData;
                try {
                    // Try to parse as JSON first
                    const contentType = response.headers.get('content-type');
                    if (contentType && contentType.includes('application/json')) {
                        errorData = await response.json();
                        console.error('API error response (JSON):', response.status, errorData);
                        throw new Error(errorData.message || `API request failed with status ${response.status}`);
                    } else {
                        // If not JSON, get as text
                        const errorText = await response.text();
                        console.error('API error response (text):', response.status, errorText);
                        throw new Error(`API request failed with status ${response.status}: ${errorText}`);
                    }
                } catch (parseError) {
                    // If parsing fails, use the original response status
                    console.error('Error parsing error response:', parseError);
                    throw new Error(`API request failed with status ${response.status}`);
                }
            }
            
            // Parse response
            let data;
            try {
                const contentType = response.headers.get('content-type');
                if (contentType && contentType.includes('application/json')) {
                    data = await response.json();
                } else {
                    const text = await response.text();
                    console.warn('Non-JSON response:', text);
                    // Try to parse as JSON anyway in case the Content-Type header is wrong
                    try {
                        data = JSON.parse(text);
                    } catch (e) {
                        // If it's not valid JSON, create a simple object
                        data = { message: text };
                    }
                }
            } catch (parseError) {
                console.error('Error parsing response:', parseError);
                throw new Error('Failed to parse API response');
            }
            
            console.log('API response data:', data);
            
            return { success: true, data };
        } catch (fetchError) {
            // This catch block specifically handles fetch errors
            clearTimeout(timeoutId);
            throw fetchError; // Re-throw to be caught by the outer catch block
        }
    } catch (error) {
        console.error('API request error:', error);
        
        // Handle token expiration
        if (error.message && error.message.includes('token') && error.message.includes('expired')) {
            authService.logout();
        }
        
        // Handle network errors more specifically
        let errorMessage = error.message;
        
        if (error.name === 'AbortError') {
            errorMessage = 'Request timed out. Please try again.';
        } else if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
            errorMessage = `Network error: Failed to connect to the API server at ${API_CONFIG.BASE_URL}. Please check if the server is running and accessible.`;
        } else if (error.message.includes('NetworkError') || error.message.includes('CORS')) {
            errorMessage = `Network error: Unable to connect to the API server at ${API_CONFIG.BASE_URL}. This might be due to CORS issues or the server being offline. Try running both the frontend and backend on the same origin.`;
        } else if (error.message.includes('SyntaxError')) {
            errorMessage = 'Invalid response from server. The API returned data in an unexpected format.';
        }
        
        console.warn('Formatted error message:', errorMessage);
        return { success: false, error: errorMessage };
    }
}