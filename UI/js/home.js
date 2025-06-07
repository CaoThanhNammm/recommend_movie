// Home page script
document.addEventListener('DOMContentLoaded', async () => {
    // Get container elements
    const recommendedMoviesContainer = document.getElementById('recommendedMovies');
    const topRatedMoviesContainer = document.getElementById('topRatedMovies');
    
    // Load recommendations if user is authenticated
    if (authService.isAuthenticated()) {
        loadPersonalizedRecommendations();
    } else {
        // Show message to login for personalized recommendations
        recommendedMoviesContainer.innerHTML = `
            <div class="auth-prompt">
                <i class="fas fa-user-lock"></i>
                <h3>Get Personalized Recommendations</h3>
                <p>Log in to see movie recommendations tailored just for you.</p>
                <div class="auth-prompt-buttons">
                    <a href="login.html" class="btn btn-primary">Login</a>
                    <a href="register.html" class="btn btn-secondary">Register</a>
                </div>
            </div>
        `;
    }
    
    // Load top rated movies for all users
    loadTopRatedMovies();
    
    // Function to load personalized recommendations
    async function loadPersonalizedRecommendations() {
        try {
            // Show loading state
            recommendedMoviesContainer.innerHTML = '';
            for (let i = 0; i < 8; i++) {
                recommendedMoviesContainer.innerHTML += '<div class="movie-card skeleton"></div>';
            }
            
            // Make API request
            // Yêu cầu số phim lớn hơn để đảm bảo nhận đủ 8 phim
            const response = await apiRequest(API_CONFIG.ENDPOINTS.RECOMMENDATIONS_PERSONALIZED, {
                method: 'POST',
                body: { 
                    limit: 20, // Tăng limit lên để đảm bảo nhận đủ 8 phim
                    min_wr: 6.5  // Giảm điểm WR để có nhiều phim hơn
                }
            });
            
            // Clear loading state
            recommendedMoviesContainer.innerHTML = '';
            
            if (!response.success) {
                throw new Error(response.error);
            }
            
            const { recommendations, stage } = response.data;
            
            // Display recommendations
            if (recommendations && recommendations.length > 0) {
                // Lấy chính xác 8 phim đầu tiên từ danh sách đề xuất
                const moviesToShow = recommendations.slice(0, 8);
                
                // Kiểm tra xem có đủ 8 phim không
                if (moviesToShow.length < 8) {
                    console.warn(`Chỉ nhận được ${moviesToShow.length} phim từ API thay vì 8 phim như yêu cầu`);
                }
                
                moviesToShow.forEach(movie => {
                    // Make sure movie has all required properties
                    const processedMovie = {
                        id: movie.id || movie.movie_id,
                        title: movie.title,
                        poster_path: movie.poster_path,
                        vote_average: movie.vote_average,
                        wr: movie.wr,
                        release_date: movie.release_date,
                        genres: movie.genres || []
                    };
                    recommendedMoviesContainer.innerHTML += createMovieCard(processedMovie);
                });
                
                // Add event listeners to movie cards
                addMovieCardEventListeners(recommendedMoviesContainer);
            } else {
                // Show empty state and adjust container for centering
                recommendedMoviesContainer.classList.add('movie-grid-empty');
                recommendedMoviesContainer.innerHTML = `
                    <div class="empty-state">
                        <i class="fas fa-film"></i>
                        <p>Không tìm thấy đề xuất nào. Hãy cập nhật sở thích của bạn.</p>
                        <a href="preferences.html" class="btn btn-primary">Cập Nhật Sở Thích</a>
                    </div>
                `;
            }
        } catch (error) {
            console.error('Error loading recommendations:', error);
            
            // Show error state
            recommendedMoviesContainer.innerHTML = `
                <div class="error-state">
                    <i class="fas fa-exclamation-circle"></i>
                    <p>Failed to load recommendations. Please try again.</p>
                    <button id="retryRecommendations" class="btn btn-primary">Retry</button>
                </div>
            `;
            
            // Add retry button event listener
            document.getElementById('retryRecommendations')?.addEventListener('click', loadPersonalizedRecommendations);
        }
    }
    
    // Function to load top rated movies
    async function loadTopRatedMovies() {
        try {
            // Show loading state
            topRatedMoviesContainer.innerHTML = '';
            for (let i = 0; i < 8; i++) {
                topRatedMoviesContainer.innerHTML += '<div class="movie-card skeleton"></div>';
            }
            
            // Make API request
            const response = await apiRequest(API_CONFIG.ENDPOINTS.TOP_WEIGHTED + '/?limit=8');
            
            // Clear loading state
            topRatedMoviesContainer.innerHTML = '';
            
            if (!response.success) {
                throw new Error(response.error);
            }
            
            // Handle different response formats
            const movies = response.data.movies || response.data;
            
            // Display movies
            if (movies && movies.length > 0) {
                movies.forEach(movie => {
                    // Make sure movie has all required properties
                    const processedMovie = {
                        id: movie.id || movie.movie_id,
                        title: movie.title,
                        poster_path: movie.poster_path,
                        vote_average: movie.vote_average,
                        wr: movie.wr,
                        release_date: movie.release_date,
                        genres: movie.genres || []
                    };
                    topRatedMoviesContainer.innerHTML += createMovieCard(processedMovie);
                });
                
                // Add event listeners to movie cards
                addMovieCardEventListeners(topRatedMoviesContainer);
            } else {
                // Show empty state
                topRatedMoviesContainer.innerHTML = `
                    <div class="empty-state">
                        <i class="fas fa-film"></i>
                        <p>No top rated movies found.</p>
                    </div>
                `;
            }
        } catch (error) {
            console.error('Error loading top rated movies:', error);
            
            // Show error state
            topRatedMoviesContainer.innerHTML = `
                <div class="error-state">
                    <i class="fas fa-exclamation-circle"></i>
                    <p>Failed to load top rated movies. Please try again.</p>
                    <button id="retryTopRated" class="btn btn-primary">Retry</button>
                </div>
            `;
            
            // Add retry button event listener
            document.getElementById('retryTopRated')?.addEventListener('click', loadTopRatedMovies);
        }
    }
    
    // Add event listeners to movie cards
    function addMovieCardEventListeners(container) {
        // Watch later buttons
        const watchLaterButtons = container.querySelectorAll('.watch-later');
        watchLaterButtons.forEach(button => {
            button.addEventListener('click', async (e) => {
                e.preventDefault();
                
                // Check if user is authenticated
                if (!authService.isAuthenticated()) {
                    // Show auth modal
                    const authModal = document.getElementById('authCheckModal');
                    authModal.classList.add('active');
                    
                    // Close modal button
                    const closeModal = authModal.querySelector('.close-modal');
                    closeModal.addEventListener('click', () => {
                        authModal.classList.remove('active');
                    });
                    
                    return;
                }
                
                // Get movie ID
                const movieCard = button.closest('.movie-card');
                const movieId = movieCard.dataset.id;
                
                // Toggle bookmark icon
                const icon = button.querySelector('i');
                icon.classList.toggle('far');
                icon.classList.toggle('fas');
                
                // TODO: Implement watch later functionality
                console.log('Add to watch later:', movieId);
            });
        });
    }
});