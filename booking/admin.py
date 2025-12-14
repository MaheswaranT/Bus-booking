from django.contrib import admin
from .models import Location, Route, Bus, RouteBus, Seat, Booking, BookingSeat


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'code']
    ordering = ['name']


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ['origin', 'destination', 'distance', 'base_price', 'created_at']
    list_filter = ['created_at', 'origin', 'destination']
    search_fields = ['origin__name', 'destination__name']
    ordering = ['origin', 'destination']
    autocomplete_fields = ['origin', 'destination']


class SeatInline(admin.TabularInline):
    model = Seat
    extra = 0
    fields = ['seat_number', 'row', 'column', 'seat_type', 'is_active']
    readonly_fields = ['seat_number', 'row', 'column']


@admin.register(Bus)
class BusAdmin(admin.ModelAdmin):
    list_display = ['name', 'bus_type', 'total_seats', 'created_at']
    list_filter = ['bus_type', 'created_at']
    search_fields = ['name']
    ordering = ['name']
    inlines = [SeatInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'bus_type', 'total_seats')
        }),
        ('Seat Layout Configuration', {
            'fields': ('seat_layout',),
            'description': 'JSON format: {"rows": number, "cols_per_side": [left, right]}'
        }),
    )


@admin.register(RouteBus)
class RouteBusAdmin(admin.ModelAdmin):
    list_display = ['route', 'bus', 'departure_time', 'arrival_time', 'created_at']
    list_filter = ['created_at', 'bus__bus_type', 'route']
    search_fields = ['route__origin__name', 'route__destination__name', 'bus__name']
    ordering = ['route', 'departure_time']
    autocomplete_fields = ['route', 'bus']
    
    fieldsets = (
        ('Route and Bus', {
            'fields': ('route', 'bus')
        }),
        ('Schedule', {
            'fields': ('departure_time', 'arrival_time', 'available_days')
        }),
    )


@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ['bus', 'seat_number', 'row', 'column', 'seat_type', 'is_active']
    list_filter = ['bus', 'seat_type', 'is_active']
    search_fields = ['bus__name', 'seat_number']
    ordering = ['bus', 'row', 'column']
    autocomplete_fields = ['bus']


class BookingSeatInline(admin.TabularInline):
    model = BookingSeat
    extra = 0
    readonly_fields = ['seat', 'price']
    can_delete = False


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'route_bus', 'booking_date', 'travel_date', 'total_price', 'status', 'created_at']
    list_filter = ['status', 'created_at', 'booking_date', 'travel_date']
    search_fields = ['user__username', 'route_bus__route__origin__name', 'route_bus__route__destination__name']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [BookingSeatInline]
    
    fieldsets = (
        ('User and Route', {
            'fields': ('user', 'route_bus')
        }),
        ('Booking Details', {
            'fields': ('booking_date', 'travel_date', 'total_price', 'status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(BookingSeat)
class BookingSeatAdmin(admin.ModelAdmin):
    list_display = ['booking', 'seat', 'price']
    list_filter = ['booking__status', 'booking__created_at']
    search_fields = ['booking__user__username', 'seat__seat_number']
    ordering = ['booking', 'seat']
    autocomplete_fields = ['booking', 'seat']
