from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from faker import Faker
from unicflo_api.models import (
    User, Category, Product, ProductImage,
    Cart, CartItem, Order, OrderItem, Address, Coupon,
    GenderCategory, Subcategory, Brand, Color, Size, Material, ShippingMethod, ProductVariant, Season
)
import random
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
from django.utils.text import slugify

fake = Faker(['ru_RU'])  # Using Russian locale
User = get_user_model()

class Command(BaseCommand):
    help = 'Generates fake data for testing'

    def add_arguments(self, parser):
        parser.add_argument('--users', type=int, default=10, help='Number of users')
        parser.add_argument('--categories', type=int, default=10, help='Number of categories')
        parser.add_argument('--products', type=int, default=50, help='Number of products')
        parser.add_argument('--reviews', type=int, default=100, help='Number of reviews')
        parser.add_argument('--orders', type=int, default=20, help='Number of orders')

    def generate_unique_slug(self, name, model_class):
        base_slug = slugify(name)
        slug = base_slug
        counter = 1
        while model_class.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        return slug

    def handle(self, *args, **options):
        self.stdout.write('Starting fake data generation...')
        
        fake = Faker('ru_RU')
        users = []
        products = []
        
        # Create users
        for _ in range(options['users']):
            user = User.objects.create_user(
                username=fake.user_name(),
                email=fake.email(),
                password='testpass123',
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                telegram_username=fake.user_name()
            )
            users.append(user)
            self.stdout.write(f'Created user: {user.username}')

        # Create gender categories
        genders = []
        for gender_name in ['Male', 'Female', 'Unisex']:
            gender = GenderCategory.objects.create(
                name=gender_name,
                slug=self.generate_unique_slug(gender_name, GenderCategory),
                description=fake.text()
            )
            genders.append(gender)
            self.stdout.write(f'Created gender category: {gender.name}')

        # Create categories
        categories = []
        for category_name in ['Одежда', 'Обувь', 'Аксессуары']:
            category = Category.objects.create(
                name=category_name,
                slug=self.generate_unique_slug(category_name, Category),
                description=fake.text()
            )
            categories.append(category)
            self.stdout.write(f'Created category: {category.name}')

        # Create subcategories
        subcategories = []
        clothing_subcats = ['Футболки', 'Джинсы', 'Куртки', 'Платья', 'Рубашки']
        shoes_subcats = ['Кроссовки', 'Ботинки', 'Туфли', 'Сандалии']
        accessories_subcats = ['Сумки', 'Ремни', 'Часы', 'Очки']

        for category in categories:
            if category.name == 'Одежда':
                subcats = clothing_subcats
            elif category.name == 'Обувь':
                subcats = shoes_subcats
            else:
                subcats = accessories_subcats

            for subcat_name in subcats:
                for gender in genders:
                    if gender.name != 'Unisex' or category.name == 'Аксессуары':
                        subcategory = Subcategory.objects.create(
                            category=category,
                            gender=gender,
                            name=subcat_name,
                            slug=self.generate_unique_slug(f"{subcat_name}-{gender.name}", Subcategory),
                            description=fake.text()
                        )
                        subcategories.append(subcategory)
                        self.stdout.write(f'Created subcategory: {subcategory.name} for {gender.name}')

        # Create brands
        brands = []
        brand_names = ['Nike', 'Adidas', 'Puma', 'Reebok', 'New Balance', 'Zara', 'H&M', 'Uniqlo']
        for brand_name in brand_names:
            brand = Brand.objects.create(
                name=brand_name,
                slug=self.generate_unique_slug(brand_name, Brand),
                description=fake.text()
            )
            brands.append(brand)
            self.stdout.write(f'Created brand: {brand.name}')

        # Create colors
        colors = []
        color_data = [
            ('Black', '#000000'),
            ('White', '#FFFFFF'),
            ('Red', '#FF0000'),
            ('Blue', '#0000FF'),
            ('Green', '#00FF00'),
            ('Yellow', '#FFFF00'),
            ('Gray', '#808080'),
        ]
        for color_name, hex_code in color_data:
            color = Color.objects.create(name=color_name, hex_code=hex_code)
            colors.append(color)
            self.stdout.write(f'Created color: {color.name}')

        # Create sizes
        sizes = []
        size_data = [
            ('XS', 42, 8, 10, 36),
            ('S', 44, 10, 12, 38),
            ('M', 46, 12, 14, 40),
            ('L', 48, 14, 16, 42),
            ('XL', 50, 16, 18, 44),
        ]
        for name, eu, us, uk, fr in size_data:
            size = Size.objects.create(
                name=name,
                size_eu=eu,
                size_us=us,
                size_uk=uk,
                size_fr=fr
            )
            sizes.append(size)
            self.stdout.write(f'Created size: {size.name}')

        # Create materials
        materials = []
        material_names = ['Cotton', 'Leather', 'Polyester', 'Wool', 'Denim', 'Silk']
        for material_name in material_names:
            material = Material.objects.create(
                name=material_name,
                description=fake.text()
            )
            materials.append(material)
            self.stdout.write(f'Created material: {material.name}')

        # Create shipping methods
        shipping_methods = []
        shipping_data = [
            ('Standard Delivery', 3, 5, Decimal('5.99')),
            ('Express Delivery', 1, 2, Decimal('12.99')),
            ('Next Day Delivery', 1, 1, Decimal('19.99')),
        ]
        for name, min_days, max_days, price in shipping_data:
            method = ShippingMethod.objects.create(
                name=name,
                min_days=min_days,
                max_days=max_days,
                price=price
            )
            shipping_methods.append(method)
            self.stdout.write(f'Created shipping method: {method.name}')

        # Create products
        for _ in range(options['products']):
            subcategory = random.choice(subcategories)
            brand = random.choice(brands)
            
            name = f'{brand.name} {subcategory.name}'
            price = Decimal(str(random.uniform(1000, 50000)))
            discount = random.choice([True, False])
            discount_price = price * Decimal('0.8') if discount else None

            product = Product.objects.create(
                name=name,
                slug=self.generate_unique_slug(name, Product),
                description=fake.text(),
                price=price,
                discount_price=discount_price,
                subcategory=subcategory,
                brand=brand,
                gender=subcategory.gender,
                season=random.choice(Season.objects.all()),
                is_featured=random.choice([True, False]),
                is_active=True
            )
            
            # Add random materials (1-3)
            product.materials.add(*random.sample(materials, random.randint(1, 3)))
            
            # Add random shipping methods (1-2)
            product.shipping_methods.add(*random.sample(shipping_methods, random.randint(1, 2)))

            # Create product variants
            for color in random.sample(colors, random.randint(1, 3)):
                for size in random.sample(sizes, random.randint(2, 4)):
                    ProductVariant.objects.create(
                        product=product,
                        color=color,
                        size=size,
                        stock=random.randint(0, 100)
                    )
                    
                    # Create product images for each color
                    ProductImage.objects.create(
                        product=product,
                        color=color,
                        is_primary=(color == colors[0]),
                        alt_text=f"{product.name} - {color.name}"
                    )

            products.append(product)
            self.stdout.write(f'Created product: {product.name}')

        # Create coupons
        for _ in range(5):
            valid_from = timezone.now()
            valid_to = valid_from + timedelta(days=random.randint(10, 60))
            
            Coupon.objects.create(
                code=fake.bothify(text='????####').upper(),
                description=fake.sentence(),
                discount_percent=random.choice([10, 15, 20, 25, 30]),
                valid_from=valid_from,
                valid_to=valid_to,
                is_active=True
            )

        # Create orders
        statuses = ['pending', 'processing', 'shipped', 'delivered']
        payment_methods = ['credit_card', 'paypal', 'cash_on_delivery']

        for _ in range(options['orders']):
            user = random.choice(users)
            address = Address.objects.create(
                user=user,  # Привязываем адрес к пользователю
                full_name=f"{user.first_name} {user.last_name}",
                street=fake.street_address(),
                city=fake.city(),
                country='Россия',
                postal_code=fake.postcode(),
                phone=user.phone_number
            )

            order = Order.objects.create(
                user=user,  # Привязываем заказ к пользователю
                total_amount=Decimal('0'),
                shipping_amount=Decimal('500'),
                status=random.choice(statuses),
                payment_method=random.choice(payment_methods),
                shipping_address=address,
                billing_address=address,
                tracking_number=fake.unique.random_number(digits=10),
                order_note=fake.text(max_nb_chars=100)
            )

            # Add random products to order
            total_amount = Decimal('0')
            for _ in range(random.randint(1, 5)):
                product = random.choice(products)
                quantity = random.randint(1, 3)
                price = product.price
                item_total = price * quantity
                total_amount += item_total

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    price=price
                )

            order.total_amount = total_amount
            order.final_amount = total_amount + order.shipping_amount
            order.save()

        self.stdout.write(self.style.SUCCESS('Successfully generated fake data')) 