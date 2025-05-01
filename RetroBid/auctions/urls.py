from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("category/<int:category_id>", views.category, name="category"),
    path("category", views.categories, name="categories"),
    path("closed", views.closed, name="closed"),
    path("listing/<int:listing_id>", views.listing, name="listing"),
    path("listing/<int:listing_id>/bid_add", views.bid_add, name="bid_add"),
    path("listing/<int:listing_id>/comment_add", views.comment_add, name="comment_add"),
    path("listing/<int:listing_id>/listing_close", views.listing_close, name="listing_close"),
    path("listing/<int:listing_id>/watch_toggle", views.watch_toggle, name="watch_toggle"),
    path("listing/<int:listing_id>/dutch_price", views.get_dutch_price, name="get_dutch_price"),
    path("listing/add", views.listing_add, name="listing_add"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("watchlist", views.watchlist, name="watchlist"),
    path("dashboard", views.dashboard, name="dashboard"),
    path("share_contact/<int:winner_id>", views.share_contact, name="share_contact"),
]
