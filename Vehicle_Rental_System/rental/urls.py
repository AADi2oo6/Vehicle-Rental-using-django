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
    
    # Custom admin dashboard URLs
    path("admin_new/", views.admin_dashboard_view, name="admin_dashboard"),
    path("admin_new/maintenance/", views.admin_maintenance_view, name="admin_maintenance"),
    path("admin_new/bookings/", views.bookings_management_view, name="bookings_management"),
    path("admin_new/queries/", views.admin_queries_view, name="admin_queries"),
    
    # Payments Management URLs (consolidated)
     path("admin_new/bookings/return/<int:booking_id>/", views.return_vehicle_view, name="return_vehicle"),
   path("admin_new/payments/", views.admin_payments_view, name="admin_payments"),
    path("admin_new/payments/add/", views.payment_form_view, name="payment_add"),
    path("admin_new/payments/edit/<int:payment_id>/", views.payment_form_view, name="payment_edit"),
    path("admin_new/payments/delete/<int:payment_id>/", views.payment_delete_view, name="payment_delete"),

    path("admin_new/api/data/", views.get_dashboard_data, name="get_dashboard_data"),
     path("admin_new/change-password/", views.change_password_view, name="change_password"),
]