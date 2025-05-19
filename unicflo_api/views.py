from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from .models import (
    User, Category, Product, ProductImage, ProductReview,
    Wishlist, Cart, CartItem, Coupon, Order, Address
)
from .serializers import (
    UserSerializer, CategorySerializer, ProductSerializer, ProductImageSerializer, 
    ProductReviewSerializer, WishlistSerializer, CartSerializer, CartItemSerializer,
    CouponSerializer, OrderSerializer, AddressSerializer
)
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['username', 'email']

    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        return super().get_permissions()

    def get_queryset(self):
        if self.request.user.is_staff:
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)

    @swagger_auto_schema(
        operation_description="Retrieve or manage user profiles. Requires JWT authentication.",
        responses={
            200: UserSerializer(many=True),
            401: openapi.Response(description="Unauthorized"),
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [AllowAny()]

    @method_decorator(cache_page(60 * 15))
    @swagger_auto_schema(
        operation_description="List all categories. Publicly accessible.",
        responses={
            200: CategorySerializer(many=True),
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'brand', 'size', 'color', 'price', 'is_featured']
    search_fields = ['name', 'description', 'brand']
    ordering_fields = ['price', 'created_at', 'name']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [AllowAny()]

    @method_decorator(cache_page(60 * 15))
    @swagger_auto_schema(
        operation_description="List all products or filter by various attributes. Publicly accessible.",
        responses={
            200: ProductSerializer(many=True),
            400: openapi.Response(description="Invalid filter parameters"),
        },
        manual_parameters=[
            openapi.Parameter('category', openapi.IN_QUERY, description="Filter by category ID", type=openapi.TYPE_INTEGER),
            openapi.Parameter('brand', openapi.IN_QUERY, description="Filter by brand (e.g., Nike)", type=openapi.TYPE_STRING),
            openapi.Parameter('size', openapi.IN_QUERY, description="Filter by size (e.g., M)", type=openapi.TYPE_STRING),
            openapi.Parameter('color', openapi.IN_QUERY, description="Filter by color (e.g., Pink)", type=openapi.TYPE_STRING),
            openapi.Parameter('price', openapi.IN_QUERY, description="Filter by price", type=openapi.TYPE_NUMBER),
            openapi.Parameter('is_featured', openapi.IN_QUERY, description="Filter featured products", type=openapi.TYPE_BOOLEAN),
            openapi.Parameter('search', openapi.IN_QUERY, description="Search in name, description, and brand", type=openapi.TYPE_STRING),
            openapi.Parameter('ordering', openapi.IN_QUERY, description="Order by fields (e.g., price, -price, created_at)", type=openapi.TYPE_STRING),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @action(detail=True, methods=['get'])
    @method_decorator(cache_page(60 * 5))
    def similar_products(self, request, pk=None):
        """Get similar products based on category and brand"""
        product = self.get_object()
        similar_products = Product.objects.filter(
            category=product.category,
            is_active=True
        ).exclude(id=product.id)[:5]
        serializer = self.get_serializer(similar_products, many=True)
        return Response(serializer.data)

class ProductReviewViewSet(viewsets.ModelViewSet):
    queryset = ProductReview.objects.all()
    serializer_class = ProductReviewSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['product', 'rating']

    def get_queryset(self):
        if self.request.user.is_staff:
            return ProductReview.objects.all()
        return ProductReview.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @swagger_auto_schema(
        operation_description="Manage product reviews. Only accessible to the review owner or admin. Requires JWT authentication.",
        responses={
            200: ProductReviewSerializer(many=True),
            401: openapi.Response(description="Unauthorized"),
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @action(detail=False, methods=['get'])
    def product_reviews(self, request):
        """Get all reviews for a specific product"""
        product_id = request.query_params.get('product_id')
        if not product_id:
            return Response({"error": "Product ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        reviews = ProductReview.objects.filter(product_id=product_id, is_approved=True)
        serializer = self.get_serializer(reviews, many=True)
        return Response(serializer.data)

class WishlistViewSet(viewsets.ModelViewSet):
    queryset = Wishlist.objects.all()
    serializer_class = WishlistSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'])
    def add_product(self, request):
        """Add a product to the user's wishlist"""
        product_id = request.data.get('product_id')
        if not product_id:
            return Response({"error": "Product ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        wishlist, created = Wishlist.objects.get_or_create(user=request.user)
        try:
            product = Product.objects.get(id=product_id)
            wishlist.products.add(product)
            return Response({"message": f"{product.name} added to wishlist"}, status=status.HTTP_200_OK)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'])
    def remove_product(self, request):
        """Remove a product from the user's wishlist"""
        product_id = request.data.get('product_id')
        if not product_id:
            return Response({"error": "Product ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            wishlist = Wishlist.objects.get(user=request.user)
            product = Product.objects.get(id=product_id)
            wishlist.products.remove(product)
            return Response({"message": f"{product.name} removed from wishlist"}, status=status.HTTP_200_OK)
        except (Wishlist.DoesNotExist, Product.DoesNotExist):
            return Response({"error": "Wishlist or product not found"}, status=status.HTTP_404_NOT_FOUND)

class CartViewSet(viewsets.ModelViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @swagger_auto_schema(
        operation_description="Manage user carts. Only accessible to the cart owner. Requires JWT authentication.",
        responses={
            200: CartSerializer(many=True),
            401: openapi.Response(description="Unauthorized"),
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @action(detail=False, methods=['get'])
    def my_cart(self, request):
        """Get or create the user's active cart"""
        cart, created = Cart.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(cart)
        return Response(serializer.data)

class CartItemViewSet(viewsets.ModelViewSet):
    queryset = CartItem.objects.all()
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CartItem.objects.filter(cart__user=self.request.user)

    def perform_create(self, serializer):
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        serializer.save(cart=cart)

    @swagger_auto_schema(
        operation_description="Manage items in a user's cart. Only accessible to the cart owner. Requires JWT authentication.",
        responses={
            200: CartItemSerializer(many=True),
            401: openapi.Response(description="Unauthorized"),
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @action(detail=False, methods=['post'])
    def add_to_cart(self, request):
        """Add a product to the cart or update quantity if already exists"""
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))
        
        if not product_id:
            return Response({"error": "Product ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            product = Product.objects.get(id=product_id)
            if product.stock < quantity:
                return Response(
                    {"error": f"Not enough stock. Only {product.stock} available."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            cart, created = Cart.objects.get_or_create(user=request.user)
            cart_item, item_created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                defaults={'quantity': quantity}
            )
            
            if not item_created:
                cart_item.quantity += quantity
                cart_item.save()
            
            return Response({"message": f"{product.name} added to cart"}, status=status.HTTP_200_OK)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

class CouponViewSet(viewsets.ModelViewSet):
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'list']:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    @action(detail=False, methods=['post'])
    def validate(self, request):
        """Validate a coupon code"""
        code = request.data.get('code')
        if not code:
            return Response({"error": "Coupon code is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            coupon = Coupon.objects.get(code=code, is_active=True)
            serializer = self.get_serializer(coupon)
            return Response(serializer.data)
        except Coupon.DoesNotExist:
            return Response({"error": "Invalid or expired coupon code"}, status=status.HTTP_404_NOT_FOUND)

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'payment_status', 'payment_method']
    ordering_fields = ['created_at', 'total_amount']

    def get_queryset(self):
        if self.request.user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @swagger_auto_schema(
        operation_description="Manage user orders. Only accessible to the order owner or admin. Requires JWT authentication.",
        responses={
            200: OrderSerializer(many=True),
            401: openapi.Response(description="Unauthorized"),
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def cancel_order(self, request, pk=None):
        """Cancel an order if it's still in pending status"""
        order = self.get_object()
        if order.status != 'pending':
            return Response(
                {"error": "Only pending orders can be cancelled"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order.status = 'canceled'
        order.save()
        
        # Return items to stock
        for item in order.items.all():
            product = item.product
            product.stock += item.quantity
            product.save()
        
        return Response({"message": "Order cancelled successfully"}, status=status.HTTP_200_OK)

class AddressViewSet(viewsets.ModelViewSet):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # If this is set as default, unset any existing default
        if serializer.validated_data.get('is_default', False):
            Address.objects.filter(
                user=self.request.user,
                address_type=serializer.validated_data.get('address_type', 'both')
            ).update(is_default=False)
        serializer.save(user=self.request.user)

    @swagger_auto_schema(
        operation_description="Manage user addresses. Only accessible to the address owner. Requires JWT authentication.",
        responses={
            200: AddressSerializer(many=True),
            401: openapi.Response(description="Unauthorized"),
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @action(detail=False, methods=['get'])
    def default(self, request):
        """Get the user's default address"""
        address_type = request.query_params.get('type', 'both')
        try:
            address = Address.objects.get(user=request.user, is_default=True, address_type__in=[address_type, 'both'])
            serializer = self.get_serializer(address)
            return Response(serializer.data)
        except Address.DoesNotExist:
            return Response({"error": "No default address found"}, status=status.HTTP_404_NOT_FOUND)