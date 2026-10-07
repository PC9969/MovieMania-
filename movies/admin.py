from django.contrib import admin
from .models import Genre, Movie, Watchlist


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'movie_count')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}

    def movie_count(self, obj):
        return obj.movies.count()
    movie_count.short_description = 'Movies'


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ('title', 'release_year', 'language', 'rating', 'runtime_minutes', 'director', 'featured', 'created_at')
    list_filter = ('language', 'release_year', 'featured', 'genres')
    search_fields = ('title', 'director', 'cast', 'overview')
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ('genres',)
    ordering = ('-rating', '-release_year')
    list_editable = ('rating', 'featured')
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'overview', 'genres', 'language', 'release_year', 'rating', 'runtime_minutes')
        }),
        ('Credits & Mood', {
            'fields': ('director', 'cast', 'mood_tag', 'featured')
        }),
        ('Media Artwork', {
            'fields': ('poster_url', 'backdrop_url'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Watchlist)
class WatchlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'movie', 'added_at')
    list_filter = ('added_at',)
    search_fields = ('user__username', 'movie__title')
    raw_id_fields = ('movie',)
