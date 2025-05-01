import os
from django.contrib.auth import get_user_model
from django.core.management import BaseCommand

User = get_user_model()

# Create superuser if it doesn't exist
if not User.objects.filter(email='a@b.com').exists():
    User.objects.create_superuser('admin', 'a@b.com', 'Asd123!@#') 