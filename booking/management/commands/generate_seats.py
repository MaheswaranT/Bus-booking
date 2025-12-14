from django.core.management.base import BaseCommand
from booking.models import Bus, Seat


class Command(BaseCommand):
    help = 'Generate seats for a bus based on its seat layout configuration'

    def add_arguments(self, parser):
        parser.add_argument('bus_id', type=int, help='Bus ID to generate seats for')

    def handle(self, *args, **options):
        bus_id = options['bus_id']
        try:
            bus = Bus.objects.get(id=bus_id)
        except Bus.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Bus with ID {bus_id} does not exist.'))
            return

        # Get seat layout configuration
        seat_layout = bus.get_seat_layout_config()
        rows = seat_layout.get('rows', 0)
        cols_per_side = seat_layout.get('cols_per_side', [0, 0])
        
        if rows == 0 or sum(cols_per_side) == 0:
            self.stdout.write(self.style.ERROR('Invalid seat layout configuration.'))
            return

        # Delete existing seats
        Seat.objects.filter(bus=bus).delete()
        self.stdout.write(f'Deleted existing seats for bus {bus.name}')

        # Generate seats
        seat_count = 0
        
        for row in range(1, rows + 1):
            # Left side seats
            for col in range(1, cols_per_side[0] + 1):
                seat_letter = chr(64 + col)  # A, B, C, etc.
                seat_type = 'Window' if col == 1 else ('Aisle' if col == cols_per_side[0] else 'Middle')
                Seat.objects.create(
                    bus=bus,
                    seat_number=f'{row}{seat_letter}',  # 1A, 1B, etc.
                    row=row,
                    column=col,
                    seat_type=seat_type
                )
                seat_count += 1
            
            # Right side seats
            for col in range(cols_per_side[0] + 1, cols_per_side[0] + cols_per_side[1] + 1):
                col_index = col - cols_per_side[0]
                seat_letter = chr(64 + cols_per_side[0] + col_index)  # Continue from left side
                seat_type = 'Window' if col_index == cols_per_side[1] else ('Aisle' if col_index == 1 else 'Middle')
                Seat.objects.create(
                    bus=bus,
                    seat_number=f'{row}{seat_letter}',
                    row=row,
                    column=col,
                    seat_type=seat_type
                )
                seat_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'Successfully generated {seat_count} seats for bus {bus.name}'
        ))

