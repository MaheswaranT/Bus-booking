from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
import json


class Location(models.Model):
    """Store origin and destination locations"""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"


class Route(models.Model):
    """Define bus routes between locations"""
    origin = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='origin_routes')
    destination = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='destination_routes')
    distance = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    base_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['origin', 'destination']
        ordering = ['origin', 'destination']

    def __str__(self):
        return f"{self.origin.name} → {self.destination.name}"


class Bus(models.Model):
    """Store bus information"""
    BUS_TYPE_CHOICES = [
        ('AC', 'AC'),
        ('Non-AC', 'Non-AC'),
        ('Sleeper', 'Sleeper'),
        ('Semi-sleeper', 'Semi-sleeper'),
    ]

    name = models.CharField(max_length=100)
    bus_type = models.CharField(max_length=20, choices=BUS_TYPE_CHOICES)
    total_seats = models.PositiveIntegerField()
    seat_layout = models.JSONField(default=dict, help_text="JSON format: {'rows': number, 'cols_per_side': [left, right]}")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.bus_type})"

    def get_seat_layout_config(self):
        """Return seat layout configuration"""
        if isinstance(self.seat_layout, str):
            return json.loads(self.seat_layout)
        return self.seat_layout or {'rows': 0, 'cols_per_side': [0, 0]}


class RouteBus(models.Model):
    """Link buses to routes (many-to-many relationship)"""
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='route_buses')
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE, related_name='bus_routes')
    departure_time = models.TimeField()
    arrival_time = models.TimeField()
    available_days = models.JSONField(
        default=list,
        help_text="List of days (0=Monday, 6=Sunday) when bus is available"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['route', 'bus', 'departure_time']
        ordering = ['route', 'departure_time']

    def __str__(self):
        return f"{self.route} - {self.bus.name} ({self.departure_time})"


class Seat(models.Model):
    """Individual seat information"""
    SEAT_TYPE_CHOICES = [
        ('Window', 'Window'),
        ('Aisle', 'Aisle'),
        ('Middle', 'Middle'),
    ]

    bus = models.ForeignKey(Bus, on_delete=models.CASCADE, related_name='seats')
    seat_number = models.CharField(max_length=10)
    row = models.PositiveIntegerField()
    column = models.PositiveIntegerField()
    seat_type = models.CharField(max_length=10, choices=SEAT_TYPE_CHOICES, default='Window')
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ['bus', 'seat_number']
        ordering = ['bus', 'row', 'column']

    def __str__(self):
        return f"{self.bus.name} - Seat {self.seat_number}"


class Booking(models.Model):
    """Store booking information"""
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    route_bus = models.ForeignKey(RouteBus, on_delete=models.CASCADE, related_name='bookings')
    booking_date = models.DateField()
    travel_date = models.DateField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Booking #{self.id} - {self.user.username} - {self.route_bus}"

    def get_seats(self):
        """Get all seats for this booking"""
        return self.booking_seats.all()


class BookingSeat(models.Model):
    """Link seats to bookings"""
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='booking_seats')
    seat = models.ForeignKey(Seat, on_delete=models.CASCADE, related_name='bookings')
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])

    class Meta:
        unique_together = ['booking', 'seat']
        ordering = ['booking', 'seat']

    def __str__(self):
        return f"{self.booking} - {self.seat}"

