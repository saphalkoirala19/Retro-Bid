import datetime
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    bio = models.TextField(max_length=500, blank=True)
    birth_date = models.DateField(null=True, blank=True)

class ListingCategory(models.Model):
    name = models.CharField(max_length=64)

    def __str__(self):
        return f"{self.name}"

class Listing(models.Model):
    # Auction type choices
    ENGLISH = 'english'
    DUTCH = 'dutch'
    AUCTION_TYPE_CHOICES = [
        (ENGLISH, 'English Auction'),
        (DUTCH, 'Dutch Auction'),
    ]

    create_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="listings")
    title = models.CharField(max_length=64)
    description = models.TextField()
    category = models.ForeignKey(ListingCategory, on_delete=models.DO_NOTHING, related_name="listings")
    image_url = models.URLField(max_length=200)
    
    # Common fields for both auction types
    starting_bid = models.DecimalField(max_digits=10, decimal_places=2)
    current_bid = models.DecimalField(max_digits=10, decimal_places=2)
    current_bidder = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name="leading_bids", null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    # New fields for auction type
    auction_type = models.CharField(max_length=10, choices=AUCTION_TYPE_CHOICES, default=ENGLISH)
    
    # Dutch auction specific fields
    dutch_start_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    dutch_reserve_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    dutch_decrement = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    dutch_decrement_interval = models.IntegerField(null=True, blank=True, help_text="Interval in seconds")
    dutch_last_update = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.id}: {self.title} to {self.category}"
    
    def get_current_dutch_price(self):
        """Calculate the current price for a Dutch auction based on time elapsed"""
        if self.auction_type != self.DUTCH or not self.is_active:
            return self.current_bid
            
        if not self.dutch_last_update:
            return self.dutch_start_price
            
        # Calculate time elapsed since last update
        now = timezone.now()
        time_elapsed = (now - self.dutch_last_update).total_seconds()
        
        # Calculate number of decrements
        num_decrements = int(time_elapsed / self.dutch_decrement_interval)
        
        # Calculate new price
        new_price = self.dutch_start_price - (num_decrements * self.dutch_decrement)
        
        # Don't go below reserve price
        if new_price < self.dutch_reserve_price:
            new_price = self.dutch_reserve_price
            
        return new_price
    
    def update_dutch_price(self):
        """Update the current price for a Dutch auction"""
        if self.auction_type != self.DUTCH or not self.is_active:
            return
            
        new_price = self.get_current_dutch_price()
        self.current_bid = new_price
        # Don't update dutch_last_update here, as it would reset the time calculation
        self.save()
        
        # If price reaches reserve and no bidder, close the auction
        if self.current_bid <= self.dutch_reserve_price and not self.current_bidder:
            self.is_active = False
            self.save()
            # No need to create AuctionWinner record here as there's no winner


class Bid(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="bids")
    bidder = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name="bids")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    create_date = models.DateTimeField("Bid Date", auto_now=False, auto_now_add=True)

    def __str__(self):
        return f"{self.bidder}: {self.amount}"
    
class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="comments")
    content = models.TextField()
    create_date = models.DateTimeField("Bid Date", auto_now=False, auto_now_add=True)

    def __str__(self):
        return f"{self.user}: {self.content}"

class Watcher(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="watchlist")
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="watchers")
    
    def __str__(self):
        return f"{self.listing}"

class AuctionWinner(models.Model):
    listing = models.OneToOneField(Listing, on_delete=models.CASCADE, related_name="winner_info")
    winner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="won_auctions")
    contact_info_shared = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.winner.username} won {self.listing.title}"
