import json
from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db.models import Q, Count
from django.urls import reverse

from .models import Movie, Genre, Watchlist
from .recommender import get_recommendations, get_similar_movies


def home_view(request):
    """Landing and Homepage displaying Hero movie, curated shelves, and discovery CTA."""
    # Featured Hero Movie
    hero_movie = Movie.objects.filter(featured=True, rating__gte=8.7).order_by('-rating').first()
    if not hero_movie:
        hero_movie = Movie.objects.order_by('-rating').first()

    # User watchlist set for marking saved movies
    user_watchlist_ids = set()
    if request.user.is_authenticated:
        user_watchlist_ids = set(Watchlist.objects.filter(user=request.user).values_list('movie_id', flat=True))

    # Curated Shelves
    editors_picks = Movie.objects.filter(featured=True).exclude(id=hero_movie.id if hero_movie else None)[:8]
    
    top_indian = Movie.objects.filter(
        language__in=['Hindi', 'Tamil', 'Telugu', 'Malayalam', 'Kannada'],
        rating__gte=8.1
    ).order_by('-rating', '-release_year')[:8]

    top_hollywood = Movie.objects.filter(
        language='English',
        rating__gte=8.4
    ).order_by('-rating')[:8]

    scifi_thrillers = Movie.objects.filter(
        Q(genres__name__in=['Sci-Fi', 'Thriller', 'Mystery'])
    ).distinct().order_by('-rating')[:8]

    all_genres = Genre.objects.annotate(movie_count=Count('movies')).filter(movie_count__gt=0).order_by('name')

    context = {
        'hero_movie': hero_movie,
        'hero_in_watchlist': (hero_movie.id in user_watchlist_ids) if hero_movie else False,
        'editors_picks': editors_picks,
        'top_indian': top_indian,
        'top_hollywood': top_hollywood,
        'scifi_thrillers': scifi_thrillers,
        'all_genres': all_genres,
        'user_watchlist_ids': user_watchlist_ids,
    }
    return render(request, 'movies/home.html', context)


def discover_view(request):
    """
    Core Recommendation & Discovery view.
    Accepts GET parameters for genres, language, min_rating, era, runtime, mood.
    Returns rendered HTML or JSON when requested via AJAX.
    """
    # Extract query params
    selected_genres = request.GET.getlist('genres')
    if not selected_genres and request.GET.get('genre'):
        selected_genres = [request.GET.get('genre')]

    selected_language = request.GET.get('language', 'all')
    min_rating = request.GET.get('min_rating', '')
    selected_era = request.GET.get('era', 'all')
    selected_runtime = request.GET.get('runtime', 'all')
    selected_mood = request.GET.get('mood', 'all')

    preferences = {
        'genres': selected_genres,
        'language': selected_language,
        'min_rating': min_rating,
        'era': selected_era,
        'runtime': selected_runtime,
        'mood': selected_mood,
    }

    # Determine if user entered explicit filters
    has_active_filters = bool(
        selected_genres or
        (selected_language and selected_language != 'all') or
        min_rating or
        (selected_era and selected_era != 'all') or
        (selected_runtime and selected_runtime != 'all') or
        (selected_mood and selected_mood != 'all')
    )

    recommendations = get_recommendations(preferences, user=request.user, limit=30)

    # If AJAX request, return structured JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
        data = []
        for item in recommendations:
            m = item['movie']
            data.append({
                'id': m.id,
                'title': m.title,
                'slug': m.slug,
                'release_year': m.release_year,
                'language': m.language,
                'rating': str(m.rating),
                'runtime_formatted': m.formatted_runtime,
                'genres': [g.name for g in m.genres.all()],
                'poster_url': m.poster_url,
                'overview': m.overview[:140] + '...' if len(m.overview) > 140 else m.overview,
                'director': m.director,
                'mood_tag': m.mood_tag,
                'match_score': item['match_score'],
                'match_reasons': item['match_reasons'],
                'is_in_watchlist': item['is_in_watchlist'],
                'detail_url': reverse('movie_detail', kwargs={'slug': m.slug}),
            })
        return JsonResponse({
            'count': len(data),
            'has_active_filters': has_active_filters,
            'results': data
        })

    all_genres = Genre.objects.all().order_by('name')
    all_languages = [choice[0] for choice in Movie.LANGUAGE_CHOICES]
    mood_options = [
        'Mind-Bending', 'Inspiring', 'Gripping', 'Feel-Good',
        'Dark & Gripping', 'High-Octane', 'Heartwarming', 'Atmospheric & Haunting'
    ]

    context = {
        'recommendations': recommendations,
        'all_genres': all_genres,
        'all_languages': all_languages,
        'mood_options': mood_options,
        'selected_genres': selected_genres,
        'selected_language': selected_language,
        'selected_min_rating': min_rating,
        'selected_era': selected_era,
        'selected_runtime': selected_runtime,
        'selected_mood': selected_mood,
        'has_active_filters': has_active_filters,
        'result_count': len(recommendations),
    }
    return render(request, 'movies/discover.html', context)


def movie_detail_view(request, slug):
    """Detailed movie view with rich metadata, similar movies, and watchlist control."""
    movie = get_object_or_404(Movie.objects.prefetch_related('genres'), slug=slug)
    
    is_in_watchlist = False
    if request.user.is_authenticated:
        is_in_watchlist = Watchlist.objects.filter(user=request.user, movie=movie).exists()

    similar_movies = get_similar_movies(movie, limit=6, user=request.user)

    # Optional match calculation if incoming from a specific preference session/query
    match_score = request.GET.get('match_score')
    match_reasons = request.GET.getlist('reasons')

    context = {
        'movie': movie,
        'is_in_watchlist': is_in_watchlist,
        'similar_movies': similar_movies,
        'match_score': match_score,
        'match_reasons': match_reasons,
    }
    return render(request, 'movies/movie_detail.html', context)


def search_view(request):
    """Multi-field keyword search covering title, director, cast, and overview."""
    query = request.GET.get('q', '').strip()
    results = []
    user_watchlist_ids = set()

    if request.user.is_authenticated:
        user_watchlist_ids = set(Watchlist.objects.filter(user=request.user).values_list('movie_id', flat=True))

    if query:
        results = Movie.objects.filter(
            Q(title__icontains=query) |
            Q(director__icontains=query) |
            Q(cast__icontains=query) |
            Q(overview__icontains=query) |
            Q(genres__name__icontains=query)
        ).distinct().order_by('-rating')

    context = {
        'query': query,
        'results': results,
        'result_count': len(results),
        'user_watchlist_ids': user_watchlist_ids,
    }
    return render(request, 'movies/search.html', context)


@login_required
def watchlist_view(request):
    """Personalized Watchlist page displaying user's saved movies."""
    watchlist_items = Watchlist.objects.filter(user=request.user).select_related('movie').prefetch_related('movie__genres')
    
    context = {
        'watchlist_items': watchlist_items,
        'item_count': watchlist_items.count(),
    }
    return render(request, 'movies/watchlist.html', context)


@login_required
@require_POST
def toggle_watchlist_view(request, movie_id):
    """AJAX endpoint to add/remove a movie from user's watchlist."""
    movie = get_object_or_404(Movie, id=movie_id)
    watchlist_entry = Watchlist.objects.filter(user=request.user, movie=movie).first()

    if watchlist_entry:
        watchlist_entry.delete()
        in_watchlist = False
        message = f"'{movie.title}' removed from your watchlist."
    else:
        Watchlist.objects.create(user=request.user, movie=movie)
        in_watchlist = True
        message = f"'{movie.title}' added to your watchlist!"

    new_count = Watchlist.objects.filter(user=request.user).count()

    return JsonResponse({
        'status': 'success',
        'in_watchlist': in_watchlist,
        'watchlist_count': new_count,
        'message': message,
        'movie_id': movie.id,
        'movie_title': movie.title
    })


def api_recommend_view(request):
    """RESTful JSON API endpoint for external consumers or client-side fetches."""
    selected_genres = request.GET.getlist('genres')
    if not selected_genres and request.GET.get('genre'):
        selected_genres = [request.GET.get('genre')]

    preferences = {
        'genres': selected_genres,
        'language': request.GET.get('language', 'all'),
        'min_rating': request.GET.get('min_rating', ''),
        'era': request.GET.get('era', 'all'),
        'runtime': request.GET.get('runtime', 'all'),
        'mood': request.GET.get('mood', 'all'),
    }

    recommendations = get_recommendations(preferences, user=request.user, limit=30)
    data = []
    for item in recommendations:
        m = item['movie']
        data.append({
            'id': m.id,
            'title': m.title,
            'slug': m.slug,
            'release_year': m.release_year,
            'language': m.language,
            'rating': float(m.rating),
            'runtime_minutes': m.runtime_minutes,
            'runtime_formatted': m.formatted_runtime,
            'genres': [g.name for g in m.genres.all()],
            'director': m.director,
            'cast': m.cast,
            'poster_url': m.poster_url,
            'overview': m.overview,
            'mood_tag': m.mood_tag,
            'match_score': item['match_score'],
            'match_reasons': item['match_reasons'],
            'is_in_watchlist': item['is_in_watchlist'],
        })

    return JsonResponse({
        'status': 'success',
        'count': len(data),
        'preferences': preferences,
        'recommendations': data
    })


def register_view(request):
    """User Registration view with clean validation and automatic login."""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome to MovieMania, {user.username}! Your account has been created.")
            return redirect('discover')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserCreationForm()

    return render(request, 'movies/register.html', {'form': form})


def login_view(request):
    """User Login view."""
    if request.user.is_authenticated:
        return redirect('home')

    next_url = request.GET.get('next', 'home')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect(request.POST.get('next') or 'home')
        else:
            messages.error(request, "Invalid username or password. Please try again.")
    else:
        form = AuthenticationForm()

    return render(request, 'movies/login.html', {'form': form, 'next': next_url})


def logout_view(request):
    """User Logout view."""
    if request.user.is_authenticated:
        username = request.user.username
        logout(request)
        messages.info(request, f"Goodbye, {username}! You have been logged out.")
    return redirect('home')
