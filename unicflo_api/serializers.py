from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .models import User, Product, Cart, CartItem, Order, OrderItem, Address, ProductReview, UserProfile
from .utils.telegram import TelegramService

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['telegram_chat_id']

class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone_number', 'created_at', 'profile']

class ProductReviewSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = ProductReview
        fields = ['id', 'user', 'rating', 'comment', 'created_at']

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise ValidationError("Rating must be between 1 and 5.")
        return value

class ProductSerializer(serializers.ModelSerializer):
    reviews = ProductReviewSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'size', 'color', 'brand', 'stock', 'created_at', 'reviews']

    def validate_price(self, value):
        if value <= 0:
            raise ValidationError("Price must be greater than zero.")
        return value

class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), source='product', write_only=True)

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_id', 'quantity']

    def validate_quantity(self, value):
        if value <= 0:
            raise ValidationError("Quantity must be greater than zero.")
        return value

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'user', 'items', 'created_at']

class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), source='product', write_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_id', 'quantity']

    def validate_quantity(self, value):
        if value <= 0:
            raise ValidationError("Quantity must be greater than zero.")
        return value

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    product_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True)

    class Meta:
        model = Order
        fields = ['id', 'user', 'items', 'product_ids', 'total_amount', 'status', 'shipping_address', 'created_at']

    def validate_product_ids(self, value):
        if not value:
            raise ValidationError("At least one product ID is required.")
        return value

    def validate_total_amount(self, value):
        if value <= 0:
            raise ValidationError("Total amount must be greater than zero.")
        return value

    def create(self, validated_data):
        product_ids = validated_data.pop('product_ids')
        order = Order.objects.create(**validated_data)
        for product_id in product_ids:
            product = Product.objects.get(id=product_id)
            OrderItem.objects.create(order=order, product=product, quantity=1)
        TelegramService.notify_order_status(order)
        return order

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        if 'status' in validated_data:
            TelegramService.notify_order_status(instance)
        return instance

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['id', 'user', 'street', 'city', 'country', 'postal_code', 'is_default']

    def validate(self, attrs):
        if not attrs.get('street') or not attrs.get('city') or not attrs.get('country'):
            raise ValidationError("Street, city, and country are required.")
        return attrs