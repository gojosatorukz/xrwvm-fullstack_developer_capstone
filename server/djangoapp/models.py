from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class CarMake(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class CarModel(models.Model):
    car_make = models.ForeignKey(CarMake, on_delete=models.CASCADE, related_name="models")
    dealer_id = models.PositiveIntegerField(default=1)
    name = models.CharField(max_length=100)
    type = models.CharField(
        max_length=10,
        choices=[("Sedan", "Sedan"), ("SUV", "SUV"), ("Wagon", "Wagon"), ("Truck", "Truck"), ("Coupe", "Coupe")],
        default="Sedan",
    )
    year = models.PositiveIntegerField(default=2023, validators=[MinValueValidator(2015), MaxValueValidator(2023)])

    class Meta:
        ordering = ["car_make__name", "name", "year"]
        constraints = [models.UniqueConstraint(fields=["car_make", "name", "year"], name="unique_car_model_year")]

    def __str__(self):
        return f"{self.car_make.name} {self.name} ({self.year})"
