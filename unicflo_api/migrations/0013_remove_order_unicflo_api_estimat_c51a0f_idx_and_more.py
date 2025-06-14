# Generated by Django 4.2.20 on 2025-05-23 15:51

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('unicflo_api', '0012_cartitem_deleted_at_cartitem_is_deleted_and_more'),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='order',
            name='unicflo_api_estimat_c51a0f_idx',
        ),
        migrations.RemoveField(
            model_name='order',
            name='delivery_notes',
        ),
        migrations.RemoveField(
            model_name='order',
            name='estimated_delivery_date',
        ),
        migrations.RemoveField(
            model_name='order',
            name='gift_wrapping',
        ),
        migrations.RemoveField(
            model_name='order',
            name='preferred_delivery_time',
        ),
        migrations.RemoveField(
            model_name='order',
            name='promo_code',
        ),
        migrations.RemoveField(
            model_name='order',
            name='promo_code_discount',
        ),
        migrations.RemoveField(
            model_name='order',
            name='save_billing_address',
        ),
        migrations.RemoveField(
            model_name='order',
            name='save_shipping_address',
        ),
        migrations.AddField(
            model_name='order',
            name='cart',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='unicflo_api.cart'),
        ),
        migrations.AddField(
            model_name='order',
            name='customer_name',
            field=models.CharField(default=1, max_length=100),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='order',
            name='first_payment_amount',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='first_payment_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='is_split_payment',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='order',
            name='payment_status',
            field=models.CharField(choices=[('pending', 'Pending'), ('processing', 'Processing'), ('shipped', 'Shipped'), ('delivered', 'Delivered'), ('canceled', 'Canceled'), ('returned', 'Returned')], default='pending', max_length=20),
        ),
        migrations.AddField(
            model_name='order',
            name='second_payment_amount',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='second_payment_due_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='second_payment_status',
            field=models.CharField(choices=[('pending', 'Pending'), ('processing', 'Processing'), ('shipped', 'Shipped'), ('delivered', 'Delivered'), ('canceled', 'Canceled'), ('returned', 'Returned')], default='pending', max_length=20),
        ),
        migrations.AddField(
            model_name='order',
            name='shipping_method',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='unicflo_api.shippingmethod'),
        ),
        migrations.AddField(
            model_name='orderitem',
            name='variant',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='unicflo_api.productvariant'),
        ),
        migrations.AlterField(
            model_name='cart',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='carts', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='order',
            name='payment_method',
            field=models.CharField(choices=[('card', 'Credit Card'), ('cash_on_delivery', 'Cash on Delivery'), ('split', 'Split Payment')], default='cash_on_delivery', max_length=20),
        ),
        migrations.AlterField(
            model_name='order',
            name='phone_number',
            field=models.CharField(max_length=20),
        ),
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['payment_status'], name='unicflo_api_payment_3c311a_idx'),
        ),
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['is_split_payment'], name='unicflo_api_is_spli_b2ba8d_idx'),
        ),
        migrations.AddIndex(
            model_name='orderitem',
            index=models.Index(fields=['variant'], name='unicflo_api_variant_a19181_idx'),
        ),
    ]
