from django.core.management.base import BaseCommand
from django.utils.text import slugify
from unicflo_api.models import (
    GenderCategory, Category, Subcategory, Brand,
    Color, Size, Material, Season, Product,
    ProductVariant, ProductImage
)

class Command(BaseCommand):
    help = 'Generate test data for the e-commerce platform'

    def handle(self, *args, **kwargs):
        self.stdout.write('Starting to generate test data...')
        
        # Clear existing data
        self.stdout.write('Clearing existing data...')
        Product.objects.all().delete()
        Subcategory.objects.all().delete()
        Category.objects.all().delete()
        Brand.objects.all().delete()
        GenderCategory.objects.all().delete()
        Color.objects.all().delete()
        Size.objects.all().delete()
        Material.objects.all().delete()
        Season.objects.all().delete()

        # Create Gender Categories
        self.stdout.write('Creating gender categories...')
        genders = [
            {'name': 'Erkaklar', 'slug': 'erkaklar'},
            {'name': 'Ayollar', 'slug': 'ayollar'},
        ]
        for gender_data in genders:
            GenderCategory.objects.create(**gender_data)

        # Create Brands
        self.stdout.write('Creating brands...')
        brands = [
            {'name': 'Nike', 'slug': 'nike'},
            {'name': 'Adidas', 'slug': 'adidas'},
            {'name': 'Zara', 'slug': 'zara'},
            {'name': 'H&M', 'slug': 'h-and-m'},
            {'name': 'Gucci', 'slug': 'gucci'},
        ]
        for brand_data in brands:
            Brand.objects.create(**brand_data)

        # Create Categories and Subcategories
        self.stdout.write('Creating categories and subcategories...')
        categories = {
            'Kiyimlar': ['Ko\'ylaklar', 'Shimlar', 'Futbolkalar', 'Kostyumlar'],
            'Poyabzallar': ['Krossovkalar', 'Tuflilar', 'Sandalar'],
            'Aksessuarlar': ['Sumkalar', 'Soatlar', 'Kamarlar'],
        }

        for category_name, subcategories in categories.items():
            for gender in GenderCategory.objects.all():
                category = Category.objects.create(
                    name=category_name,
                    slug=f"{slugify(category_name)}-{gender.slug}",
                    gender=gender
                )
                
                for subcat_name in subcategories:
                    Subcategory.objects.create(
                        name=subcat_name,
                        slug=f"{slugify(subcat_name)}-{gender.slug}",
                        category=category,
                        gender=gender
                    )

        # Create Colors
        self.stdout.write('Creating colors...')
        colors = [
            {'name': 'Qora', 'hex_code': '#000000'},
            {'name': 'Oq', 'hex_code': '#FFFFFF'},
            {'name': 'Ko\'k', 'hex_code': '#0000FF'},
            {'name': 'Qizil', 'hex_code': '#FF0000'},
        ]
        for color_data in colors:
            Color.objects.create(**color_data)

        # Create Sizes
        self.stdout.write('Creating sizes...')
        sizes = ['XS', 'S', 'M', 'L', 'XL', 'XXL']
        for size_name in sizes:
            Size.objects.create(name=size_name)

        # Create Materials
        self.stdout.write('Creating materials...')
        materials = ['Paxta', 'Teri', 'Jungli', 'Sintetika']
        for material_name in materials:
            Material.objects.create(name=material_name)

        # Create Seasons
        self.stdout.write('Creating seasons...')
        seasons = ['Bahor', 'Yoz', 'Kuz', 'Qish']
        for season_name in seasons:
            Season.objects.create(name=season_name)

        # Create Products with Variants
        self.stdout.write('Creating products and variants...')
        products_data = [
            {
                'name': 'Sport Futbolka',
                'price': 199000,
                'description': 'Yuqori sifatli sport futbolka',
            },
            {
                'name': 'Klassik Shim',
                'price': 299000,
                'description': 'Zamonaviy klassik shim',
            },
            {
                'name': 'Sport Krossovka',
                'price': 499000,
                'description': 'Qulay sport krossovka',
            },
        ]

        for product_data in products_data:
            for gender in GenderCategory.objects.all():
                for subcategory in Subcategory.objects.filter(gender=gender):
                    product_name = f"{product_data['name']} ({gender.name})"
                    product_slug = f"{slugify(product_name)}-{subcategory.slug}"
                    product = Product.objects.create(
                        name=product_name,
                        slug=product_slug,
                        price=product_data['price'],
                        description=product_data['description'],
                        subcategory=subcategory,
                        brand=Brand.objects.first(),
                        season=Season.objects.first(),
                        gender=gender
                    )

                    # Add materials
                    product.materials.add(*Material.objects.all()[:2])
                    
                    # Create variants
                    for color in Color.objects.all():
                        for size in Size.objects.all():
                            ProductVariant.objects.create(
                                product=product,
                                color=color,
                                size=size,
                                stock=100
                            )

        self.stdout.write(self.style.SUCCESS('Successfully generated test data')) 