# rental/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # User-facing URLs
    path("", views.home_view, name="home"),
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("vehicles/", views.vehicle_list_view, name="vehicle_list"),
    path("book/<int:vehicle_id>/", views.booking_view, name="booking"),
    path("about/", views.about_us_view, name="about_us"),
    path("profile/", views.my_profile_view, name="my_profile"),
    path("profile/bookings/", views.my_bookings_view, name="my_bookings"),
    path("api/all-reviews/", views.all_reviews_api, name="all_reviews_api"),

    path("profile/edit/", views.edit_profile_view, name="edit_profile"),

    # The <int:booking_id> part captures the ID from the URL.
    path("booking/<int:booking_id>/", views.booking_detail_view, name="booking_detail"),

    path("booking/<int:booking_id>/review/add/", views.add_review, name="add_review"),
    path("review/<int:review_id>/edit/", views.edit_review, name="edit_review"),
    path("review/<int:review_id>/delete/", views.delete_review, name="delete_review"),

    path("booking/confirm/<int:vehicle_id>/", views.confirm_booking_pay_later, name="confirm_booking_pay_later"),
    
    # Razorpay Payment URLs
    path("booking/<int:vehicle_id>/pay/", views.initiate_razorpay_payment, name="initiate_razorpay_payment"),
    path("payment/razorpay/callback/", views.razorpay_payment_callback, name="razorpay_payment_callback"),
]