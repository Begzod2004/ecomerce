from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from .models import User, Product, Cart, CartItem, Order, Address, ProductReview
from .serializers import UserSerializer, ProductSerializer, CartSerializer, CartItemSerializer, OrderSerializer, AddressSerializer, ProductReviewSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Retrieve or manage user profiles. Requires JWT authentication.",
        responses={
            200: UserSerializer(many=True),
            401: openapi.Response(description="Unauthorized"),
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['brand', 'size', 'color', 'price']

    @method_decorator(cache_page(60 * 15))
    @swagger_auto_schema(
        operation_description="List all products or filter by brand, size, color, or price. Publicly accessible.",
        responses={
            200: ProductSerializer(many=True),
            400: openapi.Response(description="Invalid filter parameters"),
        },
        manual_parameters=[
            openapi.Parameter('brand', openapi.IN_QUERY, description="Filter by brand (e.g., Nike)", type=openapi.TYPE_STRING),
            openapi.Parameter('size', openapi.IN_QUERY, description="Filter by size (e.g., M)", type=openapi.TYPE_STRING),
            openapi.Parameter('color', openapi.IN_QUERY, description="Filter by color (e.g., Pink)", type=openapi.TYPE_STRING),
            openapi.Parameter('price', openapi.IN_QUERY, description="Filter by price", type=openapi.TYPE_NUMBER),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

class ProductReviewViewSet(viewsets.ModelViewSet):
    queryset = ProductReview.objects.all()
    serializer_class = ProductReviewSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ProductReview.objects.filter(user=self.request.user)

    @swagger_auto_schema(
        operation_description="Manage product reviews. Only accessible to the review owner. Requires JWT authentication.",
        responses={
            200: ProductReviewSerializer(many=True),
            401: openapi.Response(description="Unauthorized"),
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

class CartViewSet(viewsets.ModelViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)

    @swagger_auto_schema(
        operation_description="Manage user carts. Only accessible to the cart owner. Requires JWT authentication.",
        responses={
            200: CartSerializer(many=True),
            401: openapi.Response(description="Unauthorized"),
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

class CartItemViewSet(viewsets.ModelViewSet):
    queryset = CartItem.objects.all()
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CartItem.objects.filter(cart__user=self.request.user)

    @swagger_auto_schema(
        operation_description="Manage items in a user's cart. Only accessible to the cart owner. Requires JWT authentication.",
        responses={
            200: CartItemSerializer(many=True),
            401: openapi.Response(description="Unauthorized"),
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    @swagger_auto_schema(
        operation_description="Manage user orders. Only accessible to the order owner. Requires JWT authentication.",
        responses={
            200: OrderSerializer(many=True),
            401: openapi.Response(description="Unauthorized"),
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

class AddressViewSet(viewsets.ModelViewSet):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)

    @swagger_auto_schema(
        operation_description="Manage user addresses. Only accessible to the address owner. Requires JWT authentication.",
        responses={
            200: AddressSerializer(many=True),
            401: openapi.Response(description="Unauthorized"),
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)