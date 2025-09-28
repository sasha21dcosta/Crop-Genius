from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField


class Item(models.Model):
    class ItemType(models.TextChoices):
        MARKETPLACE = 'marketplace', 'Marketplace'
        RENTAL = 'rental', 'Rental'

    owner = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='items')
    item_type = models.CharField(max_length=20, choices=ItemType.choices)
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    # For rental items only; optional for marketplace
    per_unit = models.CharField(max_length=20, blank=True, null=True)  # hour, acre, day
    operator_available = models.BooleanField(default=False)
    image = models.ImageField(upload_to='items/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # New fields for rental
    availability_start = models.DateField(blank=True, null=True)
    availability_end = models.DateField(blank=True, null=True)
    time_slots = models.JSONField(blank=True, null=True)

    def __str__(self) -> str:
        return f"{self.item_type}: {self.name} by {self.owner}"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    city = models.CharField(max_length=100)
    address = models.TextField()
    preferred_language = models.CharField(max_length=20, choices=[('English', 'English'), ('Hindi', 'Hindi'), ('Marathi', 'Marathi')])

    def __str__(self):
        return f"Profile of {self.user.username}"


class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        ACCEPTED = 'accepted', 'Accepted'
        DECLINED = 'declined', 'Declined'

    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='bookings')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    date = models.DateField()
    time_slot = models.CharField(max_length=50)  # e.g. '09:00-10:00'
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    contact_phone = models.CharField(max_length=20)
    contact_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Booking for {self.item.name} by {self.user.username} on {self.date} at {self.time_slot} ({self.status})"
