from django.urls import path
from . import views

app_name = 'booking'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('routes/<int:route_id>/buses/', views.buses_view, name='buses'),
    path('route-bus/<int:route_bus_id>/seats/', views.seat_selection_view, name='seat_selection'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('confirm-booking/', views.confirm_booking_view, name='confirm_booking'),
    path('booking/<int:booking_id>/confirmation/', views.booking_confirmation_view, name='booking_confirmation'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('booking/<int:booking_id>/cancel/', views.cancel_booking_view, name='cancel_booking'),
]
