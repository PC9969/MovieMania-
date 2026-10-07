from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Genre, Movie, Watchlist
from .recommender import get_recommendations, get_similar_movies


class MovieModelTests(TestCase):
    def setUp(self):
        self.genre_scifi = Genre.objects.create(name='Sci-Fi')
        self.genre_action = Genre.objects.create(name='Action')
        self.movie = Movie.objects.create(
            title='Inception',
            overview='A thief who steals corporate secrets through dream-sharing technology.',
            language='English',
            release_year=2010,
            rating=Decimal('8.8'),
            runtime_minutes=148,
            director='Christopher Nolan',
            cast='Leonardo DiCaprio, Joseph Gordon-Levitt',
            mood_tag='Mind-Bending',
            featured=True,
        )
        self.movie.genres.add(self.genre_scifi, self.genre_action)

    def test_movie_slug_and_str(self):
        self.assertEqual(self.movie.slug, 'inception-2010')
        self.assertEqual(str(self.movie), 'Inception (2010)')

    def test_formatted_runtime(self):
        self.assertEqual(self.movie.formatted_runtime, '2h 28m')

    def test_cast_list_and_genre_names(self):
        self.assertEqual(len(self.movie.cast_list), 2)
        self.assertIn('Leonardo DiCaprio', self.movie.cast_list)
        self.assertIn('Sci-Fi', self.movie.genre_names)
        self.assertIn('Action', self.movie.genre_names)


class RecommendationEngineTests(TestCase):
    def setUp(self):
        self.scifi = Genre.objects.create(name='Sci-Fi')
        self.drama = Genre.objects.create(name='Drama')
        self.comedy = Genre.objects.create(name='Comedy')

        self.m1 = Movie.objects.create(
            title='Interstellar',
            overview='Exploration of wormholes in space.',
            language='English',
            release_year=2014,
            rating=Decimal('8.7'),
            runtime_minutes=169,
            director='Christopher Nolan',
            cast='Matthew McConaughey',
            mood_tag='Epic',
        )
        self.m1.genres.add(self.scifi, self.drama)

        self.m2 = Movie.objects.create(
            title='3 Idiots',
            overview='Two friends search for their college buddy.',
            language='Hindi',
            release_year=2009,
            rating=Decimal('8.4'),
            runtime_minutes=170,
            director='Rajkumar Hirani',
            cast='Aamir Khan',
            mood_tag='Inspiring',
        )
        self.m2.genres.add(self.comedy, self.drama)

    def test_recommendation_genre_and_language_filter(self):
        prefs = {
            'genres': ['Sci-Fi'],
            'language': 'English',
            'min_rating': '8.0',
            'era': '2010s',
        }
        recs = get_recommendations(prefs)
        self.assertTrue(len(recs) >= 1)
        top = recs[0]
        self.assertEqual(top['movie'].title, 'Interstellar')
        self.assertGreaterEqual(top['match_score'], 80)
        self.assertTrue(any('Sci-Fi' in r for r in top['match_reasons']))
        self.assertTrue(any('English' in r for r in top['match_reasons']))

    def test_similar_movies(self):
        similar = get_similar_movies(self.m1)
        # Both share the Drama genre
        self.assertTrue(len(similar) >= 1)
        self.assertEqual(similar[0]['movie'].title, '3 Idiots')


class ViewAndRoutingTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='filmfan', password='testpassword123')
        self.genre = Genre.objects.create(name='Thriller')
        self.movie = Movie.objects.create(
            title='Parasite',
            overview='Class satire thriller.',
            language='Korean',
            release_year=2019,
            rating=Decimal('8.5'),
            runtime_minutes=132,
            director='Bong Joon Ho',
            cast='Song Kang-ho',
            featured=True,
        )
        self.movie.genres.add(self.genre)

    def test_homepage_loads(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'MovieMania')
        self.assertContains(response, 'Parasite')

    def test_discover_page_loads(self):
        response = self.client.get(reverse('discover'), {'language': 'Korean', 'genres': 'Thriller'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Parasite')
        self.assertContains(response, '% Match')

    def test_movie_detail_page(self):
        response = self.client.get(reverse('movie_detail', kwargs={'slug': self.movie.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Bong Joon Ho')
        self.assertContains(response, 'Song Kang-ho')

    def test_search_view(self):
        response = self.client.get(reverse('search'), {'q': 'Parasite'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Parasite')

    def test_watchlist_login_required(self):
        response = self.client.get(reverse('watchlist'))
        self.assertEqual(response.status_code, 302)  # Redirects to login

        self.client.login(username='filmfan', password='testpassword123')
        response = self.client.get(reverse('watchlist'))
        self.assertEqual(response.status_code, 200)

    def test_toggle_watchlist_ajax(self):
        self.client.login(username='filmfan', password='testpassword123')
        response = self.client.post(
            reverse('toggle_watchlist', kwargs={'movie_id': self.movie.id}),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['in_watchlist'])
        self.assertEqual(data['watchlist_count'], 1)

        # Toggle again to remove
        response2 = self.client.post(
            reverse('toggle_watchlist', kwargs={'movie_id': self.movie.id}),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        data2 = response2.json()
        self.assertFalse(data2['in_watchlist'])
        self.assertEqual(data2['watchlist_count'], 0)

    def test_api_recommend_endpoint(self):
        response = self.client.get(reverse('api_recommend'), {'language': 'Korean'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertTrue(data['count'] >= 1)
        self.assertEqual(data['recommendations'][0]['title'], 'Parasite')
