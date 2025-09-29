# rental/urls.py
from django.urls import path
from . import views

urlpatterns = [  
    # Custom admin dashboard URLs
    path("", views.admin_dashboard_view, name="admin_dashboard"),
    path("maintenance/", views.admin_maintenance_view, name="admin_maintenance"),
    path("bookings/", views.bookings_management_view, name="bookings_management"),
    path("queries/", views.admin_queries_view, name="admin_queries"),
    
    # Payments Management URLs (consolidated)
    path("bookings/return/<int:booking_id>/", views.return_vehicle_view, name="return_vehicle"),
    path("payments/", views.admin_payments_view, name="admin_payments"),
    path("payments/add/", views.payment_form_view, name="payment_add"),
    path("payments/edit/<int:payment_id>/", views.payment_form_view, name="payment_edit"),
    path("payments/delete/<int:payment_id>/", views.payment_delete_view, name="payment_delete"),

    path("api/data/", views.get_dashboard_data, name="get_dashboard_data"),
    path("change-password/", views.change_password_view, name="change_password"),

         # New Self-Join Report URL
    path("payments/analytics/", views.payment_analytics_view, name="payment_analytics_report"),

]