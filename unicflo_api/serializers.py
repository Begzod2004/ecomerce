from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .models import (
    User, Category, Product, ProductImage,
    Wishlist, Cart, CartItem, Order, OrderItem, Address, Subcategory, Brand, Size, Material, Season, ShippingMethod, ProductVariant, GenderCategory,
    Color, PromoCode, ProductRecommendation
)
from .utils.telegram import TelegramService
from django.shortcuts import get_object_or_404
from django.db import transaction
from decimal import Decimal

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            
            'id', 
            'username', 
            'telegram_id', 
            'telegram_username',
            'first_name',
            'last_name',
            'is_telegram_user',
            'is_telegram_admin',
            'is_verified'
        ]
        read_only_fields = ['username', 'is_telegram_admin']  # Only admins can change this via admin panel

class GenderCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = GenderCategory
        fields = ['id', 'name', 'slug']

class CategorySerializer(serializers.ModelSerializer):
    gender = GenderCategorySerializer(read_only=True)
    subcategories_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'gender', 'image', 'subcategories_count', 'created_at']
        read_only_fields = ['slug']

class BrandSerializer(serializers.ModelSerializer):
    products_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Brand
        fields = ['id', 'name', 'slug', 'description', 'logo', 'products_count', 'created_at']
        read_only_fields = ['slug']

class ColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Color
        fields = ['id', 'name', 'hex_code', 'created_at']

class SizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Size
        fields = ['id', 'name', 'size_eu', 'size_us', 'size_uk', 'size_fr', 'created_at']

class MaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Material
        fields = ['id', 'name', 'description', 'created_at']

class SeasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Season
        fields = ['id', 'name', 'description', 'created_at']

class ShippingMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingMethod
        fields = [
            'id', 'name', 'delivery_type', 'min_days', 'max_days', 'price',
            'is_active', 'description', 'estimated_delivery_time',
            'free_shipping_threshold', 'available_time_slots', 'max_weight',
            'tracking_available', 'insurance_available', 'insurance_cost',
            'created_at', 'updated_at'
        ]

class SubcategorySerializer(serializers.ModelSerializer):
    gender = GenderCategorySerializer(read_only=True)
    products_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Subcategory
        fields = ['id', 'name', 'slug', 'description', 'gender', 'products_count']

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'is_primary']

class ProductVariantSerializer(serializers.ModelSerializer):
    color_name = serializers.CharField(source='color.name', read_only=True)
    color_hex = serializers.CharField(source='color.hex_code', read_only=True)
    size_name = serializers.CharField(source='size.name', read_only=True)

    class Meta:
        model = ProductVariant
        fields = ['id', 'color', 'color_name', 'color_hex', 'size', 'size_name', 'stock']
        read_only_fields = ['color_name', 'color_hex', 'size_name']

class ProductSerializer(serializers.ModelSerializer):
    variants = ProductVariantSerializer(many=True, read_only=True, source='variants.all')
    images = ProductImageSerializer(many=True, read_only=True)
    likes_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    uploaded_images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False
    )
    # Write-only fields for bulk assignment
    material_ids = serializers.PrimaryKeyRelatedField(
        queryset=Material.objects.all(),
        many=True,
        write_only=True,
        required=False
    )
    shipping_method_ids = serializers.PrimaryKeyRelatedField(
        queryset=ShippingMethod.objects.all(),
        many=True,
        write_only=True,
        required=False
    )
    subcategory_id = serializers.PrimaryKeyRelatedField(
        queryset=Subcategory.objects.all(),
        source='subcategory',
        write_only=True,
        required=False
    )
    brand_id = serializers.PrimaryKeyRelatedField(
        queryset=Brand.objects.all(),
        source='brand',
        write_only=True,
        required=False
    )
    gender_id = serializers.PrimaryKeyRelatedField(
        queryset=GenderCategory.objects.all(),
        source='gender',
        write_only=True,
        required=False
    )
    season_id = serializers.PrimaryKeyRelatedField(
        queryset=Season.objects.all(),
        source='season',
        write_only=True,
        required=False
    )

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'price', 'discount_price',
            'subcategory', 'subcategory_id', 'brand', 'brand_id',
            'gender', 'gender_id', 'season', 'season_id',
            'materials', 'material_ids', 'shipping_methods', 'shipping_method_ids',
            'is_featured', 'is_active', 'created_at', 'updated_at',
            'images', 'uploaded_images', 'variants',
            'likes_count', 'is_liked'
        ]
        read_only_fields = ['slug', 'subcategory', 'brand', 'gender', 'season', 'materials', 'shipping_methods']

    def get_likes_count(self, obj):
        return obj.likes.count()

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(id=request.user.id).exists()
        return False

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than zero")
        return value

    def create(self, validated_data):
        uploaded_images = validated_data.pop('uploaded_images', [])
        material_ids = validated_data.pop('material_ids', [])
        shipping_method_ids = validated_data.pop('shipping_method_ids', [])
        product = Product.objects.create(**validated_data)
        if material_ids:
            product.materials.set(material_ids)
        if shipping_method_ids:
            product.shipping_methods.set(shipping_method_ids)
        for i, image in enumerate(uploaded_images):
            ProductImage.objects.create(
                product=product,
                image=image,
                is_primary=(i == 0)
            )
        return product

    def update(self, instance, validated_data):
        material_ids = validated_data.pop('material_ids', None)
        shipping_method_ids = validated_data.pop('shipping_method_ids', None)
        uploaded_images = validated_data.pop('uploaded_images', [])
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if material_ids is not None:
            instance.materials.set(material_ids)
        if shipping_method_ids is not None:
            instance.shipping_methods.set(shipping_method_ids)
        instance.save()
        for i, image in enumerate(uploaded_images):
            ProductImage.objects.create(
                product=instance,
                image=image,
                is_primary=(i == 0)
            )
        return instance

class ProductRecommendationSerializer(serializers.ModelSerializer):
    recommended_product = ProductSerializer(read_only=True)
    recommendation_type_display = serializers.CharField(source='get_recommendation_type_display', read_only=True)

    class Meta:
        model = ProductRecommendation
        fields = [
            'id', 'recommended_product', 'recommendation_type',
            'recommendation_type_display', 'score', 'created_at'
        ]
        read_only_fields = ['score', 'created_at']

class WishlistSerializer(serializers.ModelSerializer):
    products = ProductSerializer(many=True, read_only=True)
    product_ids = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(queryset=Product.objects.all()),
        write_only=True,
        required=False
    )
    total_value = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    discounted_value = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    potential_savings = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    products_count = serializers.IntegerField(read_only=True)
    is_public = serializers.BooleanField(default=False)
    name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Wishlist
        fields = [
            'id', 'user', 'products', 'product_ids', 'created_at', 'updated_at',
            'total_value', 'discounted_value', 'potential_savings', 'products_count',
            'is_public', 'name', 'description'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']
    
    def get_total_value(self, obj):
        return obj.get_total_value()

    def get_discounted_value(self, obj):
        return obj.get_discounted_value()

    def get_potential_savings(self, obj):
        return obj.get_savings()

    def get_products_count(self, obj):
        return obj.products.count()
    
    def create(self, validated_data):
        product_ids = validated_data.pop('product_ids', [])
        wishlist = Wishlist.objects.create(**validated_data)
        
        # Add products and update their liked status
        for product in product_ids:
            wishlist.add_product(product)
            
        return wishlist

    def update(self, instance, validated_data):
        product_ids = validated_data.pop('product_ids', None)
        
        # Update basic fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Handle product updates if provided
        if product_ids is not None:
            # Remove products not in the new list
            current_products = set(instance.products.all())
            new_products = set(product_ids)
            products_to_remove = current_products - new_products
            products_to_add = new_products - current_products
            
            # Remove products and update their liked status
            for product in products_to_remove:
                instance.remove_product(product)
            
            # Add new products and update their liked status
            for product in products_to_add:
                instance.add_product(product)
        
        instance.save()
        return instance

class AddToWishlistRequestSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    wishlist_id = serializers.IntegerField(required=False)
    name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)
    is_public = serializers.BooleanField(default=False)

    def validate_product_id(self, value):
        try:
            product = Product.objects.get(id=value)
            if not product.is_active:
                raise serializers.ValidationError("Product is not available")
            return value
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product not found")

class RemoveFromWishlistRequestSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    wishlist_id = serializers.IntegerField(required=False)

    def validate_product_id(self, value):
        try:
            Product.objects.get(id=value)
            return value
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product not found")

class WishlistResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    wishlist = WishlistSerializer()
    is_liked = serializers.BooleanField()

class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_image = serializers.SerializerMethodField()
    product_price = serializers.DecimalField(source='product.price', max_digits=10, decimal_places=2, read_only=True)
    product_discount_price = serializers.DecimalField(source='product.discount_price', max_digits=10, decimal_places=2, read_only=True)
    color = serializers.SerializerMethodField()
    color_hex = serializers.SerializerMethodField()
    size = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()
    variant_id = serializers.IntegerField(source='variant.id', read_only=True)

    class Meta:
        model = CartItem
        fields = [
            'id', 'product', 'product_name', 'product_image', 
            'product_price', 'product_discount_price', 'quantity',
            'color', 'color_hex', 'size', 'total_price', 'variant_id'
        ]
        read_only_fields = ['id', 'product_name', 'product_image', 
                           'product_price', 'product_discount_price',
                           'color', 'color_hex', 'size', 'total_price', 'variant_id']

    def get_product_image(self, obj):
        if obj.variant:
            image = ProductImage.objects.filter(
                product=obj.product,
                color=obj.variant.color,
                is_primary=True
            ).first()
        else:
            # If no variant, get any primary image for the product
            image = ProductImage.objects.filter(
                product=obj.product,
                is_primary=True
            ).first()
            
        if image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(image.image.url)
            return image.image.url
        return None

    def get_color(self, obj):
        if obj.variant:
            return obj.variant.color.name
        return None

    def get_color_hex(self, obj):
        if obj.variant:
            return obj.variant.color.hex_code
        return None

    def get_size(self, obj):
        if obj.variant:
            return obj.variant.size.name
        return None

    def get_total_price(self, obj):
        return obj.total_price

    def create(self, validated_data):
        request = self.context.get('request')
        if not request:
            raise serializers.ValidationError("Request context is required")

        # Get user from telegram ID
        telegram_id = request.META.get('HTTP_X_TELEGRAM_ID')
        if not telegram_id:
            raise serializers.ValidationError("Telegram ID is required")

        try:
            user = User.objects.get(telegram_id=telegram_id)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found")

        # Get or create active cart for user
        cart = Cart.objects.filter(user=user, is_active=True).first()
        if not cart:
            # Deactivate any existing carts
            Cart.objects.filter(user=user, is_active=True).update(is_active=False)
            # Create new cart
            cart = Cart.objects.create(user=user, is_active=True)

        validated_data['cart'] = cart
        return super().create(validated_data)

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True, source='active_items')
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    items_count = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'items', 'total_price', 'items_count', 'created_at', 'updated_at', 'is_active']
        read_only_fields = ['id', 'items', 'total_price', 'items_count', 'created_at', 'updated_at']

    def get_items_count(self, obj):
        return obj.active_items.count()

    def create(self, validated_data):
        request = self.context.get('request')
        if not request:
            raise serializers.ValidationError("Request context is required")

        # Get user from telegram ID
        telegram_id = request.META.get('HTTP_X_TELEGRAM_ID')
        if not telegram_id:
            raise serializers.ValidationError("Telegram ID is required")

        try:
            user = User.objects.get(telegram_id=telegram_id)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found")

        # Deactivate any existing active carts for this user
        Cart.objects.filter(user=user, is_active=True).update(is_active=False)

        # Create new active cart
        cart = Cart.objects.create(user=user, is_active=True)
        return cart

class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), source='product', write_only=True)
    total_price = serializers.DecimalField(read_only=True, max_digits=10, decimal_places=2)
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_image = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            'id', 'product', 'product_id', 'product_name', 'product_image',
            'quantity', 'price', 'total_price', 'created_at'
        ]
        read_only_fields = ['id', 'price', 'total_price', 'created_at']

    def get_product_image(self, obj):
        if obj.product.images.exists():
            return obj.product.images.first().image.url
        return None

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero")
        return value

    def validate(self, attrs):
        product = attrs.get('product')
        quantity = attrs.get('quantity', 1)
        
        # Check product stock
        if not product.is_active:
            raise serializers.ValidationError("Product is not available")
            
        # Check if product has enough stock
        if hasattr(product, 'stock') and product.stock < quantity:
            raise serializers.ValidationError(f"Only {product.stock} items available in stock")
            
        return attrs

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = [
            'id', 'name', 'branch_type', 'street', 'district', 'city', 'region',
            'country', 'postal_code', 'phone', 'working_hours', 'is_active',
            'location_link', 'manager_name', 'manager_phone', 'has_fitting_room',
            'has_parking', 'is_24_hours', 'created_at', 'updated_at'
        ]

    def validate(self, attrs):
        return attrs

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    shipping_method = ShippingMethodSerializer(read_only=True)
    shipping_method_id = serializers.PrimaryKeyRelatedField(
        queryset=ShippingMethod.objects.all(),
        source='shipping_method',
        write_only=True,
        required=False
    )
    pickup_branch = AddressSerializer(read_only=True)
    pickup_branch_id = serializers.PrimaryKeyRelatedField(
        queryset=Address.objects.all(),
        source='pickup_branch',
        write_only=True,
        required=False
    )
    delivery_address = AddressSerializer(read_only=True)
    delivery_address_id = serializers.PrimaryKeyRelatedField(
        queryset=Address.objects.all(),
        source='delivery_address',
        write_only=True,
        required=False
    )
    cart_id = serializers.PrimaryKeyRelatedField(
        queryset=Cart.objects.all(),
        source='cart',
        write_only=True,
        required=True
    )
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    items_count = serializers.SerializerMethodField(read_only=True)
    can_cancel = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'user', 'cart', 'cart_id', 'products', 'items', 'items_count',
            'total_amount', 'discount_amount', 'shipping_amount', 'final_amount',
            'status', 'status_display', 'shipping_method', 'shipping_method_id',
            'pickup_branch', 'pickup_branch_id', 'delivery_address', 'delivery_address_id',
            'tracking_number', 'order_note', 'customer_name', 'phone_number',
            'is_split_payment', 'first_payment_amount', 'first_payment_date',
            'second_payment_amount', 'second_payment_due_date', 'second_payment_status',
            'payment_method', 'payment_method_display', 'payment_status',
            'can_cancel', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'products', 'items', 'items_count', 'total_amount',
            'discount_amount', 'shipping_amount', 'final_amount', 'status',
            'created_at', 'updated_at', 'status_display', 'payment_method_display', 'can_cancel',
            'shipping_method', 'pickup_branch', 'delivery_address', 'first_payment_amount',
            'second_payment_amount', 'first_payment_date', 'second_payment_due_date', 'second_payment_status', 'payment_status'
        ]

    def get_items_count(self, obj):
        return obj.items.count()

    def get_can_cancel(self, obj):
        return obj.status in ['pending', 'processing']

    def create(self, validated_data):
        return super().create(validated_data)

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)

class AddToCartRequestSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    variant_id = serializers.IntegerField(required=False)
    quantity = serializers.IntegerField(default=1)

class CartResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    cart_item = CartItemSerializer()

class OrderResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    order = OrderSerializer()

class PromoCodeSerializer(serializers.ModelSerializer):
    is_valid = serializers.SerializerMethodField()
    validity_message = serializers.SerializerMethodField()
    discount_amount = serializers.SerializerMethodField()
    
    class Meta:
        model = PromoCode
        fields = [
            'id', 'code', 'description', 'discount_type', 'discount_value',
            'min_order_amount', 'max_discount_amount', 'start_date', 'end_date',
            'usage_limit', 'usage_count', 'per_user_limit', 'status',
            'is_first_purchase_only', 'is_new_user_only', 'is_birthday_only',
            'is_seasonal', 'seasonal_start_month', 'seasonal_end_month',
            'applicable_categories', 'applicable_products', 'excluded_products',
            'min_items_in_cart', 'max_items_in_cart', 'is_valid',
            'validity_message', 'discount_amount'
        ]
        read_only_fields = ['usage_count', 'is_valid', 'validity_message', 'discount_amount']
    
    def get_is_valid(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
            
        cart = request.user.cart
        if not cart:
            return False
            
        cart_total = cart.total_price
        cart_items_count = cart.items.count()
        
        is_valid, _ = obj.is_valid(request.user, cart_total, cart_items_count)
        return is_valid
    
    def get_validity_message(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return "Please login to use promo code"
            
        cart = request.user.cart
        if not cart:
            return "Add items to cart first"
            
        cart_total = cart.total_price
        cart_items_count = cart.items.count()
        
        _, message = obj.is_valid(request.user, cart_total, cart_items_count)
        return message
    
    def get_discount_amount(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return 0
            
        cart = request.user.cart
        if not cart:
            return 0
            
        try:
            return obj.calculate_discount(cart.total_price, cart.items.all())
        except:
            return 0
    
    def validate(self, attrs):
        # Validate dates
        if attrs.get('start_date') and attrs.get('end_date'):
            if attrs['start_date'] >= attrs['end_date']:
                raise serializers.ValidationError("End date must be after start date")
        
        # Validate seasonal months
        if attrs.get('is_seasonal'):
            if not attrs.get('seasonal_start_month') or not attrs.get('seasonal_end_month'):
                raise serializers.ValidationError("Seasonal months are required for seasonal promo codes")
            if not (1 <= attrs['seasonal_start_month'] <= 12 and 1 <= attrs['seasonal_end_month'] <= 12):
                raise serializers.ValidationError("Invalid month values")
        
        # Validate discount values
        if attrs.get('discount_type') == 'percentage':
            if not (0 < attrs.get('discount_value', 0) <= 100):
                raise serializers.ValidationError("Percentage discount must be between 0 and 100")
        
        return attrs

class ApplyPromoCodeSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=50)
    
    def validate_code(self, value):
        try:
            promo_code = PromoCode.objects.get(code=value)
            if promo_code.status != 'active':
                raise serializers.ValidationError("Promo code is not active")
            return value
        except PromoCode.DoesNotExist:
            raise serializers.ValidationError("Invalid promo code")
    
    def validate(self, attrs):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("Please login to use promo code")
            
        cart = request.user.cart
        if not cart:
            raise serializers.ValidationError("Add items to cart first")
            
        promo_code = PromoCode.objects.get(code=attrs['code'])
        is_valid, message = promo_code.is_valid(
            request.user,
            cart.total_price,
            cart.items.count()
        )
        
        if not is_valid:
            raise serializers.ValidationError(message)
            
        return attrs