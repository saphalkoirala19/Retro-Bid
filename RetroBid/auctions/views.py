from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from .models import ListingCategory, User, Listing, Bid, Comment, Watcher, AuctionWinner
from django.contrib.auth.decorators import login_required


def index(request):
    active_listings = Listing.objects.filter(is_active=True)
    # Update Dutch auction prices
    for listing in active_listings:
        if listing.auction_type == Listing.DUTCH:
            listing.update_dutch_price()
    return render(request, "auctions/index.html", {
        "listings": active_listings
    })



def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")

@login_required
def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")

@login_required    
def bid_add(request, listing_id):
    if request.method == "POST":
        listing = Listing.objects.get(id=listing_id)
        user = request.user
        
        # Handle different auction types
        if listing.auction_type == Listing.ENGLISH:
            amount = request.POST["amount"]
            
            if float(amount) <= listing.current_bid or float(amount) <= listing.starting_bid:
                return render(request, "auctions/listing.html", {
                    "listing": listing,
                    "message": "Your bid must be greater than the current bid."
                })
            
            # Add new bid
            Bid.objects.create(
                listing=listing,
                bidder=user,
                amount=amount
            )

            # Update current bid for this listing
            listing.current_bid = amount
            listing.current_bidder = user
            listing.save()
            
        elif listing.auction_type == Listing.DUTCH:
            # For Dutch auction, update the price first
            listing.update_dutch_price()
            
            # Create bid at current price
            Bid.objects.create(
                listing=listing,
                bidder=user,
                amount=listing.current_bid
            )
            
            # Set bidder and close auction
            listing.current_bidder = user
            listing.is_active = False
            listing.save()
            
            # Create AuctionWinner record for Dutch auction
            AuctionWinner.objects.create(
                listing=listing,
                winner=user
            )

        return HttpResponseRedirect(reverse("listing", args=(listing_id,))) 

@login_required
def categories(request):
    categories = ListingCategory.objects.all()
    return render(request, "auctions/categories.html", {
        "categories": categories
    })

@login_required
def category(request, category_id):
    category = ListingCategory.objects.get(id=category_id)
    listings = Listing.objects.filter(category=category ,is_active=True)
    # Update Dutch auction prices
    for listing in listings:
        if listing.auction_type == Listing.DUTCH:
            listing.update_dutch_price()
    return render(request, "auctions/index.html", {
        "category": category,
        "listings": listings
    })

@login_required
def closed(request):
    closed_listings = Listing.objects.filter(is_active=False)
    return render(request, "auctions/closed.html", {
        "listings": closed_listings
    })

@login_required
def comment_add(request, listing_id):
    if request.method == "POST":
        listing = Listing.objects.get(id=listing_id)
        content = request.POST["content"]
        user = request.user

        # Add new comment
        Comment.objects.create(
            listing=listing,
            user=user,
            content=content
        )

        return HttpResponseRedirect(reverse("listing", args=(listing_id,))) 


@login_required
def listing(request, listing_id):
    listing = Listing.objects.get(id=listing_id)
    
    # Update Dutch auction price if active
    if listing.auction_type == Listing.DUTCH and listing.is_active:
        listing.update_dutch_price()
        
    bids = listing.bids.all()
    comments = listing.comments.all()
    user = request.user
    is_watched = Watcher.objects.filter(user=user, listing=listing).exists()
    return render(request, "auctions/listing.html", {
        "listing": listing,
        "bids": bids,
        "comments": comments,
        "is_watched": is_watched
    })

@login_required
def listing_add(request):
    if request.method == "POST":
        title = request.POST["title"]
        description = request.POST["description"]
        category = ListingCategory.objects.get(id=request.POST["category"])
        image_url = request.POST["image_url"]
        auction_type = request.POST["auction_type"]
        user = request.user

        if not user.is_authenticated:
            return HttpResponseRedirect(request, "auctions/index.html", {
                "message": "You must be logged in to add a listing."
            })
        
        # Create listing with common fields
        listing = Listing(
            create_user=user,
            title=title,
            description=description,
            category=category,
            image_url=image_url,
            auction_type=auction_type,
            is_active=True,
        )
        
        # Handle specific auction type fields
        if auction_type == Listing.ENGLISH:
            starting_bid = float(request.POST["starting_bid"])
            listing.starting_bid = starting_bid
            listing.current_bid = 0
            listing.current_bidder = None
            
        elif auction_type == Listing.DUTCH:
            dutch_start_price = float(request.POST["dutch_start_price"])
            dutch_reserve_price = float(request.POST["dutch_reserve_price"])
            dutch_decrement = float(request.POST["dutch_decrement"])
            dutch_decrement_interval = int(request.POST["dutch_decrement_interval"])
            
            # Validate Dutch auction parameters
            if dutch_start_price <= dutch_reserve_price:
                return render(request, "auctions/listing_add.html", {
                    "categories": ListingCategory.objects.all(),
                    "message": "Start price must be greater than reserve price."
                })
                
            if dutch_decrement <= 0:
                return render(request, "auctions/listing_add.html", {
                    "categories": ListingCategory.objects.all(),
                    "message": "Price decrement must be greater than zero."
                })
                
            if dutch_decrement_interval <= 0:
                return render(request, "auctions/listing_add.html", {
                    "categories": ListingCategory.objects.all(),
                    "message": "Decrement interval must be greater than zero."
                })
            
            # Set Dutch auction fields
            listing.starting_bid = dutch_start_price
            listing.current_bid = dutch_start_price
            listing.dutch_start_price = dutch_start_price
            listing.dutch_reserve_price = dutch_reserve_price
            listing.dutch_decrement = dutch_decrement
            listing.dutch_decrement_interval = dutch_decrement_interval
            listing.dutch_last_update = timezone.now()
            
        # Save the listing
        listing.save()
        return HttpResponseRedirect(reverse("index"))
    
    return render(request, "auctions/listing_add.html", {
        "categories": ListingCategory.objects.all()
    })

@login_required    
def listing_close(request, listing_id):
    listing = Listing.objects.get(id=listing_id)
    if listing.create_user != request.user:
        return render(request, "auctions/listing.html", {
            "listing": listing,
            "message": "You are not the owner of this listing."
        })
    
    listing.is_active = False
    listing.save()
    
    # Record the winner if there is a current bidder
    if listing.current_bidder:
        AuctionWinner.objects.create(
            listing=listing,
            winner=listing.current_bidder
        )
    
    return HttpResponseRedirect(reverse("index"))

@login_required
def watchlist(request):
    user = request.user
    watchers = Watcher.objects.filter(user=user)
    watched_listings = [watcher.listing for watcher in watchers]
    
    # Update Dutch auction prices
    for listing in watched_listings:
        if listing.auction_type == Listing.DUTCH and listing.is_active:
            listing.update_dutch_price()
            
    return render(request, "auctions/index.html", {
        "watchlist": True,
        "listings": watched_listings
    })

@login_required
def watch_toggle(request, listing_id):
    listing = Listing.objects.get(id=listing_id)
    user = request.user

    if Watcher.objects.filter(user=user, listing=listing).exists():
        Watcher.objects.filter(user=user, listing=listing).delete()
    else:
        Watcher.objects.create(
            user=user,
            listing=listing
        )

    return HttpResponseRedirect(reverse("listing", args=(listing_id,)))

@login_required
def get_dutch_price(request, listing_id):
    """AJAX endpoint to get the current Dutch auction price"""
    listing = Listing.objects.get(id=listing_id)
    
    if listing.auction_type != Listing.DUTCH or not listing.is_active:
        return JsonResponse({"error": "Not an active Dutch auction"}, status=400)
    
    listing.update_dutch_price()
    
    return JsonResponse({
        "current_price": float(listing.current_bid),
        "reserve_reached": listing.current_bid <= listing.dutch_reserve_price
    })  

@login_required
def dashboard(request):
    user = request.user
    
    # Get all bids made by the user
    user_bids = Bid.objects.filter(bidder=user).order_by('-create_date')
    
    # Get unique listings the user has bid on
    bid_listings = {}
    for bid in user_bids:
        if bid.listing.id not in bid_listings:
            bid_listings[bid.listing.id] = {
                'listing': bid.listing,
                'user_bid': bid.amount,
                'status': 'active' if bid.listing.is_active else 'closed',
                'won': False
            }
    
    # Check which auctions the user has won
    won_auctions = AuctionWinner.objects.filter(winner=user)
    for won in won_auctions:
        if won.listing.id in bid_listings:
            bid_listings[won.listing.id]['won'] = True
            bid_listings[won.listing.id]['contact_info_shared'] = won.contact_info_shared
    
    # Get listings created by the user that have been closed
    created_listings = Listing.objects.filter(create_user=user, is_active=False)
    
    # Get winner information for listings created by the user
    created_with_winners = []
    for listing in created_listings:
        try:
            winner_info = AuctionWinner.objects.get(listing=listing)
            created_with_winners.append({
                'listing': listing,
                'winner': winner_info.winner,
                'contact_info_shared': winner_info.contact_info_shared,
                'winner_id': winner_info.id
            })
        except AuctionWinner.DoesNotExist:
            created_with_winners.append({
                'listing': listing,
                'winner': None
            })
    
    return render(request, "auctions/dashboard.html", {
        "bid_listings": list(bid_listings.values()),
        "created_with_winners": created_with_winners
    })

@login_required
def share_contact(request, winner_id):
    if request.method == "POST":
        try:
            winner_info = AuctionWinner.objects.get(id=winner_id)
            
            # Ensure the user is the creator of the listing
            if request.user != winner_info.listing.create_user:
                return HttpResponseRedirect(reverse("dashboard"))
            
            winner_info.contact_info_shared = True
            winner_info.save()
            
            return HttpResponseRedirect(reverse("dashboard"))
        except AuctionWinner.DoesNotExist:
            pass
    
    return HttpResponseRedirect(reverse("dashboard"))  
