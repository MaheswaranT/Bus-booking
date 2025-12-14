from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from datetime import date, timedelta
from .models import Location, Route, Bus, RouteBus, Seat, Booking, BookingSeat
from decimal import Decimal


def home_view(request):
    """Home page with route selection"""
    routes = Route.objects.all().select_related('origin', 'destination')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        routes = routes.filter(
            Q(origin__name__icontains=search_query) |
            Q(destination__name__icontains=search_query) |
            Q(origin__code__icontains=search_query) |
            Q(destination__code__icontains=search_query)
        )
    
    # Filter by origin
    origin_filter = request.GET.get('origin', '')
    if origin_filter:
        routes = routes.filter(origin_id=origin_filter)
    
    # Filter by destination
    dest_filter = request.GET.get('destination', '')
    if dest_filter:
        routes = routes.filter(destination_id=dest_filter)
    
    locations = Location.objects.all().order_by('name')
    
    context = {
        'routes': routes,
        'locations': locations,
        'search_query': search_query,
        'origin_filter': origin_filter,
        'dest_filter': dest_filter,
    }
    
    return render(request, 'home.html', context)


def buses_view(request, route_id):
    """Display buses for a selected route"""
    route = get_object_or_404(Route, id=route_id)
    route_buses = RouteBus.objects.filter(route=route).select_related('bus', 'route')
    
    # Filter by travel date if provided
    travel_date = request.GET.get('travel_date', '')
    if travel_date:
        try:
            travel_date_obj = date.fromisoformat(travel_date)
            # Filter buses available on that day of week (0=Monday, 6=Sunday)
            day_of_week = travel_date_obj.weekday()
            route_buses = [
                rb for rb in route_buses 
                if day_of_week in (rb.available_days if isinstance(rb.available_days, list) else [])
            ]
        except ValueError:
            pass
    
    # Calculate prices for each bus
    buses_with_prices = []
    for route_bus in route_buses:
        price = calculate_bus_price(route, route_bus.bus)
        buses_with_prices.append({
            'route_bus': route_bus,
            'price': price,
        })
    
    context = {
        'route': route,
        'buses_with_prices': buses_with_prices,
        'travel_date': travel_date,
    }
    
    return render(request, 'buses.html', context)


def calculate_bus_price(route, bus):
    """Calculate price based on route base price and bus type"""
    base_price = route.base_price
    
    # Bus type multipliers
    bus_multipliers = {
        'Non-AC': Decimal('1.0'),
        'AC': Decimal('1.3'),
        'Semi-sleeper': Decimal('1.5'),
        'Sleeper': Decimal('1.8'),
    }
    
    multiplier = bus_multipliers.get(bus.bus_type, Decimal('1.0'))
    return base_price * multiplier


@login_required
def seat_selection_view(request, route_bus_id):
    """Display seat layout and handle seat selection"""
    route_bus = get_object_or_404(RouteBus, id=route_bus_id)
    bus = route_bus.bus
    route = route_bus.route
    
    # Get travel date
    travel_date = request.GET.get('travel_date', '')
    if not travel_date:
        travel_date = (date.today() + timedelta(days=1)).isoformat()
    
    try:
        travel_date_obj = date.fromisoformat(travel_date)
    except ValueError:
        travel_date_obj = date.today() + timedelta(days=1)
        travel_date = travel_date_obj.isoformat()
    
    # Get all seats for this bus
    seats = Seat.objects.filter(bus=bus, is_active=True).order_by('row', 'column')
    
    # Get booked seats for this route_bus on the travel date
    booked_seats = set()
    bookings = Booking.objects.filter(
        route_bus=route_bus,
        travel_date=travel_date_obj,
        status__in=['Pending', 'Confirmed']
    )
    for booking in bookings:
        booked_seats.update(booking.booking_seats.values_list('seat_id', flat=True))
    
    # Organize seats by row
    seat_layout_config = bus.get_seat_layout_config()
    rows = seat_layout_config.get('rows', 0)
    cols_per_side = seat_layout_config.get('cols_per_side', [0, 0])
    
    # Build seat rows for template
    seat_rows = []
    for row_num in range(1, rows + 1):
        row_seats = []
        # Left side seats
        for col_num in range(1, cols_per_side[0] + 1):
            seat = next((s for s in seats if s.row == row_num and s.column == col_num), None)
            if seat:
                row_seats.append({
                    'seat': seat,
                    'is_booked': seat.id in booked_seats,
                    'side': 'left'
                })
            else:
                row_seats.append(None)
        
        # Right side seats
        for col_num in range(cols_per_side[0] + 1, cols_per_side[0] + cols_per_side[1] + 1):
            seat = next((s for s in seats if s.row == row_num and s.column == col_num), None)
            if seat:
                row_seats.append({
                    'seat': seat,
                    'is_booked': seat.id in booked_seats,
                    'side': 'right'
                })
            else:
                row_seats.append(None)
        
        seat_rows.append({
            'row_num': row_num,
            'seats': row_seats,
            'left_count': cols_per_side[0],
            'right_count': cols_per_side[1]
        })
    
    # Calculate price per seat
    price_per_seat = calculate_bus_price(route, bus)
    
    context = {
        'route_bus': route_bus,
        'route': route,
        'bus': bus,
        'seats': seats,
        'seat_rows': seat_rows,
        'rows': rows,
        'cols_per_side': cols_per_side,
        'travel_date': travel_date,
        'price_per_seat': price_per_seat,
    }
    
    return render(request, 'seat_selection.html', context)


@login_required
def checkout_view(request):
    """Checkout page for booking confirmation"""
    if request.method == 'POST':
        route_bus_id = request.POST.get('route_bus_id')
        seat_ids = request.POST.getlist('selected_seats')
        travel_date = request.POST.get('travel_date')
        
        if not route_bus_id or not seat_ids or not travel_date:
            messages.error(request, 'Missing booking information.')
            return redirect('booking:home')
        
        try:
            route_bus = RouteBus.objects.get(id=route_bus_id)
            travel_date_obj = date.fromisoformat(travel_date)
            seats = Seat.objects.filter(id__in=seat_ids, bus=route_bus.bus)
            
            if seats.count() != len(seat_ids):
                messages.error(request, 'Invalid seat selection.')
                return redirect('booking:home')
            
            # Check if seats are available
            booked_seats = set()
            bookings = Booking.objects.filter(
                route_bus=route_bus,
                travel_date=travel_date_obj,
                status__in=['Pending', 'Confirmed']
            )
            for booking in bookings:
                booked_seats.update(booking.booking_seats.values_list('seat_id', flat=True))
            
            selected_seat_ids = [int(sid) for sid in seat_ids]
            if any(sid in booked_seats for sid in selected_seat_ids):
                messages.error(request, 'Some selected seats are already booked.')
                return redirect('seat_selection', route_bus_id=route_bus_id)
            
            # Calculate total price
            price_per_seat = calculate_bus_price(route_bus.route, route_bus.bus)
            total_price = price_per_seat * len(seat_ids)
            
            context = {
                'route_bus': route_bus,
                'route': route_bus.route,
                'bus': route_bus.bus,
                'seats': seats,
                'travel_date': travel_date,
                'travel_date_obj': travel_date_obj,
                'price_per_seat': price_per_seat,
                'total_price': total_price,
            }
            
            return render(request, 'checkout.html', context)
            
        except (RouteBus.DoesNotExist, ValueError, Seat.DoesNotExist) as e:
            messages.error(request, 'Invalid booking information.')
            return redirect('booking:home')
    
    messages.error(request, 'Invalid request.')
    return redirect('booking:home')


@login_required
def confirm_booking_view(request):
    """Process and confirm the booking"""
    if request.method == 'POST':
        route_bus_id = request.POST.get('route_bus_id')
        seat_ids = request.POST.getlist('selected_seats')
        travel_date = request.POST.get('travel_date')
        
        if not route_bus_id or not seat_ids or not travel_date:
            messages.error(request, 'Missing booking information.')
            return redirect('booking:home')
        
        try:
            route_bus = RouteBus.objects.get(id=route_bus_id)
            travel_date_obj = date.fromisoformat(travel_date)
            seats = Seat.objects.filter(id__in=seat_ids, bus=route_bus.bus)
            
            # Double-check seat availability
            booked_seats = set()
            bookings = Booking.objects.filter(
                route_bus=route_bus,
                travel_date=travel_date_obj,
                status__in=['Pending', 'Confirmed']
            )
            for booking in bookings:
                booked_seats.update(booking.booking_seats.values_list('seat_id', flat=True))
            
            selected_seat_ids = [int(sid) for sid in seat_ids]
            if any(sid in booked_seats for sid in selected_seat_ids):
                messages.error(request, 'Some selected seats are already booked. Please select different seats.')
                return redirect('seat_selection', route_bus_id=route_bus_id)
            
            # Calculate total price
            price_per_seat = calculate_bus_price(route_bus.route, route_bus.bus)
            total_price = price_per_seat * len(seat_ids)
            
            # Create booking
            booking = Booking.objects.create(
                user=request.user,
                route_bus=route_bus,
                booking_date=date.today(),
                travel_date=travel_date_obj,
                total_price=total_price,
                status='Confirmed'
            )
            
            # Create booking seats
            for seat in seats:
                BookingSeat.objects.create(
                    booking=booking,
                    seat=seat,
                    price=price_per_seat
                )
            
            messages.success(request, f'Booking confirmed! Booking ID: #{booking.id}')
            return redirect('booking:booking_confirmation', booking_id=booking.id)
            
        except Exception as e:
            messages.error(request, f'Error processing booking: {str(e)}')
            return redirect('booking:home')
    
    messages.error(request, 'Invalid request.')
    return redirect('booking:home')


@login_required
def booking_confirmation_view(request, booking_id):
    """Display booking confirmation"""
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    booking_seats = booking.booking_seats.all().select_related('seat')
    
    context = {
        'booking': booking,
        'booking_seats': booking_seats,
    }
    
    return render(request, 'booking_confirmation.html', context)


@login_required
def dashboard_view(request):
    """User dashboard to view booking history"""
    bookings = Booking.objects.filter(user=request.user).select_related(
        'route_bus__route__origin',
        'route_bus__route__destination',
        'route_bus__bus'
    ).order_by('-created_at')
    
    context = {
        'bookings': bookings,
    }
    
    return render(request, 'dashboard.html', context)


@login_required
def cancel_booking_view(request, booking_id):
    """Cancel a booking"""
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    if booking.status == 'Cancelled':
        messages.warning(request, 'This booking is already cancelled.')
        return redirect('booking:dashboard')
    
    if request.method == 'POST':
        booking.status = 'Cancelled'
        booking.save()
        messages.success(request, f'Booking #{booking.id} has been cancelled.')
        return redirect('booking:dashboard')
    
    context = {
        'booking': booking,
    }
    
    return render(request, 'cancel_booking.html', context)
