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
from django.utils import timezone
from datetime import timedelta
from drf_spectacular.utils import extend_schema_field

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

class SubcategorySerializer(serializers.ModelSerializer):
    gender = GenderCategorySerializer(read_only=True)
    products_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Subcategory
        fields = ['id', 'name', 'slug', 'description', 'gender', 'image', 'is_active', 'products_count', 'created_at']

class CategorySerializer(serializers.ModelSerializer):
    gender = GenderCategorySerializer(read_only=True)
    subcategories = SubcategorySerializer(many=True, read_only=True)
    products_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'gender', 'image', 'subcategories', 'products_count', 'created_at']
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

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'is_primary']

class ProductVariantSerializer(serializers.ModelSerializer):
    color_name = serializers.CharField(source='color.name', read_only=True)
    color_hex = serializers.CharField(source='color.hex_code', read_only=True)
    size_name = serializers.CharField(source='size.name', read_only=True)
    size_eu = serializers.CharField(source='size.size_eu', read_only=True)
    size_us = serializers.CharField(source='size.size_us', read_only=True)
    size_uk = serializers.CharField(source='size.size_uk', read_only=True)
    size_fr = serializers.CharField(source='size.size_fr', read_only=True)
    
    class Meta:
        model = ProductVariant
        fields = ['id', 'color', 'color_name', 'color_hex', 'size', 'size_name', 'size_eu', 'size_us', 'size_uk', 'size_fr', 'stock']
        read_only_fields = ['color_name', 'color_hex', 'size_name', 'size_eu', 'size_us', 'size_uk', 'size_fr']

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
    # Asosiy ma'lumotlar
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_slug = serializers.CharField(source='product.slug', read_only=True)
    product_price = serializers.DecimalField(source='product.price', max_digits=10, decimal_places=2, read_only=True)
    product_discount_price = serializers.DecimalField(source='product.discount_price', max_digits=10, decimal_places=2, read_only=True, allow_null=True)
    
    # Variant ma'lumotlari
    variant_details = serializers.SerializerMethodField()
    
    # Rasmlar
    product_images = serializers.SerializerMethodField()
    
    # Qo'shimcha ma'lumotlar
    total_price = serializers.SerializerMethodField()
    discount_amount = serializers.SerializerMethodField()
    savings_percentage = serializers.SerializerMethodField()
    
    # Batafsil mahsulot ma'lumotlari
    product_details = serializers.SerializerMethodField()
    
    # Mahsulot mavjudligi
    in_stock = serializers.SerializerMethodField()
    
    # Takliflar
    recommendations = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = [
            'id', 'product', 'product_name', 'product_slug', 'product_images',
            'product_price', 'product_discount_price', 'quantity',
            'variant_details', 'total_price', 'discount_amount', 
            'savings_percentage', 'product_details', 'in_stock',
            'recommendations', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'product_name', 'product_slug', 'product_images',
            'product_price', 'product_discount_price',
            'variant_details', 'total_price', 'discount_amount', 
            'savings_percentage', 'product_details', 'in_stock',
            'recommendations', 'created_at', 'updated_at'
        ]

    def get_variant_details(self, obj):
        """Variant haqida to'liq ma'lumot"""
        if not obj.variant:
            return None
            
        return {
            'id': obj.variant.id,
            'color': {
                'id': obj.variant.color.id,
                'name': obj.variant.color.name,
                'hex_code': obj.variant.color.hex_code
            },
            'size': {
                'id': obj.variant.size.id,
                'name': obj.variant.size.name,
                'size_eu': obj.variant.size.size_eu,
                'size_us': obj.variant.size.size_us,
                'size_uk': obj.variant.size.size_uk,
                'size_fr': obj.variant.size.size_fr
            },
            'stock': obj.variant.stock,
            'available': obj.variant.stock > 0,
            'max_order_quantity': min(obj.variant.stock, 10) if obj.variant.stock > 0 else 0
        }

    def get_product_images(self, obj):
        """Mahsulot rasmlari (variantga qarab)"""
        request = self.context.get('request')
        base_url = request.build_absolute_uri('/')[:-1] if request else ''
        
        # Variant bo'yicha rasm
        if obj.variant:
            images = ProductImage.objects.filter(
                product=obj.product,
                color=obj.variant.color
            ).order_by('-is_primary')
        else:
            # Barcha rasmlar
            images = obj.product.images.all().order_by('-is_primary')
        
        result = []
        for img in images:
            image_url = f"{base_url}{img.image.url}" if base_url else img.image.url
            result.append({
                'id': img.id,
                'url': image_url,
                'is_primary': img.is_primary,
                'alt_text': img.alt_text or obj.product.name
            })
            
        return result

    def get_total_price(self, obj):
        """Umumiy narx"""
        return obj.total_price

    def get_discount_amount(self, obj):
        """Chegirma miqdori"""
        if not obj.product.discount_price:
            return 0
        return (obj.product.price - obj.product.discount_price) * obj.quantity

    def get_savings_percentage(self, obj):
        """Qancha foiz tejab qolish"""
        if not obj.product.discount_price or obj.product.price == 0:
            return 0
        return round(((obj.product.price - obj.product.discount_price) / obj.product.price) * 100)

    def get_product_details(self, obj):
        """Mahsulot haqida batafsil ma'lumot"""
        product = obj.product
        
        # Subcategory
        subcategory = {
            'id': product.subcategory.id,
            'name': product.subcategory.name,
            'slug': product.subcategory.slug
        } if product.subcategory else None
        
        # Brand
        brand = {
            'id': product.brand.id,
            'name': product.brand.name,
            'slug': product.brand.slug,
            'logo': product.brand.logo.url if product.brand and product.brand.logo else None
        } if product.brand else None
        
        # Materials
        materials = []
        for material in product.materials.all():
            materials.append({
                'id': material.id,
                'name': material.name
            })
            
        # Gender
        gender = {
            'id': product.gender.id,
            'name': product.gender.name
        } if product.gender else None
        
        return {
            'description': product.description,
            'subcategory': subcategory,
            'brand': brand,
            'materials': materials,
            'gender': gender,
            'is_featured': product.is_featured,
            'created_at': product.created_at,
        }

    def get_in_stock(self, obj):
        """Mahsulot ombordami yoki yo'qmi"""
        if obj.variant:
            return obj.variant.stock > 0
            
        # Agar variant bo'lmasa, mahsulotning har qanday varianti borligini tekshiramiz
        return obj.product.variants.filter(stock__gt=0).exists()

    def get_recommendations(self, obj):
        """Mahsulotga oid tavsiyalar"""
        # Shu mahsulot bilan birga sotib olingan mahsulotlar
        recommendations = ProductRecommendation.objects.filter(
            product=obj.product,
            recommendation_type__in=['bought_also_bought', 'viewed_also_viewed']
        ).select_related('recommended_product')[:3]
        
        result = []
        for rec in recommendations:
            product = rec.recommended_product
            primary_image = product.images.filter(is_primary=True).first()
            
            result.append({
                'id': product.id,
                'name': product.name,
                'slug': product.slug,
                'price': product.price,
                'discount_price': product.discount_price,
                'image': primary_image.image.url if primary_image else None,
                'recommendation_type': rec.get_recommendation_type_display()
            })
            
        return result

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
    
    @extend_schema_field(serializers.BooleanField())
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
    
    @extend_schema_field(serializers.CharField())
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
    
    @extend_schema_field(serializers.DecimalField(max_digits=10, decimal_places=2))
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

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True, source='active_items')
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    final_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    items_count = serializers.SerializerMethodField()
    total_savings = serializers.SerializerMethodField()
    total_items_quantity = serializers.SerializerMethodField()
    
    # Qo'shimcha ma'lumotlar
    available_shipping_methods = serializers.SerializerMethodField()
    available_promo_codes = serializers.SerializerMethodField()
    applied_promo_code = serializers.SerializerMethodField()
    estimated_delivery = serializers.SerializerMethodField()
    
    # Savatchadagi xususiyatlar
    has_discounted_items = serializers.SerializerMethodField()
    has_out_of_stock_items = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = [
            'id', 'items', 'total_price', 'final_price', 'items_count', 
            'total_savings', 'total_items_quantity', 'promo_code_discount',
            'available_shipping_methods', 'available_promo_codes', 'applied_promo_code',
            'estimated_delivery', 'has_discounted_items', 'has_out_of_stock_items',
            'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = [
            'id', 'items', 'total_price', 'final_price', 'items_count',
            'total_savings', 'total_items_quantity', 'promo_code_discount',
            'available_shipping_methods', 'available_promo_codes', 'applied_promo_code',
            'estimated_delivery', 'has_discounted_items', 'has_out_of_stock_items',
            'created_at', 'updated_at'
        ]

    @extend_schema_field(serializers.IntegerField())
    def get_items_count(self, obj):
        """Savatchadagi mahsulotlar soni"""
        return obj.active_items.count()

    @extend_schema_field(serializers.DecimalField(max_digits=10, decimal_places=2))
    def get_total_savings(self, obj):
        """Umumiy tejalgan miqdor"""
        total_savings = 0
        for item in obj.active_items.all():
            if item.product.discount_price:
                savings = (item.product.price - item.product.discount_price) * item.quantity
                total_savings += savings
        return total_savings
    
    @extend_schema_field(serializers.IntegerField())
    def get_total_items_quantity(self, obj):
        """Savatchadagi mahsulotlar umumiy miqdori"""
        return sum(item.quantity for item in obj.active_items.all())
    
    @extend_schema_field(serializers.ListField(child=ShippingMethodSerializer()))
    def get_available_shipping_methods(self, obj):
        """Mavjud yetkazib berish usullari"""
        if not obj.active_items.exists():
            return []
        shipping_methods = obj.get_available_shipping_methods()
        result = []
        for method in shipping_methods:
            shipping_cost = method.calculate_shipping_cost(obj.total_price)
            result.append({
                'id': method.id,
                'name': method.name,
                'delivery_type': method.delivery_type,
                'delivery_type_display': method.get_delivery_type_display(),
                'min_days': method.min_days,
                'max_days': method.max_days,
                'price': shipping_cost,
                'description': method.description,
                'is_free': shipping_cost == 0,
                'free_shipping_threshold': method.free_shipping_threshold
            })
        return sorted(result, key=lambda x: x['price'])
    
    @extend_schema_field(serializers.ListField(child=PromoCodeSerializer()))
    def get_available_promo_codes(self, obj):
        """Foydalanuvchi uchun mavjud promo kodlar"""
        user = self.context.get('request').user if self.context.get('request') else None
        if not user or not user.is_authenticated:
            return []
        promo_codes = PromoCode.objects.filter(
            status='active',
            start_date__lte=timezone.now(),
            end_date__gte=timezone.now()
        )
        result = []
        for promo in promo_codes:
            is_valid, message = promo.is_valid(user, obj.total_price, obj.active_items.count())
            if is_valid:
                discount = promo.calculate_discount(obj.total_price, obj.active_items.all())
                result.append({
                    'id': promo.id,
                    'code': promo.code,
                    'description': promo.description,
                    'discount_type': promo.discount_type,
                    'discount_type_display': promo.get_discount_type_display(),
                    'discount_value': promo.discount_value,
                    'estimated_discount': discount
                })
        return result
    
    @extend_schema_field(PromoCodeSerializer())
    def get_applied_promo_code(self, obj):
        """Qo'llanilgan promo kod ma'lumotlari"""
        if not obj.promo_code:
            return None
        return {
            'id': obj.promo_code.id,
            'code': obj.promo_code.code,
            'description': obj.promo_code.description,
            'discount_type': obj.promo_code.discount_type,
            'discount_type_display': obj.promo_code.get_discount_type_display(),
            'discount_value': obj.promo_code.discount_value,
            'applied_discount': obj.promo_code_discount
        }
    
    @extend_schema_field(serializers.DictField())
    def get_estimated_delivery(self, obj):
        """Taxminiy yetkazib berish vaqtlari"""
        if not obj.active_items.exists():
            return None
        shipping_methods = obj.get_available_shipping_methods()
        if not shipping_methods:
            return None
        today = timezone.now().date()
        fastest = min(shipping_methods, key=lambda x: x.min_days)
        slowest = max(shipping_methods, key=lambda x: x.max_days)
        return {
            'fastest': {
                'method': fastest.name,
                'delivery_type': fastest.get_delivery_type_display(),
                'min_date': (today + timedelta(days=fastest.min_days)).strftime('%Y-%m-%d'),
                'max_date': (today + timedelta(days=fastest.max_days)).strftime('%Y-%m-%d'),
            },
            'slowest': {
                'method': slowest.name,
                'delivery_type': slowest.get_delivery_type_display(),
                'min_date': (today + timedelta(days=slowest.min_days)).strftime('%Y-%m-%d'),
                'max_date': (today + timedelta(days=slowest.max_days)).strftime('%Y-%m-%d'),
            }
        }
    
    @extend_schema_field(serializers.BooleanField())
    def get_has_discounted_items(self, obj):
        """Savatchada chegirmali mahsulotlar bormi?"""
        return obj.active_items.filter(product__discount_price__isnull=False).exists()
    
    @extend_schema_field(serializers.BooleanField())
    def get_has_out_of_stock_items(self, obj):
        """Savatchada omborda yo'q mahsulotlar bormi?"""
        for item in obj.active_items.all():
            if item.variant and item.variant.stock <= 0:
                return True
        return False

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
        queryset=Address.objects.filter(branch_type__in=['store', 'pickup']),
        source='pickup_branch',
        write_only=True,
        required=False
    )
    cart_id = serializers.PrimaryKeyRelatedField(
        queryset=Cart.objects.filter(is_active=True),
        write_only=True,
        required=False
    )
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    items_count = serializers.SerializerMethodField(read_only=True)
    can_cancel = serializers.SerializerMethodField(read_only=True)
    shipping_info = serializers.SerializerMethodField(read_only=True)
    estimated_delivery_date = serializers.SerializerMethodField(read_only=True)
    active_branches = serializers.SerializerMethodField(read_only=True)
    split_payment_info = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'user', 'cart_id', 'items', 'total_amount', 'discount_amount',
            'shipping_amount', 'final_amount', 'status', 'shipping_method',
            'shipping_method_id', 'pickup_branch', 'pickup_branch_id',
            'tracking_number', 'order_note', 'customer_name', 'phone_number',
            'payment_method', 'payment_status', 'created_at', 'updated_at',
            'status_display', 'payment_method_display', 'items_count', 'can_cancel',
            'shipping_info', 'estimated_delivery_date', 'active_branches',
            'is_split_payment', 'first_payment_amount', 'first_payment_date',
            'second_payment_amount', 'second_payment_due_date', 'second_payment_status',
            'split_payment_info'
        ]
        read_only_fields = ['id', 'user', 'items', 'total_amount', 'discount_amount',
                           'shipping_amount', 'final_amount', 'status', 'created_at', 'updated_at']

    @extend_schema_field(serializers.IntegerField())
    def get_items_count(self, obj):
        return obj.items.count()

    @extend_schema_field(serializers.BooleanField())
    def get_can_cancel(self, obj):
        return obj.status in ['pending', 'processing']
        
    @extend_schema_field(serializers.DictField())
    def get_shipping_info(self, obj):
        """Return user-friendly shipping information based on delivery type"""
        if not obj.shipping_method:
            return None
            
        info = {
            'method': obj.shipping_method.name,
            'delivery_type': obj.shipping_method.get_delivery_type_display(),
            'min_days': obj.shipping_method.min_days,
            'max_days': obj.shipping_method.max_days,
            'price': obj.shipping_amount,
        }
        
        if obj.shipping_method.delivery_type == 'branch_pickup' and obj.pickup_branch:
            info['pickup_location'] = {
                'name': obj.pickup_branch.name,
                'address': f"{obj.pickup_branch.street}, {obj.pickup_branch.district}, {obj.pickup_branch.city}",
                'working_hours': obj.pickup_branch.working_hours,
                'phone': obj.pickup_branch.phone,
                'has_fitting_room': obj.pickup_branch.has_fitting_room,
                'has_parking': obj.pickup_branch.has_parking,
                'is_24_hours': obj.pickup_branch.is_24_hours,
                'location_link': obj.pickup_branch.location_link or None,
            }
            
        return info
        
    @extend_schema_field(serializers.DictField())
    def get_estimated_delivery_date(self, obj):
        """Calculate estimated delivery date range based on shipping method"""
        if not obj.shipping_method or not obj.created_at:
            return None
            
        from datetime import timedelta
        
        min_date = obj.created_at + timedelta(days=obj.shipping_method.min_days)
        max_date = obj.created_at + timedelta(days=obj.shipping_method.max_days)
        
        return {
            'min_date': min_date.strftime('%Y-%m-%d'),
            'max_date': max_date.strftime('%Y-%m-%d'),
            'formatted': f"{min_date.strftime('%d.%m.%Y')} - {max_date.strftime('%d.%m.%Y')}"
        }
        
    @extend_schema_field(serializers.ListField(child=AddressSerializer()))
    def get_active_branches(self, obj):
        """Return list of active branches for pickup"""
        # Only return when creating a new order
        if obj.pk:
            return None
            
        branches = Address.objects.filter(
            branch_type__in=['store', 'pickup'],
            is_active=True
        ).values('id', 'name', 'street', 'district', 'city', 'working_hours', 'location_link')
        
        return branches

    @extend_schema_field(serializers.DictField())
    def get_split_payment_info(self, obj):
        """Return split payment information if applicable"""
        if not obj.is_split_payment:
            return None
            
        now = timezone.now()
        first_payment_overdue = False
        second_payment_overdue = False
        
        # Check if first payment is overdue
        if obj.first_payment_date and obj.payment_status == 'pending':
            first_payment_overdue = now - obj.first_payment_date > timedelta(days=1)
            
        # Check if second payment is overdue
        if obj.second_payment_due_date and obj.second_payment_status == 'pending':
            second_payment_overdue = now > obj.second_payment_due_date
            
        # Calculate days remaining for second payment
        days_remaining = 0
        if obj.second_payment_due_date and not second_payment_overdue:
            days_remaining = (obj.second_payment_due_date - now).days
            
        return {
            'first_payment': {
                'amount': float(obj.first_payment_amount) if obj.first_payment_amount else 0,
                'date': obj.first_payment_date.strftime('%Y-%m-%d') if obj.first_payment_date else None,
                'status': obj.payment_status,
                'due_date': obj.first_payment_date.strftime('%Y-%m-%d') if obj.first_payment_date else None,
                'is_overdue': first_payment_overdue,
                'is_paid': obj.payment_status == 'delivered'
            },
            'second_payment': {
                'amount': float(obj.second_payment_amount) if obj.second_payment_amount else 0,
                'due_date': obj.second_payment_due_date.strftime('%Y-%m-%d') if obj.second_payment_due_date else None,
                'status': obj.second_payment_status,
                'is_overdue': second_payment_overdue,
                'is_paid': obj.second_payment_status == 'delivered',
                'days_remaining': days_remaining
            },
            'total_amount': float(obj.final_amount),
            'remaining_amount': float(obj.second_payment_amount) if obj.payment_status == 'delivered' and obj.second_payment_status == 'pending' else 0,
            'payment_schedule': {
                'first_payment_due': 'Darhol',
                'second_payment_due': f"30 kun ichida ({obj.second_payment_due_date.strftime('%Y-%m-%d')} gacha)" if obj.second_payment_due_date else 'N/A'
            }
        }

    def validate(self, data):
        # Only pickup_branch is required
        if not data.get('pickup_branch'):
            raise serializers.ValidationError({
                'pickup_branch_id': 'Pickup branch is required.'
            })
        return data

    def create(self, validated_data):
        cart = validated_data.pop('cart_id', None)
        if not cart:
            raise serializers.ValidationError({'cart_id': 'Cart is required'})
        
        # Get user from request context
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
        
        # Create order with required fields and initial zero values for totals
        order = Order(
            user=user,
            pickup_branch=validated_data['pickup_branch'],
            shipping_method=validated_data.get('shipping_method'),
            customer_name=validated_data['customer_name'],
            phone_number=validated_data['phone_number'],
            payment_method=validated_data['payment_method'],
            order_note=validated_data.get('order_note', ''),
            total_amount=0,
            discount_amount=0,
            shipping_amount=0,
            final_amount=0,
            status='pending'
        )
        
        # Save the order first
        order.save()
        
        # Add items from cart
        for item in cart.active_items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                variant=item.variant,
                quantity=item.quantity,
                price=item.product.discount_price or item.product.price
            )
            
        # Calculate totals
        order.calculate_totals()
        order.save()  # Save again after calculating totals

        # Deactivate cart
        cart.is_active = False
        cart.save()
        
        return order

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

class DirectPurchaseSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    variant_id = serializers.IntegerField(required=False)
    quantity = serializers.IntegerField(default=1)
    pickup_branch_id = serializers.IntegerField()
    payment_method = serializers.ChoiceField(choices=Order.PAYMENT_METHOD_CHOICES)
    customer_name = serializers.CharField(max_length=100)
    phone_number = serializers.CharField(max_length=20)
    order_note = serializers.CharField(required=False, allow_blank=True)
    is_split_payment = serializers.BooleanField(default=False)

    def validate_product_id(self, value):
        try:
            product = Product.objects.get(id=value)
            if not product.is_active:
                raise serializers.ValidationError("Mahsulot mavjud emas")
            return value
        except Product.DoesNotExist:
            raise serializers.ValidationError("Mahsulot topilmadi")

    def validate_variant_id(self, value):
        if value:
            try:
                variant = ProductVariant.objects.get(id=value)
                if variant.stock <= 0:
                    raise serializers.ValidationError("Bu variant omborda yo'q")
                return value
            except ProductVariant.DoesNotExist:
                raise serializers.ValidationError("Variant topilmadi")
        return value

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Miqdor 0 dan katta bo'lishi kerak")
        return value

    def validate_pickup_branch_id(self, value):
        try:
            branch = Address.objects.get(id=value, branch_type__in=['store', 'pickup'], is_active=True)
            return value
        except Address.DoesNotExist:
            raise serializers.ValidationError("Filial topilmadi yoki faol emas")

    def validate(self, data):
        # Check product stock
        product = Product.objects.get(id=data['product_id'])
        if data.get('variant_id'):
            variant = ProductVariant.objects.get(id=data['variant_id'])
            if variant.stock < data['quantity']:
                raise serializers.ValidationError(f"Omborda faqat {variant.stock} dona mavjud")
        else:
            # Check if any variant has enough stock
            has_stock = False
            for variant in product.variants.all():
                if variant.stock >= data['quantity']:
                    has_stock = True
                    break
            if not has_stock:
                raise serializers.ValidationError("Mahsulot omborda yo'q")

        # Validate split payment
        if data.get('is_split_payment') and data['payment_method'] != 'split':
            raise serializers.ValidationError("Bo'lib to'lash uchun payment_method 'split' bo'lishi kerak")

        return data