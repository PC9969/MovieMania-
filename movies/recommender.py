from decimal import Decimal
from django.db.models import Q
from .models import Movie, Genre


ERA_RANGES = {
    '2020s': (2020, 2030),
    '2010s': (2010, 2019),
    '2000s': (2000, 2009),
    '90s': (1990, 1999),
    'classic': (1900, 1989),
}


def get_recommendations(preferences, user=None, limit=24):
   
    selected_genres = preferences.get('genres', [])
    if isinstance(selected_genres, str) and selected_genres:
        selected_genres = [g.strip() for g in selected_genres.split(',') if g.strip()]
    elif not isinstance(selected_genres, list):
        selected_genres = []
    # Filter out empty or 'all'
    selected_genres = [g for g in selected_genres if g and g.lower() != 'all']

    selected_language = preferences.get('language', 'all')
    if selected_language and selected_language.lower() == 'all':
        selected_language = None

    raw_min_rating = preferences.get('min_rating', None)
    min_rating = None
    if raw_min_rating:
        try:
            min_rating = float(raw_min_rating)
        except (ValueError, TypeError):
            min_rating = None

    selected_era = preferences.get('era', 'all')
    if selected_era and selected_era.lower() == 'all':
        selected_era = None

    selected_runtime = preferences.get('runtime', 'all')
    if selected_runtime and selected_runtime.lower() == 'all':
        selected_runtime = None

    selected_mood = preferences.get('mood', 'all')
    if selected_mood and selected_mood.lower() == 'all':
        selected_mood = None

    
    raw_weights = {}
    if selected_genres:
        raw_weights['genre'] = 35.0
    if selected_language:
        raw_weights['language'] = 25.0
    if min_rating is not None:
        raw_weights['rating'] = 20.0
    if selected_era and selected_era in ERA_RANGES:
        raw_weights['era'] = 10.0
    if selected_runtime:
        raw_weights['runtime'] = 5.0
    if selected_mood:
        raw_weights['mood'] = 5.0

    total_weight = sum(raw_weights.values())
    if total_weight > 0:
        norm_factor = 100.0 / total_weight
        weights = {k: v * norm_factor for k, v in raw_weights.items()}
    else:
        weights = {}

    
    queryset = Movie.objects.prefetch_related('genres').all()

    
    filter_q = Q()
    if selected_language:
       
        pass

    candidates = list(queryset)
    if not candidates:
        return []

    
    user_watchlist_ids = set()
    if user and user.is_authenticated:
        from .models import Watchlist
        user_watchlist_ids = set(Watchlist.objects.filter(user=user).values_list('movie_id', flat=True))

    results = []

    for movie in candidates:
        score = 0.0
        reasons = []
        movie_genre_names = set(g.name.lower() for g in movie.genres.all())

        
        if not weights:
            
            score = float(movie.rating) * 10.0
            reasons.append(f"Highly rated ({movie.rating}/10)")
            if movie.featured:
                reasons.append("Featured Editor's Choice")
        else:
            
            if 'genre' in weights:
                match_count = 0
                matched_genre_names = []
                for g_req in selected_genres:
                    if g_req.lower() in movie_genre_names:
                        match_count += 1
                        matched_genre_names.append(g_req)

                if match_count > 0:
                    fraction = min(1.0, match_count / len(selected_genres))
                    
                    genre_factor = 0.8 + 0.2 * (match_count / max(1, len(selected_genres)))
                    score += weights['genre'] * min(1.0, genre_factor)
                    reasons.append(f"Matches genre: {', '.join(matched_genre_names)}")

            
            if 'language' in weights:
                if movie.language.lower() == selected_language.lower():
                    score += weights['language']
                    reasons.append(f"In requested language ({movie.language})")

            
            if 'rating' in weights:
                movie_rating_float = float(movie.rating)
                if movie_rating_float >= min_rating:
                    score += weights['rating']
                    reasons.append(f"Rating {movie.rating}/10 (satisfies min {min_rating})")
                else:
                   
                    diff = min_rating - movie_rating_float
                    if diff <= 0.8:
                        partial_ratio = max(0.0, 1.0 - (diff / 0.8))
                        score += weights['rating'] * partial_ratio * 0.5

            
            if 'era' in weights:
                start_yr, end_yr = ERA_RANGES[selected_era]
                if start_yr <= movie.release_year <= end_yr:
                    score += weights['era']
                    reasons.append(f"Released in {selected_era.upper()} ({movie.release_year})")

           
            if 'runtime' in weights:
                m_rt = movie.runtime_minutes
                matched_rt = False
                if selected_runtime == 'short' and m_rt <= 110:
                    matched_rt = True
                    rt_desc = "Quick watch (<110m)"
                elif selected_runtime == 'standard' and 110 < m_rt <= 150:
                    matched_rt = True
                    rt_desc = "Standard length (110-150m)"
                elif selected_runtime == 'epic' and m_rt > 150:
                    matched_rt = True
                    rt_desc = "Epic cinematic runtime (>150m)"

                if matched_rt:
                    score += weights['runtime']
                    reasons.append(f"Fits runtime preference: {movie.formatted_runtime} ({rt_desc})")

            
            if 'mood' in weights:
                if movie.mood_tag and selected_mood.lower() in movie.mood_tag.lower():
                    score += weights['mood']
                    reasons.append(f"Matches mood '{selected_mood}'")

       
        score = min(100.0, max(0.0, round(score, 1)))

       
        if weights and score < 15.0:
            continue

        results.append({
            'movie': movie,
            'match_score': int(round(score)),
            'match_reasons': reasons,
            'is_in_watchlist': movie.id in user_watchlist_ids
        })

    
    results.sort(
        key=lambda item: (item['match_score'], float(item['movie'].rating), item['movie'].release_year),
        reverse=True
    )

    return results[:limit]


def get_similar_movies(movie, limit=6, user=None):
    """
    Finds content-similar movies based on shared genres and language.
    """
    movie_genre_ids = movie.genres.values_list('id', flat=True)
    similar_qs = Movie.objects.filter(
        genres__id__in=movie_genre_ids
    ).exclude(id=movie.id).distinct()

    
    similar_list = list(similar_qs)
    user_watchlist_ids = set()
    if user and user.is_authenticated:
        from .models import Watchlist
        user_watchlist_ids = set(Watchlist.objects.filter(user=user).values_list('movie_id', flat=True))

    def similarity_rank(m):
        genre_overlap = len(set(m.genres.values_list('id', flat=True)) & set(movie_genre_ids))
        lang_match = 2 if m.language == movie.language else 0
        return (genre_overlap + lang_match, float(m.rating))

    similar_list.sort(key=similarity_rank, reverse=True)

    results = []
    for m in similar_list[:limit]:
        results.append({
            'movie': m,
            'is_in_watchlist': m.id in user_watchlist_ids
        })
    return results
