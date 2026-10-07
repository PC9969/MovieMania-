from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify


class Genre(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Movie(models.Model):
    LANGUAGE_CHOICES = [
        ('English', 'English'),
        ('Hindi', 'Hindi'),
        ('Tamil', 'Tamil'),
        ('Telugu', 'Telugu'),
        ('Malayalam', 'Malayalam'),
        ('Kannada', 'Kannada'),
        ('Korean', 'Korean'),
        ('Japanese', 'Japanese'),
        ('Spanish', 'Spanish'),
        ('French', 'French'),
    ]

    title = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    overview = models.TextField()
    genres = models.ManyToManyField(Genre, related_name='movies', blank=True)
    language = models.CharField(max_length=30, choices=LANGUAGE_CHOICES, default='English', db_index=True)
    release_year = models.PositiveIntegerField(db_index=True)
    rating = models.DecimalField(max_digits=3, decimal_places=1, db_index=True, help_text="Rating out of 10")
    runtime_minutes = models.PositiveIntegerField(default=120, help_text="Duration in minutes")
    director = models.CharField(max_length=150)
    cast = models.TextField(help_text="Comma-separated prominent cast members")
    poster_url = models.URLField(max_length=600, blank=True)
    backdrop_url = models.URLField(max_length=600, blank=True)
    mood_tag = models.CharField(max_length=100, blank=True, help_text="e.g. Mind-Bending, Inspiring, Gripping, Uplifting")
    featured = models.BooleanField(default=False, help_text="Highlight on homepage hero/editor picks")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-rating', '-release_year']

    def __str__(self):
        return f"{self.title} ({self.release_year})"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(f"{self.title}-{self.release_year}")
            slug = base_slug
            counter = 1
            while Movie.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def formatted_runtime(self):
        hours = self.runtime_minutes // 60
        mins = self.runtime_minutes % 60
        if hours > 0 and mins > 0:
            return f"{hours}h {mins}m"
        elif hours > 0:
            return f"{hours}h"
        return f"{mins}m"

    @property
    def cast_list(self):
        return [actor.strip() for actor in self.cast.split(',') if actor.strip()]

    @property
    def genre_names(self):
        return [g.name for g in self.genres.all()]


class Watchlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watchlist')
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='watchlisted_by')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-added_at']
        constraints = [
            models.UniqueConstraint(fields=['user', 'movie'], name='unique_user_movie_watchlist')
        ]

    def __str__(self):
        return f"{self.user.username} - {self.movie.title}"
