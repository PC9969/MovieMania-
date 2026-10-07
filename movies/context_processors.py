from .models import Watchlist

def watchlist_count(request):
    """Context processor providing current user's watchlist count to all templates."""
    if request.user.is_authenticated:
        try:
            return {'watchlist_count': Watchlist.objects.filter(user=request.user).count()}
        except Exception:
            return {'watchlist_count': 0}
    return {'watchlist_count': 0}
