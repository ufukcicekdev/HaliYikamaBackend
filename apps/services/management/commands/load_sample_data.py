from django.core.management.base import BaseCommand
from apps.services.models import Category, SubType, Pricing, District, BookingSettings
from decimal import Decimal


class Command(BaseCommand):
    help = 'Load sample categories, subtypes, and pricing data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Loading sample data...')

        # Create districts
        districts_data = [
            {'name': 'Kadıköy', 'delivery_fee': '50.00', 'order_priority': 1},
            {'name': 'Beşiktaş', 'delivery_fee': '50.00', 'order_priority': 2},
            {'name': 'Şişli', 'delivery_fee': '50.00', 'order_priority': 3},
            {'name': 'Üsküdar', 'delivery_fee': '50.00', 'order_priority': 4},
            {'name': 'Bakırköy', 'delivery_fee': '60.00', 'order_priority': 5},
            {'name': 'Beyoğlu', 'delivery_fee': '50.00', 'order_priority': 6},
            {'name': 'Fatih', 'delivery_fee': '55.00', 'order_priority': 7},
            {'name': 'Maltepe', 'delivery_fee': '70.00', 'order_priority': 8},
        ]

        for district_data in districts_data:
            District.objects.get_or_create(
                name=district_data['name'],
                defaults={
                    'delivery_fee': district_data['delivery_fee'],
                    'order_priority': district_data['order_priority'],
                    'is_active': True
                }
            )
        self.stdout.write(self.style.SUCCESS(f'✓ {len(districts_data)} ilçe eklendi'))

        # Create categories with subtypes
        categories_data = [
            {
                'name': 'Halı Yıkama',
                'slug': 'hali-yikama',
                'description': 'Her türlü halı için profesyonel yıkama hizmeti',
                'icon': '🏛️',
                'pricing_type': 'per_sqm',
                'requires_time_selection': False,
                'requires_pickup_delivery': True,
                'min_days_between_pickup_delivery': 7,
                'subtypes': [
                    {'name': 'Yünlü Halı', 'slug': 'yun-hali', 'price': '45.00'},
                    {'name': 'Kilim', 'slug': 'kilim', 'price': '35.00'},
                    {'name': 'İpek Halı', 'slug': 'ipek-hali', 'price': '85.00'},
                    {'name': 'Bambu Halı', 'slug': 'bambu-hali', 'price': '40.00'},
                    {'name': 'Polyester Halı', 'slug': 'polyester-hali', 'price': '30.00'},
                    {'name': 'Shaggy Halı', 'slug': 'shaggy-hali', 'price': '50.00'},
                ]
            },
            {
                'name': 'Koltuk Yıkama',
                'slug': 'koltuk-yikama',
                'description': 'Tüm koltuk tipleri için derin temizlik',
                'icon': '🛋️',
                'pricing_type': 'per_item',
                'requires_time_selection': True,
                'requires_pickup_delivery': False,
                'min_days_between_pickup_delivery': 0,
                'subtypes': [
                    {'name': 'Tekli Koltuk', 'slug': 'tekli-koltuk', 'price': '250.00'},
                    {'name': 'İkili Koltuk', 'slug': 'ikili-koltuk', 'price': '400.00'},
                    {'name': 'Üçlü Koltuk', 'slug': 'uclu-koltuk', 'price': '550.00'},
                    {'name': 'L Koltuk', 'slug': 'l-koltuk', 'price': '750.00'},
                    {'name': 'Berjer', 'slug': 'berjer', 'price': '200.00'},
                    {'name': 'Chester Koltuk', 'slug': 'chester-koltuk', 'price': '600.00'},
                ]
            },
            {
                'name': 'Yorgan Yıkama',
                'slug': 'yorgan-yikama',
                'description': 'Yorgan, battaniye ve yatak örtüleri',
                'icon': '🛏️',
                'pricing_type': 'per_item',
                'subtypes': [
                    {'name': 'Tek Kişilik Yorgan', 'slug': 'tek-yorgan', 'price': '150.00'},
                    {'name': 'Çift Kişilik Yorgan', 'slug': 'cift-yorgan', 'price': '200.00'},
                    {'name': 'Battaniye', 'slug': 'battaniye', 'price': '100.00'},
                    {'name': 'Yatak Örtüsü', 'slug': 'yatak-ortusu', 'price': '120.00'},
                    {'name': 'Nevresim Takımı', 'slug': 'nevresim', 'price': '80.00'},
                    {'name': 'Pike', 'slug': 'pike', 'price': '90.00'},
                ]
            },
            {
                'name': 'Perde Yıkama',
                'slug': 'perde-yikama',
                'description': 'Tül ve kalın perde temizliği',
                'icon': '🪟',
                'pricing_type': 'per_sqm',
                'subtypes': [
                    {'name': 'Tül Perde', 'slug': 'tul-perde', 'price': '25.00'},
                    {'name': 'Kalın Perde', 'slug': 'kalin-perde', 'price': '35.00'},
                    {'name': 'Fon Perde', 'slug': 'fon-perde', 'price': '30.00'},
                    {'name': 'Stor Perde', 'slug': 'stor-perde', 'price': '40.00'},
                    {'name': 'Zebra Perde', 'slug': 'zebra-perde', 'price': '38.00'},
                    {'name': 'Jaluzi Perde', 'slug': 'jaluzi-perde', 'price': '35.00'},
                ]
            },
        ]

        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                slug=cat_data['slug'],
                defaults={
                    'name': cat_data['name'],
                    'description': cat_data['description'],
                    'icon': cat_data['icon'],
                    'pricing_type': cat_data['pricing_type'],
                    'is_active': True,
                    'order_priority': categories_data.index(cat_data) + 1,
                    'requires_time_selection': cat_data.get('requires_time_selection', False),
                    'requires_pickup_delivery': cat_data.get('requires_pickup_delivery', False),
                    'min_days_between_pickup_delivery': cat_data.get('min_days_between_pickup_delivery', 7),
                }
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Kategori oluşturuldu: {category.name}'))
            else:
                self.stdout.write(f'  Kategori zaten var: {category.name}')

            # Create subtypes
            for sub_data in cat_data['subtypes']:
                subtype, sub_created = SubType.objects.get_or_create(
                    category=category,
                    slug=sub_data['slug'],
                    defaults={
                        'name': sub_data['name'],
                        'is_active': True,
                        'order_priority': cat_data['subtypes'].index(sub_data) + 1
                    }
                )

                if sub_created:
                    # Create pricing
                    Pricing.objects.create(
                        subtype=subtype,
                        base_price=Decimal(sub_data['price']),
                        currency='TRY',
                        discount_percentage=Decimal('0.00'),
                        is_active=True
                    )
                    self.stdout.write(f'  ✓ Alt tip eklendi: {subtype.name} - {sub_data["price"]}₺')

        # Create booking settings
        settings, created = BookingSettings.objects.get_or_create(
            pk=1,
            defaults={
                'min_cancellation_notice_hours': 2,
                'min_reschedule_notice_hours': 2,
                'cancellation_fee_percentage': Decimal('0.00'),
                'late_cancellation_fee_percentage': Decimal('10.00'),
                'default_service_start_time': '08:00',
                'default_service_end_time': '00:00',
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Rezervasyon ayarları oluşturuldu'))
        else:
            self.stdout.write('  Rezervasyon ayarları zaten var')

        self.stdout.write(self.style.SUCCESS('\n✨ Örnek veriler başarıyla yüklendi!'))
        self.stdout.write(self.style.SUCCESS(f'Toplam {len(categories_data)} kategori ve alt tipleri eklendi'))
