"""
Management command to populate database with sample categories and subtypes.
Usage: python manage.py populate_categories
"""
from django.core.management.base import BaseCommand
from apps.services.models import Category, SubType, Pricing
from decimal import Decimal


class Command(BaseCommand):
    help = 'Populate database with sample categories and subtypes'

    def handle(self, *args, **options):
        self.stdout.write('Creating categories and subtypes...')

        # Create Halı Yıkama category
        hali_category, created = Category.objects.get_or_create(
            name='Halı Yıkama',
            defaults={
                'slug': 'hali-yikama',
                'description': 'Profesyonel halı yıkama hizmeti',
                'icon': '🧼',
                'pricing_type': 'per_sqm',
                'is_active': True,
                'order_priority': 1,
                'requires_pickup_delivery': True,
                'min_days_between_pickup_delivery': 7,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Created category: {hali_category.name}'))

        # Halı Yıkama subtypes
        hali_subtypes = [
            {'name': 'Kilim', 'slug': 'kilim', 'description': 'Geleneksel kilim yıkama', 'price': Decimal('150.00')},
            {'name': 'Yün Halı', 'slug': 'yun-hali', 'description': 'Yün halı yıkama', 'price': Decimal('200.00')},
            {'name': 'İpek Halı', 'slug': 'ipek-hali', 'description': 'İpek halı özel yıkama', 'price': Decimal('300.00')},
            {'name': 'Antika Halı', 'slug': 'antika-hali', 'description': 'Antika halı özel bakım', 'price': Decimal('350.00')},
        ]

        for subtype_data in hali_subtypes:
            price = subtype_data.pop('price')
            subtype, created = SubType.objects.get_or_create(
                category=hali_category,
                name=subtype_data['name'],
                defaults=subtype_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Created subtype: {subtype.name}'))
                # Create pricing
                Pricing.objects.create(
                    subtype=subtype,
                    base_price=price,
                    currency='TRY',
                    is_active=True
                )
                self.stdout.write(self.style.SUCCESS(f'    ✓ Created pricing: {price} TRY'))

        # Create Koltuk Yıkama category
        koltuk_category, created = Category.objects.get_or_create(
            name='Koltuk Yıkama',
            defaults={
                'slug': 'koltuk-yikama',
                'description': 'Profesyonel koltuk yıkama ve temizleme',
                'icon': '🛋️',
                'pricing_type': 'per_item',
                'is_active': True,
                'order_priority': 2,
                'requires_time_selection': True,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Created category: {koltuk_category.name}'))

        # Koltuk Yıkama subtypes
        koltuk_subtypes = [
            {'name': 'Tekli Koltuk', 'slug': 'tekli-koltuk', 'description': 'Tekli koltuk yıkama', 'price': Decimal('250.00')},
            {'name': 'İkili Koltuk', 'slug': 'ikili-koltuk', 'description': 'İkili koltuk yıkama', 'price': Decimal('400.00')},
            {'name': 'Üçlü Koltuk', 'slug': 'uclu-koltuk', 'description': 'Üçlü koltuk yıkama', 'price': Decimal('550.00')},
            {'name': 'L Koltuk', 'slug': 'l-koltuk', 'description': 'L tipi köşe koltuk yıkama', 'price': Decimal('700.00')},
            {'name': 'Chester Koltuk', 'slug': 'chester-koltuk', 'description': 'Chester koltuk özel yıkama', 'price': Decimal('800.00')},
        ]

        for subtype_data in koltuk_subtypes:
            price = subtype_data.pop('price')
            subtype, created = SubType.objects.get_or_create(
                category=koltuk_category,
                name=subtype_data['name'],
                defaults=subtype_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Created subtype: {subtype.name}'))
                Pricing.objects.create(
                    subtype=subtype,
                    base_price=price,
                    currency='TRY',
                    is_active=True
                )
                self.stdout.write(self.style.SUCCESS(f'    ✓ Created pricing: {price} TRY'))

        # Create Perde Yıkama category
        perde_category, created = Category.objects.get_or_create(
            name='Perde Yıkama',
            defaults={
                'slug': 'perde-yikama',
                'description': 'Profesyonel perde yıkama hizmeti',
                'icon': '🪟',
                'pricing_type': 'per_sqm',
                'is_active': True,
                'order_priority': 3,
                'requires_pickup_delivery': True,
                'min_days_between_pickup_delivery': 5,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Created category: {perde_category.name}'))

        # Perde Yıkama subtypes
        perde_subtypes = [
            {'name': 'Tül Perde', 'slug': 'tul-perde', 'description': 'Tül perde yıkama', 'price': Decimal('80.00')},
            {'name': 'Fon Perde', 'slug': 'fon-perde', 'description': 'Fon perde yıkama', 'price': Decimal('120.00')},
            {'name': 'Stor Perde', 'slug': 'stor-perde', 'description': 'Stor perde temizleme', 'price': Decimal('100.00')},
        ]

        for subtype_data in perde_subtypes:
            price = subtype_data.pop('price')
            subtype, created = SubType.objects.get_or_create(
                category=perde_category,
                name=subtype_data['name'],
                defaults=subtype_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Created subtype: {subtype.name}'))
                Pricing.objects.create(
                    subtype=subtype,
                    base_price=price,
                    currency='TRY',
                    is_active=True
                )
                self.stdout.write(self.style.SUCCESS(f'    ✓ Created pricing: {price} TRY'))

        self.stdout.write(self.style.SUCCESS('\n✅ Database populated successfully!'))
        self.stdout.write(f'Total categories: {Category.objects.count()}')
        self.stdout.write(f'Total subtypes: {SubType.objects.count()}')
