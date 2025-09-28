
from django.urls import path
from .views import register, login_user, CustomAuthToken, items, bookings, respond_booking, owner_bookings, user_profile

urlpatterns = [
    path('register/', register),
    path('login/', login_user),
    path('user/profile/', user_profile),
    path('items/', items),
    path('bookings/', bookings),
    path('bookings/<int:booking_id>/respond/', respond_booking),
    path('bookings/owner/', owner_bookings),
]
