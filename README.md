# Bus Ticket Booking System

A complete Django-based bus ticket booking system with user authentication, route management, seat selection, and booking functionality.

## Features

- **User Authentication**: Registration, login, and logout functionality
- **Route Management**: View and search available routes between locations
- **Bus Selection**: Display buses for selected routes with pricing
- **Interactive Seat Selection**: Visual seat layout with real-time availability
- **Price Calculation**: Dynamic pricing based on route, bus type, and seat count
- **Booking Management**: Complete booking flow with confirmation
- **User Dashboard**: View and manage booking history
- **Admin Panel**: CRUD operations for locations, routes, buses, and bookings

## Tech Stack

- **Backend**: Python 3.x, Django 4.2+
- **Database**: SQLite
- **Frontend**: Bootstrap 5, HTML5, CSS3, JavaScript

## Installation

1. **Clone or navigate to the project directory**

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run migrations**:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

4. **Create a superuser** (for admin access):
   ```bash
   python manage.py createsuperuser
   ```

5. **Run the development server**:
   ```bash
   python manage.py runserver
   ```

6. **Access the application**:
   - Home page: http://127.0.0.1:8000/
   - Admin panel: http://127.0.0.1:8000/admin/

## Setting Up Sample Data

### 1. Create Locations

Go to the admin panel and create locations (e.g., "New York", "Boston", "Philadelphia").

### 2. Create Routes

Create routes between locations with distance and base price.

### 3. Create Buses

Create buses with the following information:
- Name (e.g., "Express Bus 1")
- Bus Type (AC, Non-AC, Sleeper, Semi-sleeper)
- Total Seats
- Seat Layout (JSON format): `{"rows": 10, "cols_per_side": [2, 2]}`

Example seat layout configurations:
- 2-2 configuration: `{"rows": 10, "cols_per_side": [2, 2]}` (20 seats)
- 2-3 configuration: `{"rows": 10, "cols_per_side": [2, 3]}` (25 seats)

### 4. Generate Seats for Buses

After creating a bus, generate seats using the management command:
```bash
python manage.py generate_seats <bus_id>
```

Replace `<bus_id>` with the actual bus ID from the admin panel.

### 5. Create Route-Bus Assignments

In the admin panel, create RouteBus entries to link buses to routes with:
- Route
- Bus
- Departure Time
- Arrival Time
- Available Days (JSON array: [0,1,2,3,4,5,6] where 0=Monday, 6=Sunday)

## Usage

1. **Register/Login**: Create an account or login
2. **Browse Routes**: Search and filter available routes
3. **Select Bus**: Choose a bus for your route
4. **Select Seats**: Pick your preferred seats from the interactive layout
5. **Checkout**: Review and confirm your booking
6. **View Bookings**: Access your dashboard to see all bookings

## Project Structure

```
busticket/
├── busticket/          # Main project settings
├── booking/            # Main booking app
│   ├── models.py       # Database models
│   ├── views.py        # View functions
│   ├── urls.py         # URL routing
│   ├── admin.py        # Admin interface
│   └── management/     # Management commands
├── accounts/           # Authentication app
│   ├── views.py        # Auth views
│   └── urls.py         # Auth URLs
├── templates/          # HTML templates
├── static/             # Static files (CSS, JS)
└── manage.py           # Django management script
```

## Price Calculation

The system calculates prices using:
- Base price from the route
- Bus type multiplier:
  - Non-AC: 1.0x
  - AC: 1.3x
  - Semi-sleeper: 1.5x
  - Sleeper: 1.8x
- Total = (base_price × multiplier) × number_of_seats

## Admin Features

The admin panel allows you to:
- Manage locations (add, edit, delete)
- Manage routes (add, edit, delete)
- Manage buses (add, edit, delete)
- Configure seat layouts
- Assign buses to routes
- View and manage bookings
- View booking details with seat information

## Notes

- The payment system is simulated (no real payment gateway)
- Seat availability is checked in real-time
- Bookings are confirmed immediately upon checkout
- Users can cancel bookings from their dashboard

## License

This project is open source and available for educational purposes.

