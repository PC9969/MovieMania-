from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('discover/', views.discover_view, name='discover'),
    path('movie/<slug:slug>/', views.movie_detail_view, name='movie_detail'),
    path('search/', views.search_view, name='search'),
    path('watchlist/', views.watchlist_view, name='watchlist'),
    path('watchlist/toggle/<int:movie_id>/', views.toggle_watchlist_view, name='toggle_watchlist'),
    path('api/recommend/', views.api_recommend_view, name='api_recommend'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]
