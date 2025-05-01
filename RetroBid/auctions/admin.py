from django.contrib import admin
from .models import User, ListingCategory, Listing, Bid, Comment, Watcher

# Register your models here.
admin.site.register(User)
admin.site.register(ListingCategory)
admin.site.register(Listing)
admin.site.register(Bid)
admin.site.register(Comment)
admin.site.register(Watcher)
