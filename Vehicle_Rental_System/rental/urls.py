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
    # Specific profile URLs must come before the general one.
    path("profile/edit/", views.edit_profile_view, name="edit_profile"),
    path("profile/change-password/", views.user_change_password_view, name="user_change_password"),
    path("profile/bookings/", views.my_bookings_view, name="my_bookings"),
    path("profile/", views.my_profile_view, name="my_profile"), # General profile URL now at the end.
    path("bookings/confirm-payment/<int:booking_id>/", views.confirm_payment_view, name="confirm_payment"),
    
    # Custom admin dashboard URLs
    path("admin_new/", views.admin_dashboard_view, name="admin_dashboard"),
    path("admin_new/maintenance/", views.admin_maintenance_view, name="admin_maintenance"),
    path("admin_new/bookings/", views.bookings_management_view, name="bookings_management"),
    path("admin_new/bookings/<int:booking_id>/", views.booking_detail_view, name="booking_detail"),
    path("admin_new/bookings/cancel/<int:booking_id>/", views.cancel_booking_view, name="cancel_booking"),
    path("admin_new/bookings/activate/<int:booking_id>/", views.activate_booking_view, name="activate_booking"),
    path("admin_new/bookings/complete/<int:booking_id>/", views.complete_booking_view, name="complete_booking"),
    path("admin_new/queries/", views.admin_queries_view, name="admin_queries"),
    path("admin_new/api/customer/<int:customer_id>/", views.admin_customer_detail_ajax_view, name="admin_customer_detail_ajax"),
    path("admin_new/customers/<int:customer_id>/", views.admin_customer_detail_view, name="admin_customer_detail"),
    path("admin_new/customers/export/", views.export_customers_csv_view, name="export_customers_csv"),
    path("admin_new/customers/", views.admin_customers_view, name="admin_customers"),
    
    # Payments Management URLs (consolidated)
     path("admin_new/bookings/return/<int:booking_id>/", views.return_vehicle_view, name="return_vehicle"),
   path("admin_new/payments/", views.admin_payments_view, name="admin_payments"),
    path("admin_new/payments/add/", views.payment_form_view, name="payment_add"),
    path("admin_new/payments/edit/<int:payment_id>/", views.payment_form_view, name="payment_edit"),
    path("admin_new/payments/delete/<int:payment_id>/", views.payment_delete_view, name="payment_delete"),

    path("admin_new/api/data/", views.get_dashboard_data_ajax, name="get_dashboard_data_ajax"),
     path("admin_new/change-password/", views.change_password_view, name="change_password"),
    path("admin_new/customer/verify/<int:customer_id>/", views.verify_customer_view, name="verify_customer"),
    path("admin_new/customer/unverify/<int:customer_id>/", views.unverify_customer_view, name="unverify_customer"),

         # New Self-Join Report URL
    path("admin_new/payments/analytics/", views.payment_analytics_view, name="payment_analytics_report"),

]