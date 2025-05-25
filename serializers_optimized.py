from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .models import (
    User, Category, Product, ProductImage,
    Wishlist, Cart, CartItem, Order, OrderItem, Address, Subcategory, Brand, Size, Material, Season, ShippingMethod, ProductVariant, GenderCategory,
    Color, PromoCode
)
from .utils.telegram import TelegramService
from django.shortcuts import get_object_or_404

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
        fields = ['id', 'name', 'slug', 'description']

class SubcategorySerializer(serializers.ModelSerializer):
    gender = GenderCategorySerializer(read_only=True)
    products_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Subcategory
        fields = [
            'id', 
            'name', 
            'slug', 
            'description', 
            'gender', 
            'image', 
            'is_active',
            'created_at',
            'products_count'
        ]

class CategorySerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False)
    gender = GenderCategorySerializer(read_only=True)
    subcategories = SubcategorySerializer(many=True, read_only=True)
    products_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Category
        fields = [
            'id', 
            'name', 
            'slug', 
            'description', 
            'gender', 
            'image', 
            'created_at',
            'subcategories',
            'products_count'
        ]

class BrandSerializer(serializers.ModelSerializer):
    products_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Brand
        fields = ['id', 'name', 'slug', 'description', 'logo', 'created_at', 'products_count']

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
        fields = ['id', 'name', 'min_days', 'max_days', 'price', 'is_active', 'created_at']

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'is_primary']

class ProductVariantSerializer(serializers.ModelSerializer):
    color = ColorSerializer(read_only=True)
    size = SizeSerializer(read_only=True)
    
    class Meta:
        model = ProductVariant
        fields = ['id', 'color', 'size', 'stock']

class ProductSerializer(serializers.ModelSerializer):
    subcategory = SubcategorySerializer(read_only=True)
    subcategory_id = serializers.PrimaryKeyRelatedField(
        queryset=Subcategory.objects.all(),
        source='subcategory',
        write_only=True
    )
    brand = BrandSerializer(read_only=True)
    brand_id = serializers.PrimaryKeyRelatedField(
        queryset=Brand.objects.all(),
        source='brand',
        write_only=True,
        required=False
    )
    gender = GenderCategorySerializer(read_only=True)
    gender_id = serializers.PrimaryKeyRelatedField(
        queryset=GenderCategory.objects.all(),
        source='gender',
        write_only=True,
        required=False
    )
    season = SeasonSerializer(read_only=True)
    season_id = serializers.PrimaryKeyRelatedField(
        queryset=Season.objects.all(),
        source='season',
        write_only=True,
        required=False
    )
    materials = MaterialSerializer(many=True, read_only=True)
    material_ids = serializers.PrimaryKeyRelatedField(
        queryset=Material.objects.all(),
        source='materials',
        write_only=True,
        many=True,
        required=False
    )
    shipping_methods = ShippingMethodSerializer(many=True, read_only=True)
    shipping_method_ids = serializers.PrimaryKeyRelatedField(
        queryset=ShippingMethod.objects.all(),
        source='shipping_methods',
        write_only=True,
        many=True,
        required=False
    )
    variants = ProductVariantSerializer(many=True, read_only=True, source='variants.all')
    images = ProductImageSerializer(many=True, read_only=True)
    likes_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    uploaded_images = serializers.ListField(
        child=serializers.ImageField(),
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
        read_only_fields = ['slug']

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
        materials = validated_data.pop('materials', [])
        shipping_methods = validated_data.pop('shipping_methods', [])
        
        product = Product.objects.create(**validated_data)
        
        if materials:
            product.materials.set(materials)
        
        if shipping_methods:
            product.shipping_methods.set(shipping_methods)
        
        for i, image in enumerate(uploaded_images):
            ProductImage.objects.create(
                product=product,
                image=image,
                is_primary=(i == 0)
            )
        
        return product

class WishlistSerializer(serializers.ModelSerializer):
    products = ProductSerializer(many=True, read_only=True)
    product_ids = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(queryset=Product.objects.all()),
        write_only=True,
        required=False
    )

    class Meta:
        model = Wishlist
        fields = ['id', 'user', 'products', 'product_ids', 'created_at']
    
    def create(self, validated_data):
        product_ids = validated_data.pop('product_ids', [])
        wishlist = Wishlist.objects.create(**validated_data)
        wishlist.products.set(product_ids)
        return wishlist

class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_id', 'quantity', 'total_price']
        read_only_fields = ['id', 'total_price']

    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError("Quantity must be at least 1")
        return value

    def create(self, validated_data):
        cart = self.context.get('cart')
        product_id = validated_data.pop('product_id')
        quantity = validated_data.get('quantity', 1)

        # Check if item already exists in cart
        cart_item = CartItem.objects.filter(cart=cart, product_id=product_id).first()
        if cart_item:
            # Update quantity if item exists
            cart_item.quantity += quantity
            cart_item.save()
            return cart_item

        # Create new cart item
        return CartItem.objects.create(
            cart=cart,
            product_id=product_id,
            quantity=quantity
        )

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'user', 'items', 'total_price', 'created_at', 'updated_at']
        read_only_fields = ['user', 'total_price']

class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), source='product', write_only=True)
    total_price = serializers.DecimalField(read_only=True, max_digits=10, decimal_places=2)

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_id', 'quantity', 'price', 'total_price', 'created_at']

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero")
        return value

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = [
            'id', 'user', 'address_type', 'full_name', 'street', 'apartment',
            'city', 'state', 'country', 'postal_code', 'phone', 'is_default',
            'created_at', 'updated_at'
        ]

    def validate(self, attrs):
        # If this address is being set as default, unset any other default addresses
        if attrs.get('is_default'):
            Address.objects.filter(
                user=attrs.get('user'),
                address_type=attrs.get('address_type'),
                is_default=True
            ).update(is_default=False)
        return attrs

        return attrs

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    shipping_address = AddressSerializer(read_only=True)
    billing_address = AddressSerializer(read_only=True)
    shipping_address_id = serializers.PrimaryKeyRelatedField(
        queryset=Address.objects.all(),
        source='shipping_address',
        write_only=True
    )
    billing_address_id = serializers.PrimaryKeyRelatedField(
        queryset=Address.objects.all(),
        source='billing_address',
        write_only=True,
        required=False
    )
    cart_id = serializers.IntegerField(write_only=True)
    promo_code = serializers.PrimaryKeyRelatedField(queryset=PromoCode.objects.all(), required=False, allow_null=True, write_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'user', 'items', 'total_amount', 'discount_amount', 'shipping_amount',
            'final_amount', 'promo_code_discount', 'status', 'shipping_address',
            'shipping_address_id', 'billing_address', 'billing_address_id',
            'tracking_number', 'order_note', 'phone_number', 'cart_id',
            'payment_method', 'delivery_notes', 'gift_wrapping',
            'estimated_delivery_date', 'preferred_delivery_time',
            'save_shipping_address', 'save_billing_address', 'created_at', 'updated_at', 'promo_code'
        ]
        read_only_fields = ['user', 'total_amount', 'discount_amount', 'shipping_amount', 'final_amount', 'promo_code_discount']

    def validate_cart_id(self, value):
        user = self.context['request'].user
        try:
            cart = Cart.objects.get(id=value, user=user, is_active=True)
            if not cart.items.exists():
                raise serializers.ValidationError("Cart is empty")
            return value
        except Cart.DoesNotExist:
            raise serializers.ValidationError("Cart not found")

    def validate(self, attrs):
        user = self.context['request'].user
        shipping_address = attrs.get('shipping_address')
        billing_address = attrs.get('billing_address')
        if shipping_address and shipping_address.user != user:
            raise serializers.ValidationError({"shipping_address_id": "Invalid shipping address"})
        if billing_address and billing_address.user != user:
            raise serializers.ValidationError({"billing_address_id": "Invalid billing address"})
        return attrs

    def create(self, validated_data):
        from decimal import Decimal

        user = self.context['request'].user
        cart_id = validated_data.pop('cart_id')
        promo_code = validated_data.pop('promo_code', None)
        cart = Cart.objects.prefetch_related('items__product').get(id=cart_id, user=user, is_active=True)

        total_amount = cart.total_price
        shipping_amount = Decimal('0.00')
        discount_amount = Decimal('0.00')
        promo_discount = Decimal('0.00')

        if promo_code:
            is_valid, message = promo_code.is_valid(user, total_amount, cart.items.count())
            if is_valid:
                promo_discount = promo_code.calculate_discount(total_amount, cart.items.all())
                promo_code.usage_count += 1
                promo_code.save()
            else:
                raise serializers.ValidationError({"promo_code": message})

        final_amount = total_amount + shipping_amount - discount_amount - promo_discount

        order = Order.objects.create(
            user=user,
            total_amount=total_amount,
            shipping_amount=shipping_amount,
            discount_amount=discount_amount,
            promo_code_discount=promo_discount,
            final_amount=final_amount,
            promo_code=promo_code,
            **validated_data
        )

        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price
            )

        cart.is_active = False
        cart.save()

        return order