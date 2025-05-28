from django.core.management.base import BaseCommand
from django.db.models import Count, Q
from unicflo_api.models import Product, ProductRecommendation
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Generate product recommendations'

    def handle(self, *args, **kwargs):
        self.stdout.write('Starting to generate recommendations...')
        
        # Get all active products
        products = Product.objects.filter(is_active=True)
        total_products = products.count()
        
        self.stdout.write(f'Found {total_products} active products')
        
        # Clear existing recommendations
        ProductRecommendation.objects.all().delete()
        
        recommendations_created = 0
        
        for product in products:
            # 1. Similar products (same category and brand)
            similar_products = Product.objects.filter(
                Q(subcategory=product.subcategory) |
                Q(brand=product.brand)
            ).exclude(
                id=product.id
            ).filter(
                is_active=True
            )[:10]
            
            for similar in similar_products:
                ProductRecommendation.objects.create(
                    product=product,
                    recommended_product=similar,
                    recommendation_type='similar_products',
                    score=0.8
                )
                recommendations_created += 1
            
            # 2. Trending products in same category
            thirty_days_ago = timezone.now() - timedelta(days=30)
            trending_products = Product.objects.filter(
                subcategory=product.subcategory,
                orderitem__order__created_at__gte=thirty_days_ago
            ).exclude(
                id=product.id
            ).annotate(
                order_count=Count('orderitem')
            ).order_by('-order_count')[:10]
            
            for trending in trending_products:
                ProductRecommendation.objects.create(
                    product=product,
                    recommended_product=trending,
                    recommendation_type='trending',
                    score=0.9
                )
                recommendations_created += 1
            
                # 3. Products from same gender category
                gender_products = Product.objects.filter(
                gender=product.gender
            ).exclude(
                id=product.id
            ).filter(
                is_active=True
            ).order_by('?')[:5]  # Random selection
            
            for gender_product in gender_products:
                ProductRecommendation.objects.create(
                    product=product,
                    recommended_product=gender_product,
                    recommendation_type='personalized',
                    score=0.7
                )
                recommendations_created += 1
            
            # Progress update
            if product.id % 10 == 0:
                self.stdout.write(f'Processed {product.id} products...')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully generated {recommendations_created} recommendations for {total_products} products'
            )
        ) 