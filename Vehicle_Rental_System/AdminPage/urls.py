# rental/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [  
    # Authentication URLs
    path("login/", auth_views.LoginView.as_view(
        template_name='admin/login_standalone.html',
        redirect_authenticated_user=True,
        next_page='/admin_new/'
    ), name="admin_login"),
    path("logout/", auth_views.LogoutView.as_view(
        template_name='admin/logout.html',
        next_page='admin_login'
    ), name="admin_logout"),
    
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
    path("test-mysql-views/", views.test_mysql_views, name="test_mysql_views"),

    # New Self-Join Report URL
    path("payments/analytics/", views.payment_analytics_view, name="payment_analytics_report"),
    
    # New Payment Trends URL
    path("payments/trends/", views.payment_trends_view, name="payment_trends"),
    
    # Activity Log URL
    path("activity-log/", views.activity_log_view, name="activity_log"),
]