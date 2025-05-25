from django.db import migrations, models

def deactivate_duplicate_carts(apps, schema_editor):
    Cart = apps.get_model('unicflo_api', 'Cart')
    # Get all users with multiple active carts
    from django.db.models import Count
    users_with_multiple_carts = Cart.objects.filter(is_active=True).values('user').annotate(
        cart_count=Count('id')).filter(cart_count__gt=1)
    
    # For each user, keep only the most recent active cart
    for user_data in users_with_multiple_carts:
        user_id = user_data['user']
        # Get all active carts for this user
        user_carts = Cart.objects.filter(user_id=user_id, is_active=True).order_by('-created_at')
        # Keep the most recent one active, deactivate others
        if user_carts.exists():
            first_cart = user_carts.first()
            user_carts.exclude(id=first_cart.id).update(is_active=False)

class Migration(migrations.Migration):
    dependencies = [
        ('unicflo_api', '0008_promocode_alter_address_options_and_more'),
    ]

    operations = [
        # First add the is_active field
        migrations.AddField(
            model_name='cart',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        # Then run the data migration
        migrations.RunPython(deactivate_duplicate_carts),
        # Finally add the unique constraint
        migrations.AddConstraint(
            model_name='cart',
            constraint=models.UniqueConstraint(
                fields=['user', 'is_active'],
                condition=models.Q(is_active=True),
                name='unique_active_cart_per_user'
            ),
        ),
    ] 