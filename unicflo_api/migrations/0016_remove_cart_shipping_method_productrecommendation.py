# Generated by Django 4.2.20 on 2025-05-24 22:36

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('unicflo_api', '0015_remove_order_branch_cart_shipping_method_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cart',
            name='shipping_method',
        ),
        migrations.CreateModel(
            name='ProductRecommendation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('recommendation_type', models.CharField(choices=[('viewed_also_viewed', 'Customers Who Viewed Also Viewed'), ('bought_also_bought', 'Customers Who Bought Also Bought'), ('similar_products', 'Similar Products'), ('trending', 'Trending Products'), ('category_based', 'Category Based'), ('personalized', 'Personalized')], max_length=50)),
                ('score', models.FloatField(default=0.0, help_text='Recommendation score/weight')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recommendations', to='unicflo_api.product')),
                ('recommended_product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recommended_by', to='unicflo_api.product')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Product Recommendation',
                'verbose_name_plural': 'Product Recommendations',
                'ordering': ['-score', '-created_at'],
                'indexes': [models.Index(fields=['product', 'recommendation_type'], name='unicflo_api_product_7c669a_idx'), models.Index(fields=['user'], name='unicflo_api_user_id_d3c4f3_idx'), models.Index(fields=['score'], name='unicflo_api_score_a78969_idx'), models.Index(fields=['created_at'], name='unicflo_api_created_d49711_idx')],
                'unique_together': {('product', 'recommended_product', 'recommendation_type')},
            },
        ),
    ]
