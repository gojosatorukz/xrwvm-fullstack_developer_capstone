"""Idempotent sample catalogue for the course demonstration."""
from django.db import transaction
from .models import CarMake, CarModel


@transaction.atomic
def initiate():
    catalogue = {
        'Toyota': [('Camry', 'Sedan'), ('RAV4', 'SUV'), ('Corolla', 'Sedan')],
        'Honda': [('Civic', 'Sedan'), ('Accord', 'Sedan'), ('CR-V', 'SUV')],
        'Ford': [('Mustang', 'Coupe'), ('Explorer', 'SUV'), ('F-150', 'Truck')],
        'BMW': [('3 Series', 'Sedan'), ('X5', 'SUV')],
        'Audi': [('A4', 'Sedan'), ('Q5', 'SUV')],
        'Tesla': [('Model 3', 'Sedan'), ('Model Y', 'SUV')],
    }
    for make_name, models in catalogue.items():
        make, _ = CarMake.objects.get_or_create(
            name=make_name, defaults={'description': f'{make_name} vehicles'})
        for name, kind in models:
            CarModel.objects.get_or_create(
                car_make=make, name=name, year=2023,
                defaults={'type': kind, 'dealer_id': 1})
    return CarMake.objects.count(), CarModel.objects.count()
