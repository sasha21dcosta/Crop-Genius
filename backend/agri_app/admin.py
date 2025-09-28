from django.contrib import admin
from .models import Item
from .models import UserProfile


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "item_type", "price", "per_unit", "operator_available", "owner", "created_at")
    list_filter = ("item_type", "operator_available", "created_at")
    search_fields = ("name", "owner__username")


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "name", "phone", "city", "preferred_language")
    search_fields = ("user__username", "name", "phone", "city")

