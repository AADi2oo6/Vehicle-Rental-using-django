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
    path("profile/edit/", views.edit_profile_view, name="edit_profile"),
    path("profile/change-password/", views.user_change_password_view, name="user_change_password"),
    path("profile/bookings/", views.my_bookings_view, name="my_bookings"),
    
    # Custom admin dashboard URLs
    path("admin_new/", views.admin_dashboard_view, name="admin_dashboard"),
    path("admin_new/bookings/", views.bookings_management_view, name="bookings_management"),
    path("admin_new/bookings/<int:booking_id>/", views.booking_detail_view, name="booking_detail"),
    path("admin_new/api/booking/<int:booking_id>/", views.get_booking_details_ajax, name="get_booking_details_ajax"),
    path("admin_new/bookings/add/", views.admin_add_booking_view, name="admin_add_booking"),
    path("admin_new/bookings/cancel/<int:booking_id>/", views.cancel_booking_view, name="cancel_booking"),
    path("admin_new/bookings/activate/<int:booking_id>/", views.activate_booking_view, name="activate_booking"),
    path("admin_new/vehicles/", views.admin_vehicles_view, name="admin_vehicles"),
    path("admin_new/queries/", views.admin_queries_view, name="admin_queries"),
    path("admin_new/customers/", views.admin_customers_view, name="admin_customers"),
    
    # Payments Management URLs (consolidated)
     path("admin_new/bookings/return/<int:booking_id>/", views.return_vehicle_view, name="return_vehicle"),
   path("admin_new/payments/", views.admin_payments_view, name="admin_payments"),
    path("admin_new/payments/add/", views.payment_form_view, name="payment_add"), # Corrected: Added trailing slash
    path("admin_new/payments/edit/<int:payment_id>/", views.payment_form_view, name="payment_edit"), # Corrected: Added trailing slash
    path("admin_new/payments/delete/<int:payment_id>/", views.payment_delete_view, name="payment_delete"),

    path("admin_new/api/data/", views.get_dashboard_data_ajax, name="get_dashboard_data_ajax"),
    path("admin_new/change-password/", views.change_password_view, name="change_password"),
    # CORRECTED: Use the consolidated verification view and pass the action
    path("admin_new/customer/verify/<int:customer_id>/", views.update_customer_verification_view, {'action': 'verify'}, name="verify_customer"),
    path("admin_new/customer/unverify/<int:customer_id>/", views.update_customer_verification_view, {'action': 'unverify'}, name="unverify_customer"),

         # New Self-Join Report URL
    path("admin_new/payments/analytics/", views.payment_analytics_view, name="payment_analytics_report"),

]