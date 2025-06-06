import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import ast
import json
from datetime import datetime
import warnings

warnings.filterwarnings('ignore')

# Thiết lập style cho biểu đồ
plt.rcParams['font.family'] = 'DejaVu Sans'
sns.set_palette("husl")


class MovieDataAnalyzer:
    def __init__(self):
        self.credits = None
        self.keywords = None
        self.links = None
        self.movies = None
        self.ratings = None
        self.merged_data = None

    def load_data(self, file_paths):
        """Tải dữ liệu từ các file CSV"""
        print("🔄 Đang tải dữ liệu...")

        try:
            self.credits = pd.read_csv(file_paths['credits'])
            print(f"✅ Credits: {self.credits.shape[0]} rows, {self.credits.shape[1]} columns")

            self.keywords = pd.read_csv(file_paths['keywords'])
            print(f"✅ Keywords: {self.keywords.shape[0]} rows, {self.keywords.shape[1]} columns")

            self.links = pd.read_csv(file_paths['links'])
            print(f"✅ Links: {self.links.shape[0]} rows, {self.links.shape[1]} columns")

            self.movies = pd.read_csv(file_paths['movies_metadata'])
            print(f"✅ Movies: {self.movies.shape[0]} rows, {self.movies.shape[1]} columns")

            self.ratings = pd.read_csv(file_paths['ratings'])
            print(f"✅ Ratings: {self.ratings.shape[0]} rows, {self.ratings.shape[1]} columns")

        except Exception as e:
            print(f"Loi khi tai du lieu: {str(e)}")
            return False

        return True

    def preprocess_data(self):
        """Tiền xử lý dữ liệu"""
        print("\n🔧 Bắt đầu tiền xử lý dữ liệu...")

        # 1. Xử lý movies_metadata
        print("📊 Xử lý movies_metadata...")

        # Chuyển đổi kiểu dữ liệu
        self.movies['id'] = pd.to_numeric(self.movies['id'], errors='coerce')
        self.movies['budget'] = pd.to_numeric(self.movies['budget'], errors='coerce')
        self.movies['revenue'] = pd.to_numeric(self.movies['revenue'], errors='coerce')
        self.movies['runtime'] = pd.to_numeric(self.movies['runtime'], errors='coerce')
        self.movies['vote_average'] = pd.to_numeric(self.movies['vote_average'], errors='coerce')
        self.movies['vote_count'] = pd.to_numeric(self.movies['vote_count'], errors='coerce')
        self.movies['popularity'] = pd.to_numeric(self.movies['popularity'], errors='coerce')

        # Xử lý ngày tháng
        self.movies['release_date'] = pd.to_datetime(self.movies['release_date'], errors='coerce')
        self.movies['release_year'] = self.movies['release_date'].dt.year
        self.movies['release_month'] = self.movies['release_date'].dt.month

        # Loại bỏ các dòng có id null
        self.movies = self.movies.dropna(subset=['id'])

        # 2. Xử lý genres
        def extract_genres(genre_str):
            try:
                if pd.isna(genre_str):
                    return []
                genres = ast.literal_eval(genre_str)
                return [genre['name'] for genre in genres] if isinstance(genres, list) else []
            except:
                return []

        self.movies['genres_list'] = self.movies['genres'].apply(extract_genres)
        self.movies['primary_genre'] = self.movies['genres_list'].apply(lambda x: x[0] if x else 'Unknown')
        self.movies['genre_count'] = self.movies['genres_list'].apply(len)

        # 3. Xử lý production companies
        def extract_production_companies(companies_str):
            try:
                if pd.isna(companies_str):
                    return []
                companies = ast.literal_eval(companies_str)
                return [company['name'] for company in companies] if isinstance(companies, list) else []
            except:
                return []

        self.movies['production_companies_list'] = self.movies['production_companies'].apply(
            extract_production_companies)
        self.movies['primary_production_company'] = self.movies['production_companies_list'].apply(
            lambda x: x[0] if x else 'Unknown')

        # 4. Xử lý keywords
        print("🔑 Xử lý keywords...")

        def extract_keywords(keywords_str):
            try:
                if pd.isna(keywords_str):
                    return []
                keywords = ast.literal_eval(keywords_str)
                return [keyword['name'] for keyword in keywords] if isinstance(keywords, list) else []
            except:
                return []

        self.keywords['keywords_list'] = self.keywords['keywords'].apply(extract_keywords)
        self.keywords['keyword_count'] = self.keywords['keywords_list'].apply(len)

        # 5. Xử lý credits
        print("🎭 Xử lý credits...")

        def extract_cast_crew(cast_str, crew_str):
            cast_info = {'actors': [], 'directors': [], 'writers': []}

            # Xử lý cast
            try:
                if not pd.isna(cast_str):
                    cast = ast.literal_eval(cast_str)
                    cast_info['actors'] = [actor['name'] for actor in cast[:5]] if cast else []
            except:
                pass

            # Xử lý crew
            try:
                if not pd.isna(crew_str):
                    crew = ast.literal_eval(crew_str)
                    cast_info['directors'] = [person['name'] for person in crew if person['job'] == 'Director']
                    cast_info['writers'] = [person['name'] for person in crew if
                                            person['job'] in ['Writer', 'Screenplay']]
            except:
                pass

            return cast_info

        cast_crew_info = self.credits.apply(lambda row: extract_cast_crew(row['cast'], row['crew']), axis=1)
        self.credits['actors'] = cast_crew_info.apply(lambda x: x['actors'])
        self.credits['directors'] = cast_crew_info.apply(lambda x: x['directors'])
        self.credits['writers'] = cast_crew_info.apply(lambda x: x['writers'])
        self.credits['main_actor'] = self.credits['actors'].apply(lambda x: x[0] if x else 'Unknown')
        self.credits['main_director'] = self.credits['directors'].apply(lambda x: x[0] if x else 'Unknown')

        # 6. Xử lý ratings
        print("⭐ Xử lý ratings...")
        self.ratings['timestamp'] = pd.to_datetime(self.ratings['timestamp'], unit='s')
        self.ratings['rating_year'] = self.ratings['timestamp'].dt.year
        self.ratings['rating_month'] = self.ratings['timestamp'].dt.month

        print("✅ Hoàn thành tiền xử lý dữ liệu!")

    def join_data(self):
        """Join các dataset lại với nhau"""
        print("\n🔗 Đang join dữ liệu...")

        # Bắt đầu với movies làm base
        merged = self.movies.copy()

        # Join với credits
        merged = merged.merge(
            self.credits[['id', 'actors', 'directors', 'writers', 'main_actor', 'main_director']],
            on='id',
            how='left'
        )

        # Join với keywords
        merged = merged.merge(
            self.keywords[['id', 'keywords_list', 'keyword_count']],
            on='id',
            how='left'
        )

        # Join với links (nếu có movieId column)
        if 'movieId' in self.links.columns:
            links_renamed = self.links.rename(columns={'movieId': 'id'})
            merged = merged.merge(links_renamed, on='id', how='left')

        # Tạo aggregated rating data
        rating_stats = self.ratings.groupby('movieId').agg({
            'rating': ['mean', 'count', 'std'],
            'userId': 'nunique'
        }).round(2)

        rating_stats.columns = ['avg_rating', 'rating_count', 'rating_std', 'unique_users']
        rating_stats = rating_stats.reset_index().rename(columns={'movieId': 'id'})

        # Join với rating stats
        merged = merged.merge(rating_stats, on='id', how='left')

        self.merged_data = merged
        print(f"✅ Hoàn thành join dữ liệu! Kích thước final: {merged.shape}")

        return merged

    def data_augmentation(self):
        """Tăng cường dữ liệu với các feature mới"""
        print("\nTang cuong du lieu...")

        if self.merged_data is None:
            print("Chua co du lieu merged!")
            return

        # 1. Tính toán ROI (Return on Investment)
        self.merged_data['roi'] = np.where(
            self.merged_data['budget'] > 0,
            (self.merged_data['revenue'] - self.merged_data['budget']) / self.merged_data['budget'],
            np.nan
        )

        # 2. Phân loại ngân sách
        # Kiểm tra và đảm bảo các giá trị percentile khác nhau
        budget_min = self.merged_data['budget'].min()
        budget_max = self.merged_data['budget'].max()

        # Tạo bins thủ công thay vì dùng percentiles
        bins = [budget_min - 1, budget_min + (budget_max - budget_min) / 3,
                budget_min + 2 * (budget_max - budget_min) / 3, budget_max + 1]

        # Đảm bảo các giá trị bins là duy nhất
        bins = sorted(list(set(bins)))

        # Tạo labels phù hợp với số lượng bins
        if len(bins) == 4:
            labels = ['Low Budget', 'Medium Budget', 'High Budget']
        elif len(bins) == 3:
            labels = ['Low Budget', 'High Budget']
        elif len(bins) == 2:
            labels = ['All Budgets']
        else:
            # Nếu không thể phân loại, bỏ qua bước này
            print("Khong the phan loai budget do khong du du lieu da dang")
            return

        self.merged_data['budget_category'] = pd.cut(
            self.merged_data['budget'],
            bins=bins,
            labels=labels
        )

        # 3. Phân loại popularity
        pop_min = self.merged_data['popularity'].min()
        pop_max = self.merged_data['popularity'].max()

        # Tạo bins thủ công
        pop_bins = [pop_min - 1, pop_min + (pop_max - pop_min) / 3,
                    pop_min + 2 * (pop_max - pop_min) / 3, pop_max + 1]

        # Đảm bảo các giá trị bins là duy nhất
        pop_bins = sorted(list(set(pop_bins)))

        # Tạo labels phù hợp với số lượng bins
        if len(pop_bins) == 4:
            pop_labels = ['Low', 'Medium', 'High']
        elif len(pop_bins) == 3:
            pop_labels = ['Low', 'High']
        elif len(pop_bins) == 2:
            pop_labels = ['All']
        else:
            # Nếu không thể phân loại, bỏ qua bước này
            print("Khong the phan loai popularity do khong du du lieu da dang")
            return

        self.merged_data['popularity_category'] = pd.cut(
            self.merged_data['popularity'],
            bins=pop_bins,
            labels=pop_labels
        )

        # 4. Era phim
        # Đảm bảo các giá trị bins là duy nhất
        era_bins = [0, 1980, 2000, 2010, 2025]
        era_bins = sorted(list(set(era_bins)))

        # Tạo labels phù hợp với số lượng bins
        if len(era_bins) == 5:
            era_labels = ['Classic', '80s-90s', '2000s', '2010s+']
        elif len(era_bins) == 4:
            era_labels = ['Classic', '80s-90s', '2000s+']
        elif len(era_bins) == 3:
            era_labels = ['Classic', 'Modern']
        elif len(era_bins) == 2:
            era_labels = ['All Eras']
        else:
            # Nếu không thể phân loại, bỏ qua bước này
            print("Khong the phan loai era do khong du du lieu da dang")
            return

        self.merged_data['era'] = pd.cut(
            self.merged_data['release_year'],
            bins=era_bins,
            labels=era_labels
        )

        # 5. Success score (kết hợp nhiều yếu tố)
        # Chuẩn hóa các metrics
        for col in ['vote_average', 'popularity', 'revenue', 'vote_count']:
            if col in self.merged_data.columns:
                self.merged_data[f'{col}_normalized'] = (
                                                                self.merged_data[col] - self.merged_data[col].min()
                                                        ) / (self.merged_data[col].max() - self.merged_data[col].min())

        # Tính success score
        success_components = ['vote_average_normalized', 'popularity_normalized', 'revenue_normalized']
        self.merged_data['success_score'] = self.merged_data[success_components].mean(axis=1)

        # 6. Seasonal release pattern
        season_map = {12: 'Winter', 1: 'Winter', 2: 'Winter',
                      3: 'Spring', 4: 'Spring', 5: 'Spring',
                      6: 'Summer', 7: 'Summer', 8: 'Summer',
                      9: 'Fall', 10: 'Fall', 11: 'Fall'}
        self.merged_data['release_season'] = self.merged_data['release_month'].map(season_map)

        print("✅ Hoàn thành tăng cường dữ liệu!")

    def analyze_data(self):
        """Phân tích dữ liệu chi tiết"""
        print("\n📊 Bắt đầu phân tích dữ liệu...")

        if self.merged_data is None:
            print("❌ Chưa có dữ liệu để phân tích!")
            return

        # 1. Thống kê tổng quan
        print("\n📈 THỐNG KÊ TỔNG QUAN:")
        print(f"- Tổng số phim: {len(self.merged_data):,}")
        print(f"- Số phim có rating: {self.merged_data['avg_rating'].notna().sum():,}")
        print(
            f"- Khoảng thời gian: {self.merged_data['release_year'].min():.0f} - {self.merged_data['release_year'].max():.0f}")
        print(f"- Tổng doanh thu: ${self.merged_data['revenue'].sum():,.0f}")
        print(f"- Rating trung bình: {self.merged_data['avg_rating'].mean():.2f}")

        # 2. Top genres
        all_genres = []
        for genres_list in self.merged_data['genres_list'].dropna():
            all_genres.extend(genres_list)

        genre_counts = pd.Series(all_genres).value_counts().head(10)
        print(f"\n🎬 TOP 10 THỂ LOẠI PHỔ BIẾN:")
        for genre, count in genre_counts.items():
            print(f"- {genre}: {count} phim")

        # 3. Phân tích theo thập kỷ
        decade_analysis = self.merged_data.groupby('era').agg({
            'id': 'count',
            'budget': 'mean',
            'revenue': 'mean',
            'vote_average': 'mean',
            'runtime': 'mean'
        }).round(2)
        decade_analysis.columns = ['Số phim', 'Ngân sách TB', 'Doanh thu TB', 'Rating TB', 'Thời lượng TB']
        print(f"\n📅 PHÂN TÍCH THEO THỜI ĐẠI:")
        print(decade_analysis)

        # 4. Top directors và actors
        top_directors = self.merged_data['main_director'].value_counts().head(10)
        top_actors = self.merged_data['main_actor'].value_counts().head(10)

        print(f"\n🎭 TOP 10 ĐẠO DIỄN:")
        for director, count in top_directors.items():
            if director != 'Unknown':
                print(f"- {director}: {count} phim")

        # 5. Correlation analysis
        numeric_cols = ['budget', 'revenue', 'runtime', 'vote_average', 'vote_count', 'popularity', 'avg_rating',
                        'success_score']
        correlation_matrix = self.merged_data[numeric_cols].corr()

        print(f"\n🔍 MỐI TƯƠNG QUAN MẠNH NHẤT:")
        # Tìm correlation cao nhất (loại trừ diagonal)
        corr_pairs = []
        for i in range(len(correlation_matrix.columns)):
            for j in range(i + 1, len(correlation_matrix.columns)):
                corr_value = correlation_matrix.iloc[i, j]
                if not pd.isna(corr_value):
                    corr_pairs.append((correlation_matrix.columns[i], correlation_matrix.columns[j], abs(corr_value)))

        corr_pairs.sort(key=lambda x: x[2], reverse=True)
        for col1, col2, corr in corr_pairs[:5]:
            print(f"- {col1} vs {col2}: {corr:.3f}")

        return {
            'overview': decade_analysis,
            'genres': genre_counts,
            'directors': top_directors,
            'correlation': correlation_matrix
        }

    def create_visualizations(self):
        """Tạo các biểu đồ trực quan"""
        print("\n📊 Tạo visualizations...")

        if self.merged_data is None:
            print("❌ Chưa có dữ liệu để vẽ biểu đồ!")
            return

        # Thiết lập figure với multiple subplots
        fig = plt.figure(figsize=(20, 24))

        # 1. Distribution of ratings
        plt.subplot(4, 3, 1)
        self.merged_data['vote_average'].hist(bins=30, alpha=0.7, color='skyblue', edgecolor='black')
        plt.title('Phân Bố Điểm Rating', fontsize=14, fontweight='bold')
        plt.xlabel('Điểm Rating')
        plt.ylabel('Số Phim')
        plt.grid(True, alpha=0.3)

        # 2. Revenue vs Budget
        plt.subplot(4, 3, 2)
        valid_budget_revenue = self.merged_data.dropna(subset=['budget', 'revenue'])
        valid_budget_revenue = valid_budget_revenue[
            (valid_budget_revenue['budget'] > 0) & (valid_budget_revenue['revenue'] > 0)]

        plt.scatter(valid_budget_revenue['budget'], valid_budget_revenue['revenue'],
                    alpha=0.6, s=30, c='coral')
        plt.plot([0, valid_budget_revenue['budget'].max()], [0, valid_budget_revenue['budget'].max()],
                 'r--', alpha=0.8, linewidth=2, label='Break-even line')
        plt.xlabel('Ngân Sách ($)')
        plt.ylabel('Doanh Thu ($)')
        plt.title('Doanh Thu vs Ngân Sách', fontsize=14, fontweight='bold')
        plt.legend()
        plt.grid(True, alpha=0.3)

        # 3. Top genres
        plt.subplot(4, 3, 3)
        all_genres = []
        for genres_list in self.merged_data['genres_list'].dropna():
            all_genres.extend(genres_list)
        genre_counts = pd.Series(all_genres).value_counts().head(10)

        bars = plt.bar(range(len(genre_counts)), genre_counts.values, color='lightgreen')
        plt.title('Top 10 Thể Loại Phim', fontsize=14, fontweight='bold')
        plt.xlabel('Thể Loại')
        plt.ylabel('Số Phim')
        plt.xticks(range(len(genre_counts)), genre_counts.index, rotation=45, ha='right')

        # Thêm giá trị lên top của mỗi cột
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width() / 2., height,
                     f'{int(height)}', ha='center', va='bottom')

        # 4. Movies by era
        plt.subplot(4, 3, 4)
        era_counts = self.merged_data['era'].value_counts()
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
        wedges, texts, autotexts = plt.pie(era_counts.values, labels=era_counts.index, autopct='%1.1f%%',
                                           startangle=90, colors=colors)
        plt.title('Phân Bố Phim Theo Thời Đại', fontsize=14, fontweight='bold')

        # 5. Success score distribution
        plt.subplot(4, 3, 5)
        self.merged_data['success_score'].hist(bins=30, alpha=0.7, color='gold', edgecolor='black')
        plt.title('Phân Bố Success Score', fontsize=14, fontweight='bold')
        plt.xlabel('Success Score')
        plt.ylabel('Số Phim')
        plt.grid(True, alpha=0.3)

        # 6. Runtime distribution
        plt.subplot(4, 3, 6)
        runtime_data = self.merged_data['runtime'].dropna()
        runtime_data = runtime_data[(runtime_data > 60) & (runtime_data < 300)]  # Lọc outliers
        plt.hist(runtime_data, bins=30, alpha=0.7, color='mediumpurple', edgecolor='black')
        plt.title('Phân Bố Thời Lượng Phim', fontsize=14, fontweight='bold')
        plt.xlabel('Thời Lượng (phút)')
        plt.ylabel('Số Phim')
        plt.grid(True, alpha=0.3)

        # 7. Release pattern by season
        plt.subplot(4, 3, 7)
        season_counts = self.merged_data['release_season'].value_counts()
        bars = plt.bar(season_counts.index, season_counts.values,
                       color=['#87CEEB', '#98FB98', '#F0E68C', '#DDA0DD'])
        plt.title('Phim Phát Hành Theo Mùa', fontsize=14, fontweight='bold')
        plt.xlabel('Mùa')
        plt.ylabel('Số Phim')

        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width() / 2., height,
                     f'{int(height)}', ha='center', va='bottom')

        # 8. Correlation heatmap
        plt.subplot(4, 3, 8)
        numeric_cols = ['budget', 'revenue', 'vote_average', 'popularity', 'runtime']
        corr_data = self.merged_data[numeric_cols].corr()

        im = plt.imshow(corr_data, cmap='coolwarm', aspect='auto', vmin=-1, vmax=1)
        plt.colorbar(im)
        plt.title('Ma Trận Tương Quan', fontsize=14, fontweight='bold')
        plt.xticks(range(len(numeric_cols)), numeric_cols, rotation=45, ha='right')
        plt.yticks(range(len(numeric_cols)), numeric_cols)

        # Thêm giá trị correlation
        for i in range(len(numeric_cols)):
            for j in range(len(numeric_cols)):
                plt.text(j, i, f'{corr_data.iloc[i, j]:.2f}',
                         ha='center', va='center', color='white', fontweight='bold')

        # 9. Revenue by budget category
        plt.subplot(4, 3, 9)
        budget_revenue = self.merged_data.groupby('budget_category')['revenue'].mean().dropna()
        bars = plt.bar(budget_revenue.index, budget_revenue.values, color=['#FF7F7F', '#87CEEB', '#98FB98'])
        plt.title('Doanh Thu Trung Bình Theo Loại Ngân Sách', fontsize=14, fontweight='bold')
        plt.xlabel('Loại Ngân Sách')
        plt.ylabel('Doanh Thu Trung Bình ($)')
        plt.xticks(rotation=45)

        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width() / 2., height,
                     f'${height / 1e6:.1f}M', ha='center', va='bottom')

        # 10. Top directors (top 10)
        plt.subplot(4, 3, 10)
        top_directors = self.merged_data['main_director'].value_counts().head(10)
        top_directors = top_directors[top_directors.index != 'Unknown'][:8]  # Loại bỏ Unknown và lấy top 8

        bars = plt.barh(range(len(top_directors)), top_directors.values, color='lightcoral')
        plt.title('Top Đạo Diễn (Số Phim)', fontsize=14, fontweight='bold')
        plt.xlabel('Số Phim')
        plt.yticks(range(len(top_directors)), top_directors.index)

        for i, bar in enumerate(bars):
            width = bar.get_width()
            plt.text(width, bar.get_y() + bar.get_height() / 2.,
                     f'{int(width)}', ha='left', va='center')

        # 11. ROI Distribution
        plt.subplot(4, 3, 11)
        roi_data = self.merged_data['roi'].dropna()
        roi_data = roi_data[(roi_data > -1) & (roi_data < 10)]  # Lọc outliers
        plt.hist(roi_data, bins=30, alpha=0.7, color='orange', edgecolor='black')
        plt.title('Phân Bố ROI (Return on Investment)', fontsize=14, fontweight='bold')
        plt.xlabel('ROI')
        plt.ylabel('Số Phim')
        plt.grid(True, alpha=0.3)

        # 12. Rating trends over years
        plt.subplot(4, 3, 12)
        yearly_rating = self.merged_data.groupby('release_year')['vote_average'].mean()
        yearly_rating = yearly_rating[(yearly_rating.index >= 1980) & (yearly_rating.index <= 2020)]

        plt.plot(yearly_rating.index, yearly_rating.values, marker='o', linewidth=2, markersize=4, color='darkblue')
        plt.title('Xu Hướng Rating Theo Năm', fontsize=14, fontweight='bold')
        plt.xlabel('Năm')
        plt.ylabel('Rating Trung Bình')
        plt.grid(True, alpha=0.3)

        plt.tight_layout(pad=3.0)
        plt.show()

        # Biểu đồ bổ sung: Top movies by different metrics
        fig2, axes = plt.subplots(2, 2, figsize=(16, 12))

        # Top movies by revenue
        top_revenue = self.merged_data.nlargest(10, 'revenue')[['title', 'revenue']].dropna()
        axes[0, 0].barh(range(len(top_revenue)), top_revenue['revenue'], color='gold')
        axes[0, 0].set_title('Top 10 Phim Có Doanh Thu Cao Nhất', fontweight='bold')
        axes[0, 0].set_xlabel('Doanh Thu ($)')
        axes[0, 0].set_yticks(range(len(top_revenue)))
        axes[0, 0].set_yticklabels(top_revenue['title'], fontsize=8)

        # Top movies by rating
        top_rating = self.merged_data[(self.merged_data['vote_count'] >= 100)].nlargest(10, 'vote_average')[
            ['title', 'vote_average']].dropna()
        axes[0, 1].barh(range(len(top_rating)), top_rating['vote_average'], color='lightgreen')
        axes[0, 1].set_title('Top 10 Phim Có Rating Cao Nhất', fontweight='bold')
        axes[0, 1].set_xlabel('Rating')
        axes[0, 1].set_yticks(range(len(top_rating)))
        axes[0, 1].set_yticklabels(top_rating['title'], fontsize=8)

        # Budget vs Revenue scatter with trend line
        budget_revenue_clean = self.merged_data.dropna(subset=['budget', 'revenue'])
        budget_revenue_clean = budget_revenue_clean[(budget_revenue_clean['budget'] > 1000000) &
                                                    (budget_revenue_clean['revenue'] > 1000000)]

        x = budget_revenue_clean['budget']
        y = budget_revenue_clean['revenue']
        axes[1, 0].scatter(x, y, alpha=0.6, s=30, c='purple')

        # Thêm trend line
        z = np.polyfit(x, y, 1)
        p = np.poly1d(z)
        axes[1, 0].plot(x, p(x), "r--", alpha=0.8, linewidth=2)

        axes[1, 0].set_title('Mối Quan Hệ Ngân Sách - Doanh Thu', fontweight='bold')
        axes[1, 0].set_xlabel('Ngân Sách ($)')
        axes[1, 0].set_ylabel('Doanh Thu ($)')
        axes[1, 0].grid(True, alpha=0.3)

        # Popular genres over time
        genre_year_data = []
        for idx, row in self.merged_data.dropna(subset=['genres_list', 'release_year']).iterrows():
            if row['release_year'] >= 2000:
                for genre in row['genres_list']:
                    genre_year_data.append({'year': row['release_year'], 'genre': genre})

        genre_year_df = pd.DataFrame(genre_year_data)
        top_genres = genre_year_df['genre'].value_counts().head(5).index

        for genre in top_genres:
            genre_data = genre_year_df[genre_year_df['genre'] == genre]
            yearly_counts = genre_data.groupby('year').size()
            axes[1, 1].plot(yearly_counts.index, yearly_counts.values, marker='o', label=genre, linewidth=2)

        axes[1, 1].set_title('Xu Hướng Thể Loại Phim Qua Thời Gian (2000+)', fontweight='bold')
        axes[1, 1].set_xlabel('Năm')
        axes[1, 1].set_ylabel('Số Phim')
        axes[1, 1].legend()
        axes[1, 1].grid(True, alpha=0.3)

        plt.tight_layout()
        plt.show()

        print("✅ Hoàn thành tạo visualizations!")

    def generate_insights(self):
        """Tạo insights và recommendations"""
        print("\nINSIGHTS VA KHUYEN NGHI:")

        if self.merged_data is None:
            print("❌ Chưa có dữ liệu để phân tích!")
            return

        insights = []

        # 1. Budget vs Revenue insight
        profitable_movies = self.merged_data[self.merged_data['roi'] > 0]
        if len(profitable_movies) > 0:
            avg_roi = profitable_movies['roi'].mean()
            insights.append(f"📈 ROI trung bình của các phim có lời: {avg_roi:.2f} ({avg_roi * 100:.1f}%)")

        # 2. Genre performance
        genre_performance = {}
        for idx, row in self.merged_data.dropna(subset=['genres_list', 'revenue']).iterrows():
            for genre in row['genres_list']:
                if genre not in genre_performance:
                    genre_performance[genre] = []
                genre_performance[genre].append(row['revenue'])

        avg_revenue_by_genre = {genre: np.mean(revenues) for genre, revenues in genre_performance.items() if
                                len(revenues) >= 10}
        best_genre = max(avg_revenue_by_genre, key=avg_revenue_by_genre.get) if avg_revenue_by_genre else "N/A"
        insights.append(f"🎬 Thể loại có doanh thu cao nhất: {best_genre}")

        # 3. Seasonal insight
        seasonal_revenue = self.merged_data.groupby('release_season')['revenue'].mean().dropna()
        if len(seasonal_revenue) > 0:
            best_season = seasonal_revenue.idxmax()
            insights.append(f"Mua phat hanh tot nhat: {best_season}")

        # 4. Rating vs Commercial success
        high_rating_high_revenue = self.merged_data[
            (self.merged_data['vote_average'] >= 7.5) &
            (self.merged_data['revenue'] >= self.merged_data['revenue'].quantile(0.75))
            ]
        insights.append(f"⭐ Số phim vừa có rating cao (≥7.5) vừa có doanh thu cao: {len(high_rating_high_revenue)}")

        # 5. Runtime insight
        try:
            # Tạo bins thủ công cho runtime
            runtime_min = self.merged_data['runtime'].min()
            runtime_max = self.merged_data['runtime'].max()
            runtime_step = (runtime_max - runtime_min) / 5

            runtime_bins = [runtime_min + i * runtime_step for i in range(6)]
            runtime_bins = sorted(list(set(runtime_bins)))

            if len(runtime_bins) >= 2:
                optimal_runtime = self.merged_data.groupby(pd.cut(self.merged_data['runtime'], bins=runtime_bins))[
                    'revenue'].mean()
                if len(optimal_runtime.dropna()) > 0:
                    best_runtime_range = optimal_runtime.idxmax()
                    insights.append(f"⏱️ Khoảng thời lượng có doanh thu tốt nhất: {best_runtime_range}")
        except Exception as e:
            print(f"Khong the phan tich runtime: {str(e)}")

        # 6. Budget category insight
        budget_success = self.merged_data.groupby('budget_category')['success_score'].mean().dropna()
        if len(budget_success) > 0:
            best_budget_cat = budget_success.idxmax()
            insights.append(f"💰 Loại ngân sách có success score cao nhất: {best_budget_cat}")

        for insight in insights:
            print(insight)

        # Recommendations
        print(f"\n🎯 KHUYẾN NGHỊ:")
        print("1. 📊 Đầu tư vào các thể loại phim có ROI cao như Comedy, Horror")
        print("2. 🎭 Hợp tác với các đạo diễn và diễn viên có track record tốt")
        print("3. 📅 Cân nhắc thời điểm phát hành theo mùa để tối ưu doanh thu")
        print("4. ⚖️ Cân bằng giữa chất lượng (rating) và tính thương mại (revenue)")
        print("5. 🎬 Tối ưu thời lượng phim trong khoảng 90-120 phút")

        return insights

    def correlation_analysis(self):
        """Phân tích chi tiết mối tương quan giữa các biến"""
        print("\n🔍 PHÂN TÍCH TƯƠNG QUAN CHI TIẾT")
        print("=" * 50)

        if self.merged_data is None:
            print("❌ Chưa có dữ liệu để phân tích!")
            return

        # 1. Chọn các biến số để phân tích correlation
        numeric_vars = [
            'budget', 'revenue', 'runtime', 'vote_average', 'vote_count',
            'popularity', 'avg_rating', 'rating_count', 'unique_users',
            'success_score', 'roi', 'keyword_count', 'genre_count', 'release_year'
        ]

        # Lọc các cột tồn tại
        available_vars = [var for var in numeric_vars if var in self.merged_data.columns]
        correlation_data = self.merged_data[available_vars].copy()

        # Loại bỏ outliers để có correlation chính xác hơn
        for col in ['budget', 'revenue', 'roi']:
            if col in correlation_data.columns:
                q1 = correlation_data[col].quantile(0.01)
                q99 = correlation_data[col].quantile(0.99)
                correlation_data[col] = correlation_data[col].clip(lower=q1, upper=q99)

        # Tính correlation matrix
        corr_matrix = correlation_data.corr()

        # 2. Tìm correlations mạnh nhất
        print("🔥 TOP 15 TƯƠNG QUAN MẠNH NHẤT:")
        print("-" * 50)

        corr_pairs = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i + 1, len(corr_matrix.columns)):
                corr_value = corr_matrix.iloc[i, j]
                if not pd.isna(corr_value):
                    corr_pairs.append({
                        'var1': corr_matrix.columns[i],
                        'var2': corr_matrix.columns[j],
                        'correlation': corr_value,
                        'abs_correlation': abs(corr_value),
                        'relationship': 'Tương quan thuận' if corr_value > 0 else 'Tương quan nghịch'
                    })

        # Sort by absolute correlation
        corr_pairs_df = pd.DataFrame(corr_pairs)
        corr_pairs_df = corr_pairs_df.sort_values('abs_correlation', ascending=False)

        for idx, row in corr_pairs_df.head(15).iterrows():
            strength = "Rất mạnh" if row['abs_correlation'] >= 0.7 else \
                "Mạnh" if row['abs_correlation'] >= 0.5 else \
                    "Trung bình" if row['abs_correlation'] >= 0.3 else "Yếu"

            print(f"{row['var1']:15} ↔ {row['var2']:15} | "
                  f"r = {row['correlation']:6.3f} | {strength:8} | {row['relationship']}")

        # 3. Phân tích theo nhóm biến
        print(f"\n📊 PHÂN TÍCH THEO NHÓM BIẾN:")
        print("-" * 50)

        # Nhóm Financial metrics
        financial_vars = ['budget', 'revenue', 'roi']
        financial_vars = [v for v in financial_vars if v in available_vars]
        if len(financial_vars) >= 2:
            print("💰 FINANCIAL METRICS:")
            financial_corr = correlation_data[financial_vars].corr()
            for i in range(len(financial_vars)):
                for j in range(i + 1, len(financial_vars)):
                    corr_val = financial_corr.iloc[i, j]
                    print(f"   {financial_vars[i]} ↔ {financial_vars[j]}: {corr_val:.3f}")

        # Nhóm Quality metrics
        quality_vars = ['vote_average', 'avg_rating', 'vote_count', 'rating_count']
        quality_vars = [v for v in quality_vars if v in available_vars]
        if len(quality_vars) >= 2:
            print("\n⭐ QUALITY METRICS:")
            quality_corr = correlation_data[quality_vars].corr()
            for i in range(len(quality_vars)):
                for j in range(i + 1, len(quality_vars)):
                    corr_val = quality_corr.iloc[i, j]
                    print(f"   {quality_vars[i]} ↔ {quality_vars[j]}: {corr_val:.3f}")

        # Nhóm Popularity metrics
        popularity_vars = ['popularity', 'vote_count', 'unique_users', 'rating_count']
        popularity_vars = [v for v in popularity_vars if v in available_vars]
        if len(popularity_vars) >= 2:
            print("\n🔥 POPULARITY METRICS:")
            pop_corr = correlation_data[popularity_vars].corr()
            for i in range(len(popularity_vars)):
                for j in range(i + 1, len(popularity_vars)):
                    corr_val = pop_corr.iloc[i, j]
                    print(f"   {popularity_vars[i]} ↔ {popularity_vars[j]}: {corr_val:.3f}")

        # 4. Cross-group correlations (quan trọng nhất)
        print(f"\n🎯 TƯƠNG QUAN QUAN TRỌNG (Cross-group):")
        print("-" * 50)

        important_pairs = [
            ('budget', 'revenue', 'Ngân sách → Doanh thu'),
            ('budget', 'vote_average', 'Ngân sách → Chất lượng'),
            ('vote_average', 'popularity', 'Chất lượng → Độ nổi tiếng'),
            ('runtime', 'vote_average', 'Thời lượng → Rating'),
            ('popularity', 'revenue', 'Độ nổi tiếng → Doanh thu'),
            ('success_score', 'revenue', 'Success Score → Doanh thu'),
            ('genre_count', 'popularity', 'Số thể loại → Popularity'),
            ('keyword_count', 'popularity', 'Số keywords → Popularity'),
            ('release_year', 'budget', 'Năm phát hành → Ngân sách'),
            ('vote_count', 'revenue', 'Số vote → Doanh thu')
        ]

        for var1, var2, description in important_pairs:
            if var1 in available_vars and var2 in available_vars:
                corr_val = correlation_data[var1].corr(correlation_data[var2])
                if not pd.isna(corr_val):
                    interpretation = self._interpret_correlation(corr_val)
                    print(f"{description:25}: {corr_val:6.3f} ({interpretation})")

        # 5. Tạo visualization cho correlation analysis
        self._create_correlation_visualizations(correlation_data, corr_matrix)

        # 6. Statistical significance testing
        print(f"\n📈 KIỂM ĐỊNH Ý NGHĨA THỐNG KÊ (p < 0.05):")
        print("-" * 50)

        from scipy.stats import pearsonr
        significant_correlations = []

        for idx, row in corr_pairs_df.head(10).iterrows():
            var1_data = correlation_data[row['var1']].dropna()
            var2_data = correlation_data[row['var2']].dropna()

            # Lấy intersection của indices
            common_idx = var1_data.index.intersection(var2_data.index)
            if len(common_idx) > 10:  # Cần ít nhất 10 data points
                try:
                    corr_coef, p_value = pearsonr(var1_data[common_idx], var2_data[common_idx])
                    if p_value < 0.05:
                        significant_correlations.append({
                            'pair': f"{row['var1']} ↔ {row['var2']}",
                            'correlation': corr_coef,
                            'p_value': p_value,
                            'sample_size': len(common_idx)
                        })
                except:
                    continue

        for corr in significant_correlations[:8]:
            significance = "***" if corr['p_value'] < 0.001 else "**" if corr['p_value'] < 0.01 else "*"
            print(f"{corr['pair']:30} | r = {corr['correlation']:6.3f} | "
                  f"p = {corr['p_value']:.4f} {significance} | n = {corr['sample_size']}")

        # 7. Correlation insights
        print(f"\n💡 INSIGHTS TỪ PHÂN TÍCH TƯƠNG QUAN:")
        print("-" * 50)

        insights = self._generate_correlation_insights(corr_pairs_df, available_vars)
        for insight in insights:
            print(f"• {insight}")

        return {
            'correlation_matrix': corr_matrix,
            'top_correlations': corr_pairs_df,
            'significant_correlations': significant_correlations,
            'insights': insights
        }

    def _interpret_correlation(self, corr_value):
        """Diễn giải mức độ tương quan"""
        abs_corr = abs(corr_value)
        if abs_corr >= 0.8:
            strength = "Rất mạnh"
        elif abs_corr >= 0.6:
            strength = "Mạnh"
        elif abs_corr >= 0.4:
            strength = "Trung bình"
        elif abs_corr >= 0.2:
            strength = "Yếu"
        else:
            strength = "Rất yếu"

        direction = "thuận" if corr_value > 0 else "nghịch"
        return f"{strength}, {direction}"

    def _create_correlation_visualizations(self, correlation_data, corr_matrix):
        """Tạo các biểu đồ cho correlation analysis"""

        fig, axes = plt.subplots(2, 2, figsize=(16, 12))

        # 1. Enhanced Correlation Heatmap
        mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
        im1 = axes[0, 0].imshow(corr_matrix.values, cmap='RdBu_r', aspect='auto', vmin=-1, vmax=1)

        # Thêm colorbar
        cbar1 = plt.colorbar(im1, ax=axes[0, 0], shrink=0.8)
        cbar1.set_label('Correlation Coefficient', rotation=270, labelpad=20)

        axes[0, 0].set_title('Ma Trận Tương Quan (Correlation Matrix)', fontsize=14, fontweight='bold', pad=20)
        axes[0, 0].set_xticks(range(len(corr_matrix.columns)))
        axes[0, 0].set_yticks(range(len(corr_matrix.columns)))
        axes[0, 0].set_xticklabels(corr_matrix.columns, rotation=45, ha='right')
        axes[0, 0].set_yticklabels(corr_matrix.columns)

        # Thêm text annotations
        for i in range(len(corr_matrix.columns)):
            for j in range(len(corr_matrix.columns)):
                if not mask[i, j]:  # Chỉ hiển thị nửa dưới của matrix
                    text_color = 'white' if abs(corr_matrix.iloc[i, j]) > 0.5 else 'black'
                    axes[0, 0].text(j, i, f'{corr_matrix.iloc[i, j]:.2f}',
                                    ha='center', va='center', color=text_color, fontweight='bold')

        # 2. Scatter plot cho top correlation
        if 'budget' in correlation_data.columns and 'revenue' in correlation_data.columns:
            budget_revenue = correlation_data[['budget', 'revenue']].dropna()
            budget_revenue = budget_revenue[(budget_revenue['budget'] > 0) & (budget_revenue['revenue'] > 0)]

            if len(budget_revenue) > 0:
                x = budget_revenue['budget']
                y = budget_revenue['revenue']
                axes[0, 1].scatter(x, y, alpha=0.6, s=30, c='purple', edgecolors='white', linewidth=0.5)

                # Thêm regression line
                z = np.polyfit(x, y, 1)
                p = np.poly1d(z)
                axes[0, 1].plot(x, p(x), "r--", alpha=0.8, linewidth=2, label=f'Trend Line')

                # Tính và hiển thị R²
                correlation_coef = x.corr(y)
                r_squared = correlation_coef ** 2

                axes[0, 1].set_title(f'Budget vs Revenue\n(r = {correlation_coef:.3f}, R² = {r_squared:.3f})',
                                     fontsize=14, fontweight='bold')
                axes[0, 1].set_xlabel('Budget ($)')
                axes[0, 1].set_ylabel('Revenue ($)')
                axes[0, 1].grid(True, alpha=0.3)
                axes[0, 1].legend()

        # 3. Correlation strength distribution
        corr_values = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i + 1, len(corr_matrix.columns)):
                if not pd.isna(corr_matrix.iloc[i, j]):
                    corr_values.append(abs(corr_matrix.iloc[i, j]))

        axes[1, 0].hist(corr_values, bins=20, alpha=0.7, color='skyblue', edgecolor='black')
        axes[1, 0].axvline(np.mean(corr_values), color='red', linestyle='--', linewidth=2,
                           label=f'Mean = {np.mean(corr_values):.3f}')
        axes[1, 0].set_title('Phân Bố Mức Độ Tương Quan', fontsize=14, fontweight='bold')
        axes[1, 0].set_xlabel('|Correlation Coefficient|')
        axes[1, 0].set_ylabel('Frequency')
        axes[1, 0].legend()
        axes[1, 0].grid(True, alpha=0.3)

        # 4. Top correlations bar chart
        # Lấy top 10 correlations
        corr_pairs = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i + 1, len(corr_matrix.columns)):
                if not pd.isna(corr_matrix.iloc[i, j]):
                    corr_pairs.append({
                        'pair': f"{corr_matrix.columns[i][:8]}↔{corr_matrix.columns[j][:8]}",
                        'correlation': corr_matrix.iloc[i, j]
                    })

        corr_pairs_df = pd.DataFrame(corr_pairs)
        top_corr = corr_pairs_df.nlargest(8, 'correlation')

        colors = ['green' if x > 0 else 'red' for x in top_corr['correlation']]
        bars = axes[1, 1].barh(range(len(top_corr)), top_corr['correlation'], color=colors, alpha=0.7)
        axes[1, 1].set_title('Top 8 Tương Quan Mạnh Nhất', fontsize=14, fontweight='bold')
        axes[1, 1].set_xlabel('Correlation Coefficient')
        axes[1, 1].set_yticks(range(len(top_corr)))
        axes[1, 1].set_yticklabels(top_corr['pair'], fontsize=10)
        axes[1, 1].grid(True, alpha=0.3, axis='x')

        # Thêm values trên bars
        for i, bar in enumerate(bars):
            width = bar.get_width()
            axes[1, 1].text(width + (0.01 if width > 0 else -0.01), bar.get_y() + bar.get_height() / 2.,
                            f'{width:.3f}', ha='left' if width > 0 else 'right', va='center', fontweight='bold')

        plt.tight_layout(pad=3.0)
        plt.show()

        print("✅ Hoàn thành tạo correlation visualizations!")

    def _generate_correlation_insights(self, corr_pairs_df, available_vars):
        """Tạo insights từ phân tích correlation"""
        insights = []

        # Top positive correlation
        top_positive = corr_pairs_df[corr_pairs_df['correlation'] > 0].iloc[0]
        insights.append(
            f"Tương quan thuận mạnh nhất: {top_positive['var1']} và {top_positive['var2']} (r = {top_positive['correlation']:.3f})")

        # Top negative correlation
        top_negative = corr_pairs_df[corr_pairs_df['correlation'] < 0].head(1)
        if len(top_negative) > 0:
            neg_row = top_negative.iloc[0]
            insights.append(
                f"Tương quan nghịch mạnh nhất: {neg_row['var1']} và {neg_row['var2']} (r = {neg_row['correlation']:.3f})")

        # Business insights
        if 'budget' in available_vars and 'revenue' in available_vars:
            budget_revenue_corr = corr_pairs_df[
                ((corr_pairs_df['var1'] == 'budget') & (corr_pairs_df['var2'] == 'revenue')) |
                ((corr_pairs_df['var1'] == 'revenue') & (corr_pairs_df['var2'] == 'budget'))
                ]
            if len(budget_revenue_corr) > 0:
                corr_val = budget_revenue_corr.iloc[0]['correlation']
                if corr_val > 0.5:
                    insights.append("Ngân sách cao thường dẫn đến doanh thu cao - chiến lược đầu tư tích cực")
                elif corr_val < 0.3:
                    insights.append("Mối quan hệ ngân sách-doanh thu yếu - cần tối ưu hiệu quả chi tiêu")

        if 'vote_average' in available_vars and 'popularity' in available_vars:
            quality_pop_corr = corr_pairs_df[
                ((corr_pairs_df['var1'] == 'vote_average') & (corr_pairs_df['var2'] == 'popularity')) |
                ((corr_pairs_df['var1'] == 'popularity') & (corr_pairs_df['var2'] == 'vote_average'))
                ]
            if len(quality_pop_corr) > 0:
                corr_val = quality_pop_corr.iloc[0]['correlation']
                if corr_val > 0.4:
                    insights.append("Chất lượng phim tương quan tốt với độ nổi tiếng - focus vào quality content")
                else:
                    insights.append("Chất lượng không đảm bảo popularity - cần chiến lược marketing mạnh")

        # Số lượng correlations mạnh
        strong_corr_count = len(corr_pairs_df[corr_pairs_df['abs_correlation'] >= 0.6])
        total_pairs = len(corr_pairs_df)
        insights.append(f"Có {strong_corr_count}/{total_pairs} cặp biến có tương quan mạnh (≥0.6)")

        return insights

    def export_results(self, filename="movie_analysis_results.csv"):
        """Xuất kết quả phân tích"""
        if self.merged_data is not None:
            # Chọn các cột quan trọng để export
            export_cols = [
                'id', 'title', 'release_year', 'primary_genre', 'budget', 'revenue',
                'vote_average', 'popularity', 'runtime', 'main_director', 'main_actor',
                'success_score', 'roi', 'budget_category', 'era', 'release_season'
            ]

            export_data = self.merged_data[export_cols].copy()
            export_data.to_csv(filename, index=False, encoding='utf-8')
            print(f"✅ Đã xuất kết quả ra file: {filename}")
        else:
            print("❌ Không có dữ liệu để xuất!")

    def run_full_analysis(self, file_paths):
        """Chạy toàn bộ pipeline phân tích"""
        print("BẮT ĐẦU PHÂN TÍCH DỮ LIỆU PHIM")
        print("=" * 50)

        # Load data
        if not self.load_data(file_paths):
            return False

        # Preprocess
        self.preprocess_data()

        # Join data
        self.join_data()

        # Data augmentation
        self.data_augmentation()

        # Analysis
        analysis_results = self.analyze_data()

        # Visualizations
        self.create_visualizations()

        # Correlation Analysis (NEW!)
        correlation_results = self.correlation_analysis()

        # Generate insights
        self.generate_insights()

        # Export results
        self.export_results()

        print("\n" + "=" * 50)
        print("🎉 HOÀN THÀNH PHÂN TÍCH!")

        return True


# CÁCH SỬ DỤNG
def main():
    """Hàm main để chạy phân tích"""

    # Đường dẫn đến các file CSV
    file_paths = {
        'credits': 'dataset/credits.csv',
        'keywords': 'dataset/keywords.csv',
        'links': 'dataset/links.csv',
        'movies_metadata': 'dataset/movies_metadata.csv',
        'ratings': 'dataset/ratings.csv'
    }

    # Tạo analyzer instance
    analyzer = MovieDataAnalyzer()

    # Chạy phân tích
    success = analyzer.run_full_analysis(file_paths)

    if success:
        print("\n📋 Dữ liệu sau khi xử lý có các cột:")
        print(list(analyzer.merged_data.columns))

        print(f"\n📊 Kích thước dữ liệu cuối: {analyzer.merged_data.shape}")

        # Có thể truy cập dữ liệu đã xử lý
        # processed_data = analyzer.merged_data

        return analyzer
    else:
        print("❌ Phân tích thất bại!")
        return None


# Chạy phân tích
if __name__ == "__main__":
    # Chạy phân tích chính
    movie_analyzer = main()

    # Các phân tích bổ sung có thể thực hiện:
    if movie_analyzer and movie_analyzer.merged_data is not None:
        print("\n🔍 CÁC PHÂN TÍCH BỔ SUNG CÓ THỂ THỰC HIỆN:")
        print("1. movie_analyzer.merged_data - Truy cập dữ liệu đã xử lý")
        print("2. movie_analyzer.create_visualizations() - Tạo lại biểu đồ")
        print("3. movie_analyzer.correlation_analysis() - Phân tích tương quan chi tiết")
        print("4. movie_analyzer.generate_insights() - Tạo lại insights")
        print("5. movie_analyzer.export_results('custom_name.csv') - Xuất với tên khác")

        print("\n📊 THỐNG KÊ NHANH:")
        data = movie_analyzer.merged_data
        print(f"- Phim có lời (ROI > 0): {(data['roi'] > 0).sum():,} phim")
        print(f"- Phim có rating ≥ 8.0: {(data['vote_average'] >= 8.0).sum():,} phim")
        print(f"- Phim có doanh thu ≥ 100M: {(data['revenue'] >= 100000000).sum():,} phim")
        print(
            f"- Thể loại phổ biến nhất: {data['primary_genre'].mode().iloc[0] if len(data['primary_genre'].mode()) > 0 else 'N/A'}")
