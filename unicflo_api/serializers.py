from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .models import (
    User, UserProfile, Category, Product, ProductImage, ProductReview,
    Wishlist, Cart, CartItem, Coupon, Order, OrderItem, Address
)
from .utils.telegram import TelegramService

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['telegram_chat_id', 'profile_picture', 'bio', 'birth_date']

class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone_number', 'is_verified', 'created_at', 'profile']
        read_only_fields = ['is_verified']

class CategorySerializer(serializers.ModelSerializer):
    parent_name = serializers.StringRelatedField(source='parent', read_only=True)
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'image', 'parent', 'parent_name', 'created_at']

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'is_primary']

class ProductReviewSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    username = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = ProductReview
        fields = ['id', 'user', 'username', 'rating', 'comment', 'created_at', 'is_approved']
        read_only_fields = ['is_approved']

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise ValidationError("Rating must be between 1 and 5.")
        return value
    
    def create(self, validated_data):
        username = validated_data.pop('username', None)
        if username:
            try:
                user = User.objects.get(username=username)
                validated_data['user'] = user
            except User.DoesNotExist:
                raise ValidationError("User with this username does not exist.")
        return super().create(validated_data)

class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.StringRelatedField(source='category', read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    reviews = ProductReviewSerializer(many=True, read_only=True)
    average_rating = serializers.SerializerMethodField()
    uploaded_images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'price', 'discount_price', 
            'category', 'category_name', 'size', 'color', 'brand', 'stock',
            'is_featured', 'is_active', 'created_at', 'updated_at',
            'images', 'reviews', 'average_rating', 'uploaded_images'
        ]
        read_only_fields = ['slug']

    def get_average_rating(self, obj):
        reviews = obj.reviews.all()
        if not reviews:
            return 0
        return sum(review.rating for review in reviews) / len(reviews)

    def validate_price(self, value):
        if value <= 0:
            raise ValidationError("Price must be greater than zero.")
        return value
    
    def create(self, validated_data):
        uploaded_images = validated_data.pop('uploaded_images', [])
        product = Product.objects.create(**validated_data)
        
        for i, image in enumerate(uploaded_images):
            ProductImage.objects.create(
                product=product,
                image=image,
                is_primary=(i == 0)  # First image as primary
            )
        
        return product

class WishlistSerializer(serializers.ModelSerializer):
    products = ProductSerializer(many=True, read_only=True)
    product_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Wishlist
        fields = ['id', 'user', 'products', 'product_ids', 'created_at']
    
    def create(self, validated_data):
        product_ids = validated_data.pop('product_ids', [])
        wishlist = Wishlist.objects.create(**validated_data)
        
        if product_ids:
            products = Product.objects.filter(id__in=product_ids)
            wishlist.products.add(*products)
        
        return wishlist

class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), source='product', write_only=True)
    total_price = serializers.DecimalField(read_only=True, max_digits=10, decimal_places=2)

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_id', 'quantity', 'total_price', 'created_at', 'updated_at']

    def validate_quantity(self, value):
        if value <= 0:
            raise ValidationError("Quantity must be greater than zero.")
        return value
    
    def validate(self, attrs):
        # Check if product is in stock
        product = attrs.get('product')
        quantity = attrs.get('quantity', 1)
        
        if product and product.stock < quantity:
            raise ValidationError(f"Not enough stock available. Only {product.stock} units left.")
        
        return attrs

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.DecimalField(read_only=True, max_digits=10, decimal_places=2)

    class Meta:
        model = Cart
        fields = ['id', 'user', 'items', 'total_price', 'created_at', 'updated_at']

class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = [
            'id', 'code', 'description', 'discount_percent', 'discount_amount',
            'min_purchase', 'valid_from', 'valid_to', 'is_active', 'created_at'
        ]
        read_only_fields = ['is_active']

class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), source='product', write_only=True)
    total_price = serializers.DecimalField(read_only=True, max_digits=10, decimal_places=2)

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_id', 'quantity', 'price', 'total_price', 'created_at']

    def validate_quantity(self, value):
        if value <= 0:
            raise ValidationError("Quantity must be greater than zero.")
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
        if not attrs.get('street') or not attrs.get('city') or not attrs.get('country') or not attrs.get('full_name'):
            raise ValidationError("Full name, street, city, and country are required.")
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
    coupon_code = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Order
        fields = [
            'id', 'user', 'items', 'total_amount', 'discount_amount', 'shipping_amount',
            'final_amount', 'status', 'payment_method', 'payment_status',
            'shipping_address', 'shipping_address_id', 'billing_address', 'billing_address_id',
            'tracking_number', 'order_note', 'created_at', 'updated_at',
            'cart_id', 'coupon_code'
        ]
        read_only_fields = ['total_amount', 'discount_amount', 'final_amount', 'payment_status']

    def validate_cart_id(self, value):
        try:
            cart = Cart.objects.get(id=value)
            if cart.items.count() == 0:
                raise ValidationError("Cart is empty.")
            return value
        except Cart.DoesNotExist:
            raise ValidationError("Cart does not exist.")

    def validate(self, attrs):
        # Validate shipping address belongs to user
        shipping_address = attrs.get('shipping_address')
        if shipping_address and shipping_address.user != attrs.get('user'):
            raise ValidationError("Shipping address does not belong to this user.")

        # Validate billing address belongs to user
        billing_address = attrs.get('billing_address')
        if billing_address and billing_address.user != attrs.get('user'):
            raise ValidationError("Billing address does not belong to this user.")

        return attrs

    def create(self, validated_data):
        # Get cart items
        cart_id = validated_data.pop('cart_id')
        cart = Cart.objects.get(id=cart_id)
        cart_items = cart.items.all()
        
        # Calculate totals
        total_amount = sum(item.product.price * item.quantity for item in cart_items)
        
        # Apply coupon if provided
        coupon_code = validated_data.pop('coupon_code', None)
        discount_amount = 0
        
        if coupon_code:
            try:
                coupon = Coupon.objects.get(code=coupon_code, is_active=True)
                if total_amount >= coupon.min_purchase:
                    if coupon.discount_percent > 0:
                        discount_amount = (total_amount * coupon.discount_percent) / 100
                    else:
                        discount_amount = coupon.discount_amount
                    validated_data['coupon'] = coupon
            except Coupon.DoesNotExist:
                pass
        
        # Set shipping amount (could be dynamic based on location/weight)
        shipping_amount = 10.00  # Default shipping cost
        
        # Calculate final amount
        final_amount = total_amount - discount_amount + shipping_amount
        
        # Create order
        validated_data.update({
            'total_amount': total_amount,
            'discount_amount': discount_amount,
            'shipping_amount': shipping_amount,
            'final_amount': final_amount
        })
        
        order = Order.objects.create(**validated_data)
        
        # Create order items
        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                price=cart_item.product.price  # Store the price at time of purchase
            )
            
            # Update product stock
            product = cart_item.product
            product.stock -= cart_item.quantity
            product.save()
        
        # Clear cart after order is created
        cart.items.all().delete()
        
        # Send notification
        TelegramService.notify_order_status(order)
        
        return order

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        if 'status' in validated_data:
            TelegramService.notify_order_status(instance)
        return instance