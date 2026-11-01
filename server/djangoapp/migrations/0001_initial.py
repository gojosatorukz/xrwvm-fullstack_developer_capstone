import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name='CarMake',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('description', models.TextField(blank=True)),
            ],
            options={'ordering': ['name']},
        ),
        migrations.CreateModel(
            name='CarModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('dealer_id', models.PositiveIntegerField(default=1)),
                ('name', models.CharField(max_length=100)),
                ('type', models.CharField(choices=[('Sedan', 'Sedan'),
                    ('SUV', 'SUV'), ('Wagon', 'Wagon'), ('Truck', 'Truck'),
                    ('Coupe', 'Coupe')], default='Sedan', max_length=10)),
                ('year', models.PositiveIntegerField(default=2023, validators=[
                    django.core.validators.MinValueValidator(2015),
                    django.core.validators.MaxValueValidator(2023)])),
                ('car_make', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                    related_name='models', to='djangoapp.carmake')),
            ],
            options={
                'ordering': ['car_make__name', 'name', 'year'],
                'constraints': [models.UniqueConstraint(
                    fields=('car_make', 'name', 'year'), name='unique_car_model_year')],
            },
        ),
    ]
