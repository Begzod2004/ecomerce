from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

class User(AbstractUser):
    telegram_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    telegram_username = models.CharField(max_length=100, null=True, blank=True)
    first_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    is_telegram_user = models.BooleanField(default=False)
    is_telegram_admin = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return self.username or f"user_{self.telegram_id}"

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['telegram_id']),
            models.Index(fields=['telegram_username']),
            models.Index(fields=['is_telegram_admin']),
        ]

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username

    @classmethod
    def get_telegram_admins(cls):
        return cls.objects.filter(is_telegram_admin=True, telegram_id__isnull=False)

class GenderCategory(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Gender Category'
        verbose_name_plural = 'Gender Categories'
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['created_at']),
        ]

        
class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    gender = models.ForeignKey(GenderCategory, on_delete=models.SET_NULL, null=True, related_name='categories')
    image = models.ImageField(upload_to='category_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.gender.name}"

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['created_at']),
        ]


class Subcategory(models.Model):
    category = models.ForeignKey(Category, related_name="subcategories", on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    gender = models.ForeignKey(GenderCategory, on_delete=models.CASCADE, related_name="subcategories")
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='subcategory_images/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.category.name}"

    class Meta:
        verbose_name = 'Subcategory'
        verbose_name_plural = 'Subcategories'
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['created_at']),
            models.Index(fields=['is_active']),
        ]

class Brand(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='brand_logos/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Brand'
        verbose_name_plural = 'Brands'
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['created_at']),
        ]

class Color(models.Model):
    name = models.CharField(max_length=50)
    hex_code = models.CharField(max_length=7)  # For storing color codes like #FF0000
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Color'
        verbose_name_plural = 'Colors'

class Size(models.Model):
    name = models.CharField(max_length=20)  # For sizes like S, M, L, XL
    size_eu = models.PositiveIntegerField(null=True, blank=True)  # European size
    size_us = models.PositiveIntegerField(null=True, blank=True)  # US size
    size_uk = models.PositiveIntegerField(null=True, blank=True)  # UK size
    size_fr = models.PositiveIntegerField(null=True, blank=True)  # French size
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.size_eu:
            return f"{self.name} (EU: {self.size_eu}, US: {self.size_us}, UK: {self.size_uk}, FR: {self.size_fr})"
        return self.name

    class Meta:
        verbose_name = 'Size'
        verbose_name_plural = 'Sizes'

class Material(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Material'
        verbose_name_plural = 'Materials'

class Season(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Season'
        verbose_name_plural = 'Seasons'

class ShippingMethod(models.Model):
    DELIVERY_TYPE_CHOICES = (
        ('branch_pickup', 'Branch Pickup'),
        ('home_delivery', 'Home Delivery'),
    )
    
    name = models.CharField(max_length=100)
    delivery_type = models.CharField(max_length=20, choices=DELIVERY_TYPE_CHOICES, default='branch_pickup')
    min_days = models.PositiveIntegerField()
    max_days = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    
    # New fields for enhanced shipping options
    description = models.TextField(blank=True)
    estimated_delivery_time = models.CharField(max_length=100, blank=True)
    free_shipping_threshold = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    available_time_slots = models.JSONField(default=list, blank=True)
    max_weight = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tracking_available = models.BooleanField(default=True)
    insurance_available = models.BooleanField(default=False)
    insurance_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.get_delivery_type_display()})"

    def calculate_shipping_cost(self, order_total, weight=None):
        """Calculate shipping cost based on order total and weight"""
        # Branch pickup is always free
        if self.delivery_type == 'branch_pickup':
            return 0
            
        # For home delivery, check free shipping threshold
        if self.free_shipping_threshold and order_total >= self.free_shipping_threshold:
            return 0
        
        cost = self.price
        
        # Add weight-based cost if applicable
        if weight and self.max_weight and self.delivery_type == 'home_delivery':
            weight_factor = weight / self.max_weight
            cost += cost * weight_factor
        
        return cost

    class Meta:
        verbose_name = 'Shipping Method'
        verbose_name_plural = 'Shipping Methods'
        indexes = [
            models.Index(fields=['delivery_type']),
            models.Index(fields=['is_active']),
            models.Index(fields=['price']),
        ]
        ordering = ['price', 'min_days']

class Product(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    subcategory = models.ForeignKey(Subcategory, on_delete=models.CASCADE, related_name='products')
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, related_name='products')
    season = models.ForeignKey(Season, on_delete=models.SET_NULL, null=True, related_name='products')
    materials = models.ManyToManyField(Material, related_name='products')
    shipping_methods = models.ManyToManyField(ShippingMethod, related_name='products')
    gender = models.ForeignKey(GenderCategory, on_delete=models.SET_NULL, null=True, related_name='products')
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    likes = models.ManyToManyField(User, related_name='liked_products', blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['created_at']),
            models.Index(fields=['subcategory']),
            models.Index(fields=['brand']),
            models.Index(fields=['is_featured']),
            models.Index(fields=['is_active']),
            models.Index(fields=['gender']),
        ]

class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    color = models.ForeignKey(Color, on_delete=models.CASCADE)
    size = models.ForeignKey(Size, on_delete=models.CASCADE)
    stock = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.product.name} - {self.color.name} - {self.size.name}"

    class Meta:
        verbose_name = 'Product Variant'
        verbose_name_plural = 'Product Variants'
        unique_together = ['product', 'color', 'size']
        indexes = [
            models.Index(fields=['product', 'color', 'size']),
            models.Index(fields=['stock']),
        ]

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    color = models.ForeignKey(Color, on_delete=models.CASCADE, related_name='product_images')
    image = models.ImageField(upload_to='product_images/')
    is_primary = models.BooleanField(default=False)
    alt_text = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.product.name} - {self.color.name}"

    class Meta:
        verbose_name = 'Product Image'
        verbose_name_plural = 'Product Images'
        indexes = [
            models.Index(fields=['product', 'color']),
            models.Index(fields=['is_primary']),
        ]

class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session_key = models.CharField(max_length=40, null=True, blank=True)
    products = models.ManyToManyField(Product)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_public = models.BooleanField(default=False)
    name = models.CharField(max_length=100, blank=True, help_text="Optional name for the wishlist")
    description = models.TextField(blank=True, help_text="Optional description for the wishlist")

    def __str__(self):
        if self.user:
            return f"Wishlist for {self.user.username}"
        return f"Anonymous Wishlist {self.session_key}"

    def add_product(self, product):
        """Add a product to wishlist and update its liked status"""
        self.products.add(product)
        product.likes.add(self.user)
        return True

    def remove_product(self, product):
        """Remove a product from wishlist and update its liked status"""
        self.products.remove(product)
        product.likes.remove(self.user)
        return True

    def clear(self):
        """Clear all products from wishlist and update their liked status"""
        for product in self.products.all():
            product.likes.remove(self.user)
        self.products.clear()
        return True

    def get_total_value(self):
        """Calculate total value of all products in wishlist"""
        return sum(product.price for product in self.products.all())

    def get_discounted_value(self):
        """Calculate total value with discounts applied"""
        return sum(product.discount_price or product.price for product in self.products.all())

    def get_savings(self):
        """Calculate potential savings from discounts"""
        return self.get_total_value() - self.get_discounted_value()

    def save(self, *args, **kwargs):
        """Override save to ensure all products in wishlist are liked"""
        super().save(*args, **kwargs)
        # Ensure all products in wishlist are liked
        for product in self.products.all():
            if not product.likes.filter(id=self.user.id).exists():
                product.likes.add(self.user)

    class Meta:
        verbose_name = 'Wishlist'
        verbose_name_plural = 'Wishlists'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['session_key']),
            models.Index(fields=['created_at']),
            models.Index(fields=['updated_at']),
        ]

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='carts')
    session_key = models.CharField(max_length=40, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    promo_code = models.ForeignKey('PromoCode', on_delete=models.SET_NULL, null=True, blank=True)
    promo_code_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        if self.user:
            return f"Cart for {self.user.username}"
        return f"Anonymous Cart {self.session_key}"

    @property
    def total_price(self):
        """Calculate subtotal (products only) for non-deleted items"""
        return sum(item.total_price for item in self.items.filter(is_deleted=False))

    @property
    def final_price(self):
        """Calculate final price after discounts"""
        return self.total_price - self.promo_code_discount

    @property
    def active_items(self):
        """Get only non-deleted items"""
        return self.items.filter(is_deleted=False)

    def get_available_shipping_methods(self):
        """Get common shipping methods available for all products in cart"""
        active_items = self.active_items.select_related('product')
        if not active_items.exists():
            return ShippingMethod.objects.none()

        # Get all shipping methods for first product
        first_item = active_items.first()
        available_methods = set(first_item.product.shipping_methods.filter(is_active=True))

        # Intersect with shipping methods of other products
        for item in active_items[1:]:
            product_methods = set(item.product.shipping_methods.filter(is_active=True))
            available_methods.intersection_update(product_methods)

        # Convert set back to queryset
        method_ids = [method.id for method in available_methods]
        return ShippingMethod.objects.filter(id__in=method_ids)

    def save(self, *args, **kwargs):
        """Override save to handle cart activation status"""
        if self.is_active:
            # Deactivate all other active carts for this user
            Cart.objects.filter(user=self.user, is_active=True).exclude(id=self.id).update(is_active=False)
        
        super().save(*args, **kwargs)

    def activate(self):
        """Activate this cart and deactivate others"""
        Cart.objects.filter(user=self.user, is_active=True).update(is_active=False)
        self.is_active = True
        self.save()

    def deactivate(self):
        """Deactivate this cart"""
        self.is_active = False
        self.save()

    class Meta:
        verbose_name = 'Cart'
        verbose_name_plural = 'Carts'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['session_key']),
            models.Index(fields=['is_active']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'is_active'],
                condition=models.Q(is_active=True),
                name='unique_active_cart_per_user'
            )
        ]

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        if self.variant:
            return f"{self.quantity}x {self.product.name} ({self.variant.color.name}, {self.variant.size.name}) in cart {self.cart.id}"
        return f"{self.quantity}x {self.product.name} in cart {self.cart.id}"

    @property
    def total_price(self):
        price = self.product.discount_price or self.product.price
        return self.quantity * price

    def delete(self, *args, hard_delete=False, **kwargs):
        """
        Override delete to handle both soft and hard deletion
        """
        if hard_delete:
            result = super().delete(*args, **kwargs)
        else:
            self.is_deleted = True
            self.deleted_at = timezone.now()
            self.save(update_fields=['is_deleted', 'deleted_at'])
            result = None

        # Check if cart should be deactivated
        cart = self.cart
        active_items = cart.items.filter(is_deleted=False).exists()
        if not active_items:
            cart.is_active = False
            cart.save(update_fields=['is_active'])

        return result

    class Meta:
        verbose_name = 'Cart Item'
        verbose_name_plural = 'Cart Items'
        unique_together = ['cart', 'product', 'variant']
        indexes = [
            models.Index(fields=['is_deleted']),
            models.Index(fields=['deleted_at']),
        ]

class PromoCode(models.Model):
    DISCOUNT_TYPE_CHOICES = (
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
        ('free_shipping', 'Free Shipping'),
        ('buy_one_get_one', 'Buy One Get One'),
    )
    
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('expired', 'Expired'),
    )
    
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_discount_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    usage_limit = models.PositiveIntegerField(null=True, blank=True)
    usage_count = models.PositiveIntegerField(default=0)
    per_user_limit = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Additional creative features
    is_first_purchase_only = models.BooleanField(default=False)
    is_new_user_only = models.BooleanField(default=False)
    is_birthday_only = models.BooleanField(default=False)
    is_seasonal = models.BooleanField(default=False)
    seasonal_start_month = models.PositiveIntegerField(null=True, blank=True)
    seasonal_end_month = models.PositiveIntegerField(null=True, blank=True)
    applicable_categories = models.ManyToManyField('Category', blank=True)
    applicable_products = models.ManyToManyField('Product', blank=True)
    excluded_products = models.ManyToManyField('Product', related_name='excluded_from_promos', blank=True)
    min_items_in_cart = models.PositiveIntegerField(default=1)
    max_items_in_cart = models.PositiveIntegerField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.code} ({self.get_discount_type_display()})"

    def is_valid(self, user, cart_total, cart_items_count):
        """Check if promo code is valid for the given user and cart"""
        now = timezone.now()
        
        # Basic validation
        if self.status != 'active':
            return False, "Promo code is not active"
            
        if now < self.start_date:
            return False, "Promo code is not yet active"
            
        if now > self.end_date:
            return False, "Promo code has expired"
            
        if self.usage_limit and self.usage_count >= self.usage_limit:
            return False, "Promo code usage limit reached"
            
        if cart_total < self.min_order_amount:
            return False, f"Minimum order amount is {self.min_order_amount}"
            
        if cart_items_count < self.min_items_in_cart:
            return False, f"Minimum {self.min_items_in_cart} items required"
            
        if self.max_items_in_cart and cart_items_count > self.max_items_in_cart:
            return False, f"Maximum {self.max_items_in_cart} items allowed"
            
        # User-specific validation
        if self.is_first_purchase_only and Order.objects.filter(user=user).exists():
            return False, "Only for first purchase"
            
        if self.is_new_user_only and user.date_joined < (now - timedelta(days=30)):
            return False, "Only for new users"
            
        if self.is_birthday_only:
            if not user.birth_date:
                return False, "Birthday date not set"
            if user.birth_date.month != now.month or user.birth_date.day != now.day:
                return False, "Only valid on your birthday"
                
        # Check per-user usage limit
        user_usage_count = Order.objects.filter(
            user=user,
            promo_code=self
        ).count()
        
        if user_usage_count >= self.per_user_limit:
            return False, "You have reached the usage limit for this promo code"
            
        return True, "Valid"

    def calculate_discount(self, cart_total, cart_items):
        """Calculate discount amount based on promo code type"""
        if self.discount_type == 'percentage':
            discount = (cart_total * self.discount_value) / 100
            if self.max_discount_amount:
                discount = min(discount, self.max_discount_amount)
            return discount
            
        elif self.discount_type == 'fixed':
            return min(self.discount_value, cart_total)
            
        elif self.discount_type == 'free_shipping':
            return 0  # Shipping cost will be handled separately
            
        elif self.discount_type == 'buy_one_get_one':
            # Implement BOGO logic here
            return 0
            
        return 0

    def apply(self, user, cart_total, cart_items):
        """Apply promo code and return discount amount"""
        is_valid, message = self.is_valid(user, cart_total, len(cart_items))
        if not is_valid:
            raise ValueError(message)
            
        discount = self.calculate_discount(cart_total, cart_items)
        self.usage_count += 1
        self.save()
        return discount

    class Meta:
        verbose_name = 'Promo Code'
        verbose_name_plural = 'Promo Codes'
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['status']),
            models.Index(fields=['start_date']),
            models.Index(fields=['end_date']),
            models.Index(fields=['discount_type']),
        ]
        ordering = ['-created_at']

class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('ready_for_pickup', 'Ready for Pickup'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('canceled', 'Canceled'),
        ('returned', 'Returned'),
    )
    
    PAYMENT_METHOD_CHOICES = (
        ('card', 'Credit Card'),
        ('cash_on_delivery', 'Cash on Delivery'),
        ('cash_on_pickup', 'Cash on Pickup'),
        ('split', 'Split Payment'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    cart = models.ForeignKey(Cart, on_delete=models.SET_NULL, null=True)
    products = models.ManyToManyField(Product, through='OrderItem')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    final_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    shipping_method = models.ForeignKey(ShippingMethod, on_delete=models.SET_NULL, null=True)
    
    # For branch pickup
    pickup_branch = models.ForeignKey('Address', on_delete=models.SET_NULL, null=True, related_name='pickup_orders', help_text='Branch for pickup')
    
    # For home delivery
    delivery_address = models.ForeignKey('Address', on_delete=models.SET_NULL, null=True, related_name='delivery_orders', help_text='Address for home delivery')
    
    tracking_number = models.CharField(max_length=100, blank=True)
    order_note = models.TextField(blank=True)
    customer_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    
    # Split payment fields
    is_split_payment = models.BooleanField(default=False)
    first_payment_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    first_payment_date = models.DateTimeField(null=True, blank=True)
    second_payment_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    second_payment_due_date = models.DateTimeField(null=True, blank=True)
    second_payment_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Payment fields
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='cash_on_delivery')
    payment_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.id} by {self.user.username}"

    def save(self, *args, **kwargs):
        if not self.pk:  # Only on creation
            super().save(*args, **kwargs)  # Save first to create ID
        else:
            # Calculate totals
            self.total_amount = sum(item.total_price for item in self.items.all())
            
            # Calculate shipping amount based on delivery type
            if self.shipping_method:
                self.shipping_amount = self.shipping_method.calculate_shipping_cost(self.total_amount)
            
            self.final_amount = self.total_amount + self.shipping_amount - self.discount_amount
            
            # Handle split payment calculations
            if self.is_split_payment and not self.first_payment_amount:
                self.first_payment_amount = self.final_amount * Decimal('0.5')
                self.second_payment_amount = self.final_amount - self.first_payment_amount
                self.second_payment_due_date = timezone.now() + timedelta(days=30)
            
            super().save(*args, **kwargs)

    def calculate_totals(self):
        self.total_amount = sum(item.total_price for item in self.items.all())
        if self.shipping_method:
            self.shipping_amount = self.shipping_method.calculate_shipping_cost(self.total_amount)
        self.final_amount = self.total_amount + self.shipping_amount - self.discount_amount
        self.save()

    class Meta:
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['user']),
            models.Index(fields=['payment_method']),
            models.Index(fields=['payment_status']),
            models.Index(fields=['is_split_payment']),
        ]
        ordering = ['-created_at']

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price at time of purchase
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        variant_info = f" ({self.variant.color.name}, {self.variant.size.name})" if self.variant else ""
        return f"{self.quantity}x {self.product.name}{variant_info}"

    @property
    def total_price(self):
        if self.price is None:
            self.price = self.product.price
            self.save()
        return self.quantity * self.price

    def save(self, *args, **kwargs):
        if self.price is None:
            self.price = self.product.price
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Order Item'
        verbose_name_plural = 'Order Items'
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['variant']),
        ]

class Address(models.Model):
    BRANCH_TYPE_CHOICES = (
        ('store', 'Store'),
        ('pickup', 'Pickup Point'),
        ('warehouse', 'Warehouse'),
    )
    
    name = models.CharField(max_length=100)
    branch_type = models.CharField(max_length=20, choices=BRANCH_TYPE_CHOICES, default='store')
    street = models.CharField(max_length=255)
    district = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    region = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='Uzbekistan')
    postal_code = models.CharField(max_length=20)
    phone = models.CharField(max_length=20)
    working_hours = models.CharField(max_length=100, help_text="Example: 09:00-18:00")
    is_active = models.BooleanField(default=True)
    location_link = models.URLField(blank=True, help_text="Google Maps link")
    
    # Additional fields for branch management
    manager_name = models.CharField(max_length=100, blank=True)
    manager_phone = models.CharField(max_length=20, blank=True)
    has_fitting_room = models.BooleanField(default=False)
    has_parking = models.BooleanField(default=False)
    is_24_hours = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.get_branch_type_display()} - {self.city})"

    class Meta:
        verbose_name = 'Branch Address'
        verbose_name_plural = 'Branch Addresses'
        indexes = [
            models.Index(fields=['city']),
            models.Index(fields=['branch_type']),
            models.Index(fields=['is_active']),
        ]
        ordering = ['city', 'name']

class ProductRecommendation(models.Model):
    RECOMMENDATION_TYPES = (
        ('viewed_also_viewed', 'Customers Who Viewed Also Viewed'),
        ('bought_also_bought', 'Customers Who Bought Also Bought'),
        ('similar_products', 'Similar Products'),
        ('trending', 'Trending Products'),
        ('category_based', 'Category Based'),
        ('personalized', 'Personalized'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='recommendations')
    recommended_product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='recommended_by')
    recommendation_type = models.CharField(max_length=50, choices=RECOMMENDATION_TYPES)
    score = models.FloatField(default=0.0, help_text='Recommendation score/weight')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Product Recommendation'
        verbose_name_plural = 'Product Recommendations'
        unique_together = ['product', 'recommended_product', 'recommendation_type']
        indexes = [
            models.Index(fields=['product', 'recommendation_type']),
            models.Index(fields=['user']),
            models.Index(fields=['score']),
            models.Index(fields=['created_at']),
        ]
        ordering = ['-score', '-created_at']

    def __str__(self):
        return f"{self.product.name} -> {self.recommended_product.name} ({self.get_recommendation_type_display()})"