from rest_framework import generics, status, filters
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny, IsAuthenticatedOrReadOnly, SAFE_METHODS
from rest_framework.views import APIView
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q, Sum, Prefetch
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils.decorators import method_decorator
from django_filters import rest_framework as django_filters
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiExample, OpenApiTypes, OpenApiResponse, inline_serializer
from rest_framework import serializers
import asyncio
import logging
from rest_framework import exceptions
from .models import *
from .serializers import *
from .permissions import IsOwnerOrAdmin, IsCartOwner
from .pagination import DynamicPageSizePagination
from .filters import CategoryFilter, SubcategoryFilter, ProductFilter, UserFilter
from .utils.telegram import TelegramService
from rest_framework import viewsets
from .authentication import TelegramAuthentication
from django.http import Http404
from django.utils import timezone

logger = logging.getLogger(__name__)

class CategoryFilter(django_filters.FilterSet):
    gender = django_filters.NumberFilter(field_name='gender')
    search = django_filters.CharFilter(method='filter_search')

    class Meta:
        model = Category
        fields = ['gender']

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value) |
            Q(description__icontains=value)
        ).distinct()

class SubcategoryFilter(django_filters.FilterSet):
    gender = django_filters.NumberFilter(field_name='gender')
    category = django_filters.NumberFilter(field_name='category')
    search = django_filters.CharFilter(method='filter_search')

    class Meta:
        model = Subcategory
        fields = ['gender', 'category']

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value) |
            Q(description__icontains=value) |
            Q(category__name__icontains=value)
        ).distinct()

class ProductFilter(django_filters.FilterSet):
    gender = django_filters.NumberFilter(field_name='gender')
    category = django_filters.NumberFilter(field_name='subcategory__category')
    subcategory = django_filters.NumberFilter(field_name='subcategory')
    brand = django_filters.NumberFilter(field_name='brand')
    price_min = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    price_max = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    is_featured = django_filters.BooleanFilter(field_name='is_featured')
    is_active = django_filters.BooleanFilter(field_name='is_active')
    slug = django_filters.CharFilter(field_name='slug', lookup_expr='exact')
    search = django_filters.CharFilter(method='filter_search')
    has_discount = django_filters.BooleanFilter(method='filter_has_discount')

    class Meta:
        model = Product
        fields = ['gender', 'category', 'subcategory', 'brand', 'is_featured', 'is_active', 'slug']

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value) |
            Q(description__icontains=value) |
            Q(brand__name__icontains=value) |
            Q(subcategory__name__icontains=value) |
            Q(subcategory__category__name__icontains=value)
        ).distinct()

    def filter_has_discount(self, queryset, name, value):
        if value:
            return queryset.exclude(discount_price__isnull=True)
        return queryset

class TelegramAuthMixin:
    """
    Base mixin for Telegram authentication.
    Provides common functionality for all views that require telegram authentication.
    """
    def get_user_from_telegram_id(self):
        telegram_id = self.request.META.get('HTTP_X_TELEGRAM_ID')
        if not telegram_id:
            raise exceptions.AuthenticationFailed({
                'error': 'Authentication failed',
                'message': 'X-Telegram-ID header is required',
                'status': 401
            })

        try:
            return User.objects.get(telegram_id=telegram_id)
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed({
                'error': 'Authentication failed',
                'message': 'User not found with provided Telegram ID',
                'status': 401
            })

@extend_schema_view(
    get=extend_schema(
        summary="List users",
        description="Get a list of users with their Telegram information.",
        parameters=[
            OpenApiParameter(
                name="search",
                description="Search by username or telegram username",
                required=False,
                type=str
            ),
            OpenApiParameter(
                name="is_telegram_admin",
                description="Filter by admin status",
                required=False,
                type=bool
            ),
            OpenApiParameter(
                name="is_telegram_user",
                description="Filter by Telegram user status",
                required=False,
                type=bool
            ),
        ],
        tags=["User Management"]
    ),
    post=extend_schema(
        summary="Create user",
        description="Create a new user account.",
        tags=["User Management"]
    )
)
class UserListCreateView(generics.ListCreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [SearchFilter, DjangoFilterBackend]
    filterset_class = UserFilter
    search_fields = ['username', 'telegram_username']
    ordering = ['-date_joined']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return User.objects.none()
        return User.objects.all()

@extend_schema_view(
    get=extend_schema(
        summary="Get user details",
        description="Retrieve details of a specific user.",
        tags=["User Management"]
    ),
    put=extend_schema(
        summary="Update user",
        description="Update user's Telegram information.",
        tags=["User Management"]
    ),
    patch=extend_schema(
        summary="Partial update user",
        description="Update specific fields of user's Telegram information.",
        tags=["User Management"]
    ),
    delete=extend_schema(
        summary="Delete user",
        description="Delete a specific user account.",
        tags=["User Management"]
    )
)
class UserRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        queryset = User.objects.all()
        if not self.request.user.is_staff:
            queryset = queryset.filter(id=self.request.user.id)
        return queryset

    def perform_update(self, serializer):
        # Ensure is_telegram_admin can't be changed via API
        if 'is_telegram_admin' in serializer.validated_data:
            del serializer.validated_data['is_telegram_admin']
        serializer.save()

@extend_schema_view(
    get=extend_schema(
        summary="Get current user",
        description="Get details of the currently authenticated user.",
        tags=["User Management"]
    ),
    put=extend_schema(
        summary="Update user",
        description="Update user's Telegram information.",
        tags=["User Management"]
    ),
    patch=extend_schema(
        summary="Partial update user",
        description="Update specific fields of user's Telegram information.",
        tags=["User Management"]
    ),
    delete=extend_schema(
        summary="Delete user",
        description="Delete a specific user account.",
        tags=["User Management"]
    )
)
class UserMeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

@extend_schema_view(
    get=extend_schema(
        summary="List categories",
        description="Get a list of all product categories with filtering options.",
        parameters=[
            OpenApiParameter(
                name="gender",
                description="Filter by gender category ID",
                required=False,
                type=int
            ),
            OpenApiParameter(
                name="search",
                description="Search in name and description",
                required=False,
                type=str
            ),
        ],
        tags=["Category Management"]
    ),
    post=extend_schema(
        summary="Create category",
        description="Create a new product category. Admin only.",
        tags=["Category Management"]
    )
)
class CategoryListCreateView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = CategoryFilter
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_queryset(self):
        return Category.objects.all().select_related(
            'gender'
        ).prefetch_related(
            Prefetch(
                'subcategories',
                queryset=Subcategory.objects.annotate(
                    products_count=Count('products', filter=Q(products__is_active=True))
                )
            )
        ).annotate(
            products_count=Count('subcategories__products', filter=Q(subcategories__products__is_active=True))
        )

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [AllowAny()]
        return [IsAdminUser()]

@extend_schema_view(
    get=extend_schema(
        summary="Get category details",
        description="Retrieve details of a specific category using slug.",
        tags=["Category Management"]
    ),
    put=extend_schema(
        summary="Update category",
        description="Update all fields of a specific category. Admin only.",
        tags=["Category Management"]
    ),
    patch=extend_schema(
        summary="Partial update category",
        description="Update specific fields of a category. Admin only.",
        tags=["Category Management"]
    ),
    delete=extend_schema(
        summary="Delete category",
        description="Delete a specific category. Admin only.",
        tags=["Category Management"]
    )
)
class CategoryRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = 'slug'
    lookup_url_kwarg = 'slug'

    def get_queryset(self):
        return Category.objects.all().select_related(
            'gender'
        ).prefetch_related(
            Prefetch(
                'subcategories',
                queryset=Subcategory.objects.annotate(
                    products_count=Count('products', filter=Q(products__is_active=True))
                )
            )
        ).annotate(
            products_count=Count('subcategories__products', filter=Q(subcategories__products__is_active=True))
        )

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [AllowAny()]
        return [IsAdminUser()]

@extend_schema_view(
    get=extend_schema(
        summary="List subcategories",
        description="Get a list of all product subcategories with filtering options.",
        parameters=[
            OpenApiParameter(
                name="gender",
                description="Filter by gender category ID",
                required=False,
                type=int
            ),
            OpenApiParameter(
                name="category",
                description="Filter by category ID",
                required=False,
                type=int
            ),
            OpenApiParameter(
                name="search",
                description="Search in name and description",
                required=False,
                type=str
            ),
        ],
        tags=["Subcategory Management"]
    ),
    post=extend_schema(
        summary="Create subcategory",
        description="Create a new product subcategory. Admin only.",
        tags=["Subcategory Management"]
    )
)
class SubcategoryListCreateView(generics.ListCreateAPIView):
    queryset = Subcategory.objects.all()
    serializer_class = SubcategorySerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = SubcategoryFilter
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_queryset(self):
        return super().get_queryset()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

@extend_schema_view(
    get=extend_schema(
        summary="Get subcategory details",
        description="Retrieve details of a specific subcategory.",
        tags=["Subcategory Management"]
    ),
    put=extend_schema(
        summary="Update subcategory",
        description="Update all fields of a specific subcategory. Admin only.",
        tags=["Subcategory Management"]
    ),
    patch=extend_schema(
        summary="Partial update subcategory",
        description="Update specific fields of a subcategory. Admin only.",
        tags=["Subcategory Management"]
    ),
    delete=extend_schema(
        summary="Delete subcategory",
        description="Delete a specific subcategory. Admin only.",
        tags=["Subcategory Management"]
    )
)
class SubcategoryRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SubcategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = 'slug'
    lookup_url_kwarg = 'slug'

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):  # for swagger schema generation
            return Subcategory.objects.none()
            
        return Subcategory.objects.annotate(
            products_count=Count('products')
        ).select_related('category', 'gender')

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [AllowAny()]
        return [IsAdminUser()]

@extend_schema_view(
    get=extend_schema(
        summary="List products",
        description="Get a list of all products with advanced filtering options.",
        parameters=[
            OpenApiParameter(
                name="gender",
                description="Filter by gender category ID",
                required=False,
                type=int
            ),
            OpenApiParameter(
                name="category",
                description="Filter by category ID",
                required=False,
                type=int
            ),
            OpenApiParameter(
                name="subcategory",
                description="Filter by subcategory ID",
                required=False,
                type=int
            ),
            OpenApiParameter(
                name="brand",
                description="Filter by brand ID",
                required=False,
                type=int
            ),
            OpenApiParameter(
                name="price_min",
                description="Minimum price",
                required=False,
                type=float
            ),
            OpenApiParameter(
                name="price_max",
                description="Maximum price",
                required=False,
                type=float
            ),
            OpenApiParameter(
                name="has_discount",
                description="Filter products with discount",
                required=False,
                type=bool
            ),
            OpenApiParameter(
                name="size",
                description="Filter by size name (e.g. S, M, L, XL)",
                required=False,
                type=str
            ),
            OpenApiParameter(
                name="size_eu",
                description="Filter by EU size",
                required=False,
                type=int
            ),
            OpenApiParameter(
                name="size_us",
                description="Filter by US size",
                required=False,
                type=int
            ),
            OpenApiParameter(
                name="size_uk",
                description="Filter by UK size",
                required=False,
                type=int
            ),
            OpenApiParameter(
                name="is_featured",
                description="Filter featured products",
                required=False,
                type=bool
            ),
            OpenApiParameter(
                name="is_active",
                description="Filter active/inactive products",
                required=False,
                type=bool
            ),
            OpenApiParameter(
                name="in_stock",
                description="Filter products by stock availability",
                required=False,
                type=bool
            ),
            OpenApiParameter(
                name="delivery_min",
                description="Minimum delivery days",
                required=False,
                type=int
            ),
            OpenApiParameter(
                name="delivery_max",
                description="Maximum delivery days",
                required=False,
                type=int
            ),
            OpenApiParameter(
                name="search",
                description="Search in name, description, brand, category and subcategory",
                required=False,
                type=str
            ),
            OpenApiParameter(
                name="ordering",
                description="Order by field (prefix with '-' for descending)",
                required=False,
                type=str,
                examples=[
                    OpenApiExample(
                        'Price ascending',
                        value='price'
                    ),
                    OpenApiExample(
                        'Price descending',
                        value='-price'
                    ),
                    OpenApiExample(
                        'Newest first',
                        value='-created_at'
                    ),
                    OpenApiExample(
                        'Name A-Z',
                        value='name'
                    ),
                ]
            ),
        ],
        tags=["Product Management"]
    ),
    post=extend_schema(
        summary="Create product",
        description="Create a new product. Admin only.",
        tags=["Product Management"]
    )
)
class ProductListCreateView(generics.ListCreateAPIView):
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = ProductFilter
    ordering_fields = ['price', 'created_at', 'name']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = Product.objects.all()
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_active=True)
        
        return queryset.select_related(
            'subcategory',
            'subcategory__category',
            'subcategory__gender',
            'brand',
            'gender',
            'season'
        ).prefetch_related(
            'materials',
            'shipping_methods',
            Prefetch(
                'variants',
                queryset=ProductVariant.objects.select_related('color', 'size')
            ),
            'images'
        ).annotate(
            variants_count=Count('variants', distinct=True),
            in_stock=Sum('variants__stock')
        )

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [AllowAny()]
        return [IsAdminUser()]

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

@extend_schema_view(
    get=extend_schema(
        summary="Get product details",
        description="Retrieve details of a specific product using ID or slug.",
        tags=["Product Management"]
    ),
    put=extend_schema(
        summary="Update product",
        description="Update all fields of a specific product. Admin only.",
        tags=["Product Management"]
    ),
    patch=extend_schema(
        summary="Partial update product",
        description="Update specific fields of a product. Admin only.",
        tags=["Product Management"]
    ),
    delete=extend_schema(
        summary="Delete product",
        description="Delete a specific product. Admin only.",
        tags=["Product Management"]
    )
)
class ProductRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'
    lookup_url_kwarg = 'slug'

    def get_queryset(self):
        return Product.objects.select_related(
            'subcategory', 
            'subcategory__category', 
            'subcategory__gender',
            'brand', 
            'gender', 
            'season'
        ).prefetch_related(
            'materials',
            'shipping_methods',
            Prefetch(
                'variants',
                queryset=ProductVariant.objects.select_related('color', 'size')
            ),
            'images',
            'likes'
        )

    @action(detail=True, methods=['post'])
    def like(self, request, slug=None):
        product = self.get_object()
        user = request.user
        
        if product.likes.filter(id=user.id).exists():
            product.likes.remove(user)
            return Response({'status': 'unliked'})
        else:
            product.likes.add(user)
            return Response({'status': 'liked'})

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [IsAdminUser()]
        return [AllowAny()]

@extend_schema(
    summary="Get similar products",
    description="Get a list of similar products based on category and subcategory.",
    tags=["Product Management"]
)
class SimilarProductsView(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]
    pagination_class = DynamicPageSizePagination

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Product.objects.none()
            
        product_id = self.kwargs.get('pk')
        try:
            product = Product.objects.get(pk=product_id)
            return Product.objects.filter(
                Q(subcategory=product.subcategory) |
                Q(category=product.subcategory.category)
            ).exclude(id=product.id).distinct()
        except Product.DoesNotExist:
            return Product.objects.none()

@extend_schema_view(
    get=extend_schema(
        summary="List user's wishlists",
        description="Get all wishlists belonging to the authenticated user (X-Telegram-ID).",
        tags=["Wishlist Management"]
    ),
    post=extend_schema(
        summary="Create new wishlist",
        description="Create a new wishlist for the authenticated user (X-Telegram-ID).",
        tags=["Wishlist Management"]
    )
)
class WishlistListCreateView(TelegramAuthMixin, generics.ListCreateAPIView):
    serializer_class = WishlistSerializer
    permission_classes = [AllowAny]
    pagination_class = DynamicPageSizePagination

    def get_queryset(self):
        user = self.get_user_from_telegram_id()
        return Wishlist.objects.filter(user=user).prefetch_related(
            'products'
        ).order_by('-created_at')

    def perform_create(self, serializer):
        user = self.get_user_from_telegram_id()
        serializer.save(user=user)

@extend_schema_view(
    get=extend_schema(
        summary="Get wishlist details",
        description="Retrieve details of a specific wishlist.",
        tags=["Wishlist Management"]
    ),
    put=extend_schema(
        summary="Update wishlist",
        description="Update all fields of a specific wishlist.",
        tags=["Wishlist Management"]
    ),
    patch=extend_schema(
        summary="Partial update wishlist",
        description="Update specific fields of a wishlist.",
        tags=["Wishlist Management"]
    ),
    delete=extend_schema(
        summary="Delete wishlist",
        description="Delete a specific wishlist.",
        tags=["Wishlist Management"]
    )
)
class WishlistRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = WishlistSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user)

@extend_schema(
    summary="Add to wishlist",
    description="Add a product to user's wishlist (X-Telegram-ID).",
    request=AddToWishlistRequestSerializer,
    responses={
        200: WishlistResponseSerializer,
        400: OpenApiResponse(description="Invalid request data"),
        401: OpenApiResponse(
            description="Authentication failed",
            response=inline_serializer(
                name='AuthError',
                fields={
                    'error': serializers.CharField(),
                    'message': serializers.CharField(),
                    'status': serializers.IntegerField(),
                }
            )
        ),
        404: OpenApiResponse(description="Product not found")
    },
    tags=["Wishlist Management"]
)
class AddToWishlistView(TelegramAuthMixin, generics.GenericAPIView):
    serializer_class = WishlistSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            user = self.get_user_from_telegram_id()
            serializer = AddToWishlistRequestSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            wishlist, created = Wishlist.objects.get_or_create(user=user)
            try:
                product = Product.objects.get(id=serializer.validated_data['product_id'])
            except Product.DoesNotExist:
                return Response({
                    'error': 'Product not found',
                    'message': f"Product with ID {serializer.validated_data['product_id']} does not exist"
                }, status=status.HTTP_404_NOT_FOUND)
            
            if product in wishlist.products.all():
                wishlist.remove_product(product)
                message = "Product removed from wishlist"
                is_liked = False
            else:
                wishlist.add_product(product)
                message = "Product added to wishlist"
                is_liked = True

            # Ensure all products in wishlist are liked
            for wishlist_product in wishlist.products.all():
                if not wishlist_product.likes.filter(id=user.id).exists():
                    wishlist_product.likes.add(user)

            return Response({
                'message': message,
                'wishlist': WishlistSerializer(wishlist).data,
                'is_liked': is_liked
            })
        except Exception as e:
            return Response({
                'error': 'Server error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@extend_schema(
    summary="Remove from wishlist",
    description="Remove a product from user's wishlist.",
    request=OpenApiTypes.OBJECT,
    examples=[
        OpenApiExample(
            "Example Request",
            value={"product_id": 1}
        )
    ],
    tags=["Wishlist Management"]
)
class RemoveFromWishlistView(generics.GenericAPIView):
    serializer_class = WishlistSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=AddToWishlistRequestSerializer,
        responses={200: WishlistResponseSerializer}
    )
    def post(self, request):
        serializer = AddToWishlistRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            product = Product.objects.get(id=serializer.validated_data['product_id'])
            wishlist = Wishlist.objects.get(user=request.user)
            wishlist.products.remove(product)
            
            response_serializer = WishlistResponseSerializer({
                'message': 'Product removed from wishlist',
                'wishlist': wishlist
            })
            return Response(response_serializer.data)
        except (Product.DoesNotExist, Wishlist.DoesNotExist):
            return Response({'error': 'Product or wishlist not found'}, status=404)

@extend_schema_view(
    get=extend_schema(
        summary="Get cart item details",
        description="Get details of a specific item in user's cart (X-Telegram-ID).",
        tags=["Cart Management"]
    ),
    put=extend_schema(
        summary="Update cart item",
        description="Update quantity or other fields of a cart item (X-Telegram-ID).",
        tags=["Cart Management"]
    ),
    patch=extend_schema(
        summary="Partial update cart item",
        description="Partially update a cart item (X-Telegram-ID).",
        tags=["Cart Management"]
    ),
    delete=extend_schema(
        summary="Remove item from cart",
        description="Remove an item from user's cart (X-Telegram-ID).",
        tags=["Cart Management"]
    )
)
class CartItemRetrieveUpdateDestroyView(TelegramAuthMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CartItemSerializer

    def get_queryset(self):
        return CartItem.objects.filter(cart__user=self.request.user)

    def get_object(self):
        """
        Get cart item and verify it exists and is not deleted
        """
        try:
            obj = super().get_object()
            if obj.is_deleted:
                raise NotFound({
                    'error': 'Cart item not found',
                    'message': 'The requested cart item has been deleted'
                })
            return obj
        except Http404:
            raise NotFound({
                'error': 'Cart item not found',
                'message': 'The requested cart item does not exist or you do not have permission to access it'
            })

    def destroy(self, request, *args, **kwargs):
        """
        Soft delete the cart item and handle cart deactivation
        """
        try:
            instance = self.get_object()
            
            # Perform soft delete
            instance.delete(hard_delete=False)
            
            return Response(status=status.HTTP_204_NO_CONTENT)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve cart item if it exists and is not deleted
        """
        try:
            instance = self.get_object()
            if instance.is_deleted:
                raise NotFound({
                    'error': 'Cart item not found',
                    'message': 'The requested cart item has been deleted'
                })
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        except NotFound as e:
            return Response(e.detail, status=status.HTTP_404_NOT_FOUND)

@extend_schema(
    summary="Get active cart",
    description="Get user's active shopping cart using X-Telegram-ID header.",
    tags=["Cart Management"],
    responses={
        200: CartSerializer,
        401: OpenApiResponse(
            description="Authentication failed",
            response=inline_serializer(
                name='AuthError',
                fields={
                    'error': serializers.CharField(),
                    'message': serializers.CharField(),
                    'status': serializers.IntegerField(),
                }
            )
        )
    }
)
class MyCartView(TelegramAuthMixin, APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        user = self.get_user_from_telegram_id()
        cart = Cart.objects.filter(user=user, is_active=True).prefetch_related(
            Prefetch(
                'items',
                queryset=CartItem.objects.select_related('product', 'variant')
            )
        ).first()
        
        if not cart:
            # Create a new cart if none exists
            cart = Cart.objects.create(user=user, is_active=True)
        
        serializer = CartSerializer(cart, context={'request': request})
        return Response(serializer.data)

@extend_schema_view(
    get=extend_schema(
        summary="List all carts",
        description="Get a list of all carts. Admin users can see all carts, regular users see only their own carts.",
        tags=["Cart Management"]
    ),
    post=extend_schema(
        summary="Create new cart",
        description="Create a new cart for the authenticated user.",
        tags=["Cart Management"]
    )
)
class CartListCreateView(TelegramAuthMixin, generics.ListCreateAPIView):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = DynamicPageSizePagination

    def get_queryset(self):
        user = self.get_user_from_telegram_id()
        if user.is_staff or user.is_telegram_admin:
            return Cart.objects.all().prefetch_related(
                Prefetch(
                    'items',
                    queryset=CartItem.objects.select_related('product')
                )
            ).order_by('-created_at')
        return Cart.objects.filter(user=user).prefetch_related(
            Prefetch(
                'items',
                queryset=CartItem.objects.select_related('product')
            )
        ).order_by('-created_at')

    def perform_create(self, serializer):
        user = self.get_user_from_telegram_id()
        # Deactivate all existing carts for the user
        Cart.objects.filter(user=user, is_active=True).update(is_active=False)
        # Create new active cart
        serializer.save(user=user, is_active=True)

@extend_schema_view(
    get=extend_schema(
        summary="List cart items",
        description="Get all items in user's cart (X-Telegram-ID).",
        tags=["Cart Management"]
    ),
    post=extend_schema(
        summary="Add item to cart",
        description="Add a new item to user's cart (X-Telegram-ID).",
        tags=["Cart Management"]
    )
)
class CartItemListCreateView(TelegramAuthMixin, generics.ListCreateAPIView):
    serializer_class = CartItemSerializer
    permission_classes = [AllowAny]
    pagination_class = DynamicPageSizePagination

    def get_queryset(self):
        user = self.get_user_from_telegram_id()
        return CartItem.objects.filter(
            cart__user=user
        ).select_related(
            'product',
            'cart',
            'variant',
            'variant__color',
            'variant__size'
        ).order_by('-created_at')

    def perform_create(self, serializer):
        user = self.get_user_from_telegram_id()
        cart, _ = Cart.objects.get_or_create(user=user)
        serializer.save(cart=cart)

@extend_schema(
    summary="Add to cart",
    description="Add a product variant to user's cart (X-Telegram-ID).",
    request=inline_serializer(
        name='AddToCartRequest',
        fields={
            'product_id': serializers.IntegerField(),
            'variant_id': serializers.IntegerField(required=False),
            'quantity': serializers.IntegerField(default=1, min_value=1, max_value=10)
        }
    ),
    responses={
        201: CartResponseSerializer,
        400: OpenApiResponse(description="Invalid request data or insufficient stock"),
        401: OpenApiResponse(description="Authentication failed"),
        404: OpenApiResponse(description="Product or variant not found"),
        500: OpenApiResponse(description="Server error")
    },
    tags=["Cart Management"]
)
class AddToCartView(TelegramAuthMixin, APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # Get user from request context
            user = self.get_user_from_telegram_id()
            if not user:
                return Response(
                    {'error': 'Authentication failed', 'message': 'Invalid Telegram ID', 'status': 401},
                    status=status.HTTP_401_UNAUTHORIZED
                )
                
            # Get active cart for user
            cart = Cart.objects.filter(user=user, is_active=True).first()
            if not cart:
                # Create new cart if not exists
                cart = Cart.objects.create(user=user, is_active=True)
                
            # Validate request data
            serializer = AddToCartRequestSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
            # Get product from request
            product_id = serializer.validated_data.get('product_id')
            try:
                product = Product.objects.get(id=product_id, is_active=True)
            except Product.DoesNotExist:
                return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
                
            # Get variant if provided
            variant = None
            variant_id = serializer.validated_data.get('variant_id')
            if variant_id:
                try:
                    variant = ProductVariant.objects.get(id=variant_id, product=product)
                except ProductVariant.DoesNotExist:
                    return Response({'error': 'Variant not found'}, status=status.HTTP_404_NOT_FOUND)
            
            # Check if item already exists in cart
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                variant=variant,
                defaults={'quantity': serializer.validated_data.get('quantity', 1)}
            )
            
            if not created:
                new_quantity = cart_item.quantity + serializer.validated_data.get('quantity', 1)
                if variant and new_quantity > variant.stock:
                    return Response({
                        'error': 'Insufficient stock',
                        'message': f'Only {variant.stock} items available in stock'
                    }, status=status.HTTP_400_BAD_REQUEST)
                cart_item.quantity = new_quantity
                cart_item.save()

            serializer = CartItemSerializer(cart_item, context={'request': request})
            return Response({
                'message': 'Product added to cart successfully',
                'cart_item': serializer.data
            }, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(
    summary="Remove from cart",
    description="Remove a product from the cart.",
    request=AddToCartRequestSerializer,
    responses={
        200: OpenApiResponse(
            response=CartResponseSerializer,
            description="Product removed from cart successfully"
        ),
        404: OpenApiResponse(
            description="Product or cart not found"
        )
    },
    tags=["Cart Management"]
)
class RemoveFromCartView(generics.GenericAPIView):
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AddToCartRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            cart = Cart.objects.get(user=request.user)
            cart_item = CartItem.objects.get(
                cart=cart,
                product_id=serializer.validated_data['product_id']
            )
            cart_item.delete()
            
            response_serializer = CartResponseSerializer({
                'message': 'Product removed from cart',
                'cart_item': None
            })
            return Response(response_serializer.data)
        except (Cart.DoesNotExist, CartItem.DoesNotExist):
            return Response({'error': 'Product not found in cart'}, status=404)

@extend_schema_view(
    get=extend_schema(
        summary="List orders",
        description="Get a list of orders. Admin users can see all orders, regular users see only their own orders.",
        tags=["Order Management"]
    ),
    post=extend_schema(
        summary="Create order",
        description="Create a new order from cart items.",
        request=inline_serializer(
            name='CreateOrderRequest',
            fields={
                'cart_id': serializers.IntegerField(help_text="ID of the cart to create order from"),
                'shipping_method_id': serializers.IntegerField(
                    help_text="ID of the shipping method",
                    required=False
                ),
                'pickup_branch_id': serializers.IntegerField(
                    help_text="ID of the pickup branch (required)",
                    required=True
                ),
                'customer_name': serializers.CharField(help_text="Customer's full name"),
                'phone_number': serializers.CharField(help_text="Customer's phone number"),
                'order_note': serializers.CharField(
                    help_text="Optional note for the order",
                    required=False,
                    allow_blank=True
                ),
                'payment_method': serializers.ChoiceField(
                    choices=Order.PAYMENT_METHOD_CHOICES,
                    help_text="Payment method for the order"
                )
            }
        ),
        examples=[
            OpenApiExample(
                'Branch Pickup Example',
                value={
                    'cart_id': 1,
                    'shipping_method_id': 1,
                    'pickup_branch_id': 1,
                    'customer_name': 'John Doe',
                    'phone_number': '+998901234567',
                    'payment_method': 'cash_on_pickup'
                }
            )
        ],
        responses={
            201: OrderSerializer,
            400: inline_serializer(
                name='OrderError',
                fields={
                    'error': serializers.CharField(),
                    'message': serializers.CharField()
                }
            )
        },
        tags=["Order Management"]
    )
)
class OrderListCreateView(generics.ListCreateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'payment_method', 'delivery_type']
    search_fields = ['customer_name', 'phone_number', 'tracking_number']
    ordering_fields = ['created_at', 'total_amount', 'status']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save()

@extend_schema_view(
    get=extend_schema(
        summary="Get order details",
        description="Get detailed information about a specific order.",
        tags=["Order Management"]
    ),
    patch=extend_schema(
        summary="Update order",
        description="Update an existing order. Only certain fields can be updated.",
        request=inline_serializer(
            name='UpdateOrderRequest',
            fields={
                'status': serializers.ChoiceField(
                    choices=Order.STATUS_CHOICES,
                    help_text="New status for the order",
                    required=False
                ),
                'tracking_number': serializers.CharField(
                    help_text="Tracking number for shipped orders",
                    required=False,
                    allow_blank=True
                ),
                'order_note': serializers.CharField(
                    help_text="Additional note for the order",
                    required=False,
                    allow_blank=True
                )
            }
        ),
        responses={
            200: OrderSerializer,
            400: inline_serializer(
                name='OrderError',
                fields={
                    'error': serializers.CharField(),
                    'message': serializers.CharField()
                }
            )
        },
        tags=["Order Management"]
    ),
    delete=extend_schema(
        summary="Cancel order",
        description="Cancel an order. Only pending orders can be canceled.",
        responses={
            204: None,
            400: inline_serializer(
                name='OrderError',
                fields={
                    'error': serializers.CharField(),
                    'message': serializers.CharField()
                }
            )
        },
        tags=["Order Management"]
    )
)
class OrderRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(user=user)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Only allow updating specific fields
        allowed_fields = ['status', 'tracking_number', 'order_note']
        data = {k: v for k, v in request.data.items() if k in allowed_fields}
        
        serializer = self.get_serializer(instance, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Only allow canceling pending orders
        if instance.status != 'pending':
            return Response(
                {'error': 'Cannot cancel order', 'message': 'Only pending orders can be canceled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        instance.status = 'canceled'
        instance.save()
        
        return Response(status=status.HTTP_204_NO_CONTENT)

@extend_schema(
    summary="Cancel order",
    description="Cancel an existing order. Only pending orders can be canceled.",
    request=inline_serializer(
        name='CancelOrderRequest',
        fields={
            'reason': serializers.CharField(
                help_text="Reason for cancellation",
                required=False,
                allow_blank=True
            )
        }
    ),
    responses={
        200: OrderSerializer,
        400: OpenApiResponse(description="Order cannot be canceled"),
        404: OpenApiResponse(description="Order not found")
    },
    tags=["Order Management"]
)
class CancelOrderView(generics.GenericAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [TelegramAuthentication]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(user=user)

    def post(self, request, pk):
        try:
            order = self.get_queryset().get(pk=pk)
        except Order.DoesNotExist:
            return Response(
                {"error": "Order not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        if order.status != 'pending':
            return Response(
                {"error": "Only pending orders can be canceled"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update order status
        order.status = 'canceled'
        order.order_note = request.data.get('reason', '')
        order.save()

        # Send notification
        try:
            TelegramService.notify_order_status(order)
        except Exception as e:
            logger.error(f"Failed to send order cancellation notification: {str(e)}")

        serializer = self.get_serializer(order)
        return Response(serializer.data)

@extend_schema_view(
    get=extend_schema(
        summary="List addresses",
        description="Get a list of user's addresses.",
        tags=["Address Management"]
    ),
    post=extend_schema(
        summary="Create address",
        description="Create a new address for the user.",
        tags=["Address Management"]
    )
)
class AddressListCreateView(generics.ListCreateAPIView):
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = DynamicPageSizePagination

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Address.objects.none()
        return Address.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

@extend_schema_view(
    get=extend_schema(
        summary="Get address details",
        description="Retrieve details of a specific address.",
        tags=["Address Management"]
    ),
    put=extend_schema(
        summary="Update address",
        description="Update all fields of a specific address.",
        tags=["Address Management"]
    ),
    patch=extend_schema(
        summary="Partial update address",
        description="Update specific fields of an address.",
        tags=["Address Management"]
    ),
    delete=extend_schema(
        summary="Delete address",
        description="Delete a specific address.",
        tags=["Address Management"]
    )
)
class AddressRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AddressSerializer
    permission_classes = [IsOwnerOrAdmin]

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)

    def perform_update(self, serializer):
        if serializer.validated_data.get('is_default', False):
            # Set all other addresses as non-default
            Address.objects.filter(user=self.request.user).update(is_default=False)
        serializer.save()

@extend_schema(
    summary="Get default address",
    description="Get the user's default address.",
    tags=["Address Management"]
)
class DefaultAddressView(generics.RetrieveAPIView):
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return get_object_or_404(
            Address.objects.filter(user=self.request.user),
            is_default=True
        )

@extend_schema_view(
    get=extend_schema(
        summary="List brands",
        description="Get a list of all brands with filtering options.",
        parameters=[
            OpenApiParameter(
                name="search",
                description="Search in name and description",
                required=False,
                type=str
            ),
            OpenApiParameter(
                name="page",
                description="Page number",
                required=False,
                type=int
            ),
            OpenApiParameter(
                name="page_size",
                description="Number of items per page (default: 10, max: 100)",
                required=False,
                type=int
            ),
            OpenApiParameter(
                name="ordering",
                description="Order by field (prefix with '-' for descending)",
                required=False,
                type=str,
                examples=[
                    OpenApiExample(
                        'Name ascending',
                        value='name'
                    ),
                    OpenApiExample(
                        'Name descending',
                        value='-name'
                    ),
                    OpenApiExample(
                        'Created date',
                        value='created_at'
                    ),
                    OpenApiExample(
                        'Products count',
                        value='products_count'
                    ),
                ]
            ),
        ],
        tags=["Brand Management"]
    ),
    post=extend_schema(
        summary="Create brand",
        description="Create a new brand. Admin only.",
        tags=["Brand Management"]
    )
)
class BrandListCreateView(generics.ListCreateAPIView):
    serializer_class = BrandSerializer
    pagination_class = DynamicPageSizePagination
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [OrderingFilter]
    ordering_fields = ['name', 'created_at', 'products_count']
    ordering = ['name']  # Default ordering

    def get_queryset(self):
        queryset = Brand.objects.annotate(
            products_count=Count('products')
        ).prefetch_related(
            Prefetch('products', queryset=Product.objects.filter(is_active=True))
        )
        
        # Handle search parameter
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )
        
        return queryset

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [AllowAny()]
        return [IsAdminUser()]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="page_size",
                type=int,
                location=OpenApiParameter.QUERY,
                description="Number of results to return per page (default: 10, max: 100)",
                required=False
            ),
            OpenApiParameter(
                name="search",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Search brands by name or description",
                required=False
            ),
            OpenApiParameter(
                name="ordering",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Order by field (name, created_at, products_count). Use '-' for descending order.",
                required=False
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        try:
            return super().list(request, *args, **kwargs)
        except NotFound:
            # Return empty page instead of 404 when page number exceeds available pages
            return Response({
                'count': 0,
                'next': None,
                'previous': None,
                'results': []
            })

@extend_schema_view(
    get=extend_schema(
        summary="Get brand details",
        description="Retrieve details of a specific brand using slug.",
        tags=["Brand Management"]
    ),
    put=extend_schema(
        summary="Update brand",
        description="Update all fields of a specific brand. Admin only.",
        tags=["Brand Management"]
    ),
    patch=extend_schema(
        summary="Partial update brand",
        description="Update specific fields of a brand. Admin only.",
        tags=["Brand Management"]
    ),
    delete=extend_schema(
        summary="Delete brand",
        description="Delete a specific brand. Admin only.",
        tags=["Brand Management"]
    )
)
class BrandRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = BrandSerializer
    lookup_field = 'slug'
    
    def get_queryset(self):
        return Brand.objects.annotate(
            products_count=Count('products')
        )

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [AllowAny()]
        return [IsAdminUser()]

@extend_schema_view(
    get=extend_schema(
        summary="List colors",
        description="Get a list of all colors.",
        tags=["Color Management"]
    ),
    post=extend_schema(
        summary="Create color",
        description="Create a new color. Admin only.",
        tags=["Color Management"]
    )
)
class ColorListCreateView(generics.ListCreateAPIView):
    queryset = Color.objects.all()
    serializer_class = ColorSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'hex_code']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [AllowAny()]
        return [IsAdminUser()]

@extend_schema_view(
    get=extend_schema(
        summary="Get color details",
        description="Retrieve details of a specific color.",
        tags=["Color Management"]
    ),
    put=extend_schema(
        summary="Update color",
        description="Update all fields of a specific color. Admin only.",
        tags=["Color Management"]
    ),
    patch=extend_schema(
        summary="Partial update color",
        description="Update specific fields of a color. Admin only.",
        tags=["Color Management"]
    ),
    delete=extend_schema(
        summary="Delete a specific color. Admin only.",
        description="Delete a specific color. Admin only.",
        tags=["Color Management"]
    )
)
class ColorRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Color.objects.all()
    serializer_class = ColorSerializer

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [AllowAny()]
        return [IsAdminUser()]

@extend_schema_view(
    get=extend_schema(
        summary="List sizes",
        description="Get a list of all sizes.",
        tags=["Size Management"]
    ),
    post=extend_schema(
        summary="Create size",
        description="Create a new size. Admin only.",
        tags=["Size Management"]
    )
)
class SizeListCreateView(generics.ListCreateAPIView):
    queryset = Size.objects.all()
    serializer_class = SizeSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'size_eu', 'size_us', 'size_uk', 'created_at']
    ordering = ['name']

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [AllowAny()]
        return [IsAdminUser()]

@extend_schema_view(
    get=extend_schema(
        summary="Get size details",
        description="Retrieve details of a specific size.",
        tags=["Size Management"]
    ),
    put=extend_schema(
        summary="Update size",
        description="Update all fields of a specific size. Admin only.",
        tags=["Size Management"]
    ),
    patch=extend_schema(
        summary="Partial update size",
        description="Update specific fields of a size. Admin only.",
        tags=["Size Management"]
    ),
    delete=extend_schema(
        summary="Delete a specific size. Admin only.",
        description="Delete a specific size. Admin only.",
        tags=["Size Management"]
    )
)
class SizeRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Size.objects.all()
    serializer_class = SizeSerializer

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [AllowAny()]
        return [IsAdminUser()]

@extend_schema_view(
    get=extend_schema(
        summary="List materials",
        description="Get a list of all materials.",
        tags=["Material Management"]
    ),
    post=extend_schema(
        summary="Create material",
        description="Create a new material. Admin only.",
        tags=["Material Management"]
    )
)
class MaterialListCreateView(generics.ListCreateAPIView):
    queryset = Material.objects.all()
    serializer_class = MaterialSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [AllowAny()]
        return [IsAdminUser()]

@extend_schema_view(
    get=extend_schema(
        summary="Get material details",
        description="Retrieve details of a specific material.",
        tags=["Material Management"]
    ),
    put=extend_schema(
        summary="Update material",
        description="Update all fields of a specific material. Admin only.",
        tags=["Material Management"]
    ),
    patch=extend_schema(
        summary="Partial update material",
        description="Update specific fields of a material. Admin only.",
        tags=["Material Management"]
    ),
    delete=extend_schema(
        summary="Delete a specific material. Admin only.",
        description="Delete a specific material. Admin only.",
        tags=["Material Management"]
    )
)
class MaterialRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Material.objects.all()
    serializer_class = MaterialSerializer

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [AllowAny()]
        return [IsAdminUser()]

@extend_schema_view(
    get=extend_schema(
        summary="List seasons",
        description="Get a list of all seasons.",
        tags=["Season Management"]
    ),
    post=extend_schema(
        summary="Create season",
        description="Create a new season. Admin only.",
        tags=["Season Management"]
    )
)
class SeasonListCreateView(generics.ListCreateAPIView):
    queryset = Season.objects.all()
    serializer_class = SeasonSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [AllowAny()]
        return [IsAdminUser()]

@extend_schema_view(
    get=extend_schema(
        summary="Get season details",
        description="Retrieve details of a specific season.",
        tags=["Season Management"]
    ),
    put=extend_schema(
        summary="Update season",
        description="Update all fields of a specific season. Admin only.",
        tags=["Season Management"]
    ),
    patch=extend_schema(
        summary="Partial update season",
        description="Update specific fields of a season. Admin only.",
        tags=["Season Management"]
    ),
    delete=extend_schema(
        summary="Delete a specific season. Admin only.",
        description="Delete a specific season. Admin only.",
        tags=["Season Management"]
    )
)
class SeasonRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Season.objects.all()
    serializer_class = SeasonSerializer

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [AllowAny()]
        return [IsAdminUser()]

@extend_schema_view(
    get=extend_schema(
        summary="List shipping methods",
        description="Get a list of all shipping methods.",
        tags=["Shipping Management"]
    ),
    post=extend_schema(
        summary="Create shipping method",
        description="Create a new shipping method. Admin only.",
        tags=["Shipping Management"]
    )
)
class ShippingMethodListCreateView(generics.ListCreateAPIView):
    queryset = ShippingMethod.objects.all()
    serializer_class = ShippingMethodSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'price', 'min_days', 'max_days', 'created_at']
    ordering = ['name']

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [AllowAny()]
        return [IsAdminUser()]

@extend_schema_view(
    get=extend_schema(
        summary="Get shipping method details",
        description="Retrieve details of a specific shipping method.",
        tags=["Shipping Management"]
    ),
    put=extend_schema(
        summary="Update shipping method",
        description="Update all fields of a specific shipping method. Admin only.",
        tags=["Shipping Management"]
    ),
    patch=extend_schema(
        summary="Partial update shipping method",
        description="Update specific fields of a shipping method. Admin only.",
        tags=["Shipping Management"]
    ),
    delete=extend_schema(
        summary="Delete shipping method",
        description="Delete a specific shipping method. Admin only.",
        tags=["Shipping Management"]
    )
)
class ShippingMethodRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ShippingMethod.objects.all()
    serializer_class = ShippingMethodSerializer

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [AllowAny()]
        return [IsAdminUser()]

@extend_schema(
    summary="Update order status",
    description="Update the status of an order. Admin only.",
    request=inline_serializer(
        name='OrderStatusUpdate',
        fields={
            'status': serializers.ChoiceField(choices=Order.STATUS_CHOICES)
        }
    ),
    responses={
        200: OrderResponseSerializer,
        400: OpenApiResponse(description="Invalid status"),
        404: OpenApiResponse(description="Order not found")
    },
    tags=["Order Management"]
)
class UpdateOrderStatusView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer

    def post(self, request, pk):
        try:
            order = Order.objects.get(pk=pk)
            
            # Check permissions
            if not (request.user.is_staff or request.user.is_telegram_admin):
                return Response({"error": "Permission denied"}, status=403)
            
            status = request.data.get('status')
            if status not in dict(Order.STATUS_CHOICES):
                return Response({'error': 'Invalid status'}, status=400)
            
            order.status = status
            order.save()
            
            # Send notification
            if order.user.telegram_id:
                try:
                    TelegramService.notify_order_status(order)
                except Exception as e:
                    logger.error(f"Failed to send order status update notification: {e}")
            
            response_serializer = OrderResponseSerializer({
                'message': 'Order status updated successfully',
                'order': order
            })
            return Response(response_serializer.data)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=404)

@extend_schema_view(
    get=extend_schema(
        summary="List promo codes",
        description="Get a list of all active promo codes.",
        tags=["Promo Code Management"]
    ),
    post=extend_schema(
        summary="Create promo code",
        description="Create a new promo code. Admin only.",
        tags=["Promo Code Management"]
    )
)
class PromoCodeListCreateView(generics.ListCreateAPIView):
    queryset = PromoCode.objects.filter(status='active')
    serializer_class = PromoCodeSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [AllowAny()]
        return [IsAdminUser()]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return PromoCode.objects.all()
        return PromoCode.objects.filter(status='active')

@extend_schema_view(
    get=extend_schema(
        summary="Get promo code details",
        description="Get detailed information about a specific promo code.",
        tags=["Promo Code Management"]
    ),
    put=extend_schema(
        summary="Update promo code",
        description="Update an existing promo code. Admin only.",
        tags=["Promo Code Management"]
    ),
    patch=extend_schema(
        summary="Partially update promo code",
        description="Partially update an existing promo code. Admin only.",
        tags=["Promo Code Management"]
    ),
    delete=extend_schema(
        summary="Delete promo code",
        description="Delete a promo code. Admin only.",
        tags=["Promo Code Management"]
    )
)
class PromoCodeRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = PromoCode.objects.all()
    serializer_class = PromoCodeSerializer
    permission_classes = [IsAdminUser]

@extend_schema_view(
    post=extend_schema(
        summary="Apply promo code",
        description="Apply a promo code to the current cart.",
        request=ApplyPromoCodeSerializer,
        responses={
            200: inline_serializer(
                name='ApplyPromoCodeResponse',
                fields={
                    'message': serializers.CharField(),
                    'discount_amount': serializers.DecimalField(max_digits=10, decimal_places=2),
                    'new_total': serializers.DecimalField(max_digits=10, decimal_places=2)
                }
            )
        },
        tags=["Promo Code Management"]
    )
)
class ApplyPromoCodeView(generics.CreateAPIView):
    serializer_class = ApplyPromoCodeSerializer
    permission_classes = [IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        code = serializer.validated_data['code']
        promo_code = PromoCode.objects.get(code=code)
        cart = request.user.cart
        
        try:
            discount = promo_code.apply(request.user, cart.total_price, cart.items.all())
            
            # Update cart with promo code
            cart.promo_code = promo_code
            cart.promo_code_discount = discount
            cart.save()
            
            return Response({
                'message': 'Promo code applied successfully',
                'discount_amount': discount,
                'new_total': cart.total_price - discount
            })
        except ValueError as e:
            return Response({
                'message': str(e)
            }, status=400)

@extend_schema_view(
    post=extend_schema(
        summary="Remove promo code",
        description="Remove the currently applied promo code from the cart.",
        responses={
            200: inline_serializer(
                name='RemovePromoCodeResponse',
                fields={
                    'message': serializers.CharField(),
                    'new_total': serializers.DecimalField(max_digits=10, decimal_places=2)
                }
            )
        },
        tags=["Promo Code Management"]
    )
)
class RemovePromoCodeView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        cart = request.user.cart
        if not cart or not cart.promo_code:
            return Response({
                'message': 'No promo code applied'
            }, status=400)
        
        # Remove promo code
        cart.promo_code = None
        cart.promo_code_discount = 0
        cart.save()
        
        return Response({
            'message': 'Promo code removed successfully',
            'new_total': cart.total_price
        })

class CartAddItemView(generics.CreateAPIView):
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated, IsCartOwner]

    def get_queryset(self):
        return CartItem.objects.filter(cart__user=self.request.user)

class CartRemoveItemView(generics.DestroyAPIView):
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated, IsCartOwner]

    def get_queryset(self):
        return CartItem.objects.filter(cart__user=self.request.user)

class CartUpdateQuantityView(generics.UpdateAPIView):
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated, IsCartOwner]

    def get_queryset(self):
        return CartItem.objects.filter(cart__user=self.request.user)

class CartClearView(generics.DestroyAPIView):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated, IsCartOwner]

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        cart = self.get_object()
        cart.items.all().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class CartViewSet(viewsets.ModelViewSet):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated, IsCartOwner]
    pagination_class = DynamicPageSizePagination

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Cart.objects.all()
        return Cart.objects.filter(user=user)

    @extend_schema(
        summary="Get cart details",
        description="Get detailed information about a specific cart.",
        tags=["Cart Management"]
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Update cart",
        description="Update an existing cart.",
        tags=["Cart Management"]
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(
        summary="Partially update cart",
        description="Partially update an existing cart.",
        tags=["Cart Management"]
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        summary="Delete cart",
        description="Delete a specific cart.",
        tags=["Cart Management"]
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

class ProductRecommendationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ProductRecommendationSerializer
    permission_classes = [AllowAny]
    pagination_class = DynamicPageSizePagination

    def get_queryset(self):
        product_id = self.kwargs.get('product_id')
        if not product_id:
            return ProductRecommendation.objects.none()

        return ProductRecommendation.objects.filter(
            product_id=product_id
        ).select_related(
            'recommended_product',
            'recommended_product__brand',
            'recommended_product__subcategory',
            'recommended_product__gender'
        ).prefetch_related(
            'recommended_product__images',
            'recommended_product__variants'
        ).order_by('-score', '-created_at')

    @extend_schema(
        summary="Get product recommendations",
        description="Get a list of recommended products for a specific product.",
        tags=["Product Management"]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Get recommendation details",
        description="Get details of a specific product recommendation.",
        tags=["Product Management"]
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

@extend_schema(
    summary="Get active branches",
    description="Get a list of all active branches (stores and pickup points)",
    tags=["Branch Management"],
    responses={
        200: serializers.ListSerializer(child=AddressSerializer()),
        401: OpenApiResponse(
            description="Authentication failed",
            response=inline_serializer(
                name='AuthError',
                fields={
                    'error': serializers.CharField(),
                    'message': serializers.CharField(),
                    'status': serializers.IntegerField(),
                }
            )
        )
    }
)
class ActiveBranchesView(TelegramAuthMixin, APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        branches = Address.objects.filter(
            branch_type__in=['store', 'pickup'],
            is_active=True
        ).order_by('name')
        
        serializer = AddressSerializer(branches, many=True)
        return Response(serializer.data)

class DirectPurchaseView(TelegramAuthMixin, APIView):
    permission_classes = [AllowAny]
    
    @extend_schema(
        request=DirectPurchaseSerializer,
        responses={201: OrderResponseSerializer},
        description="Mahsulotni bevosita detail sahifasidan sotib olish"
    )
    def post(self, request):
        serializer = DirectPurchaseSerializer(data=request.data)
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    # Get user from telegram ID
                    user = self.get_user_from_telegram_id()
                    
                    # Get validated data
                    data = serializer.validated_data
                    product = Product.objects.get(id=data['product_id'])
                    pickup_branch = Address.objects.get(id=data['pickup_branch_id'])
                    
                    # Create order
                    order = Order.objects.create(
                        user=user,
                        pickup_branch=pickup_branch,
                        customer_name=data['customer_name'],
                        phone_number=data['phone_number'],
                        payment_method=data['payment_method'],
                        order_note=data.get('order_note', ''),
                        is_split_payment=data.get('is_split_payment', False),
                        status='pending'
                    )
                    
                    # Add order item
                    variant = None
                    if data.get('variant_id'):
                        variant = ProductVariant.objects.get(id=data['variant_id'])
                    
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        variant=variant,
                        quantity=data['quantity'],
                        price=product.discount_price or product.price
                    )
                    
                    # Calculate totals
                    order.calculate_totals()
                    
                    # Update product stock
                    if variant:
                        variant.stock -= data['quantity']
                        variant.save()
                    
                    return Response({
                        'message': 'Buyurtma muvaffaqiyatli yaratildi',
                        'order': OrderSerializer(order, context={'request': request}).data
                    }, status=201)
                    
            except Exception as e:
                return Response({
                    'message': str(e)
                }, status=400)
                
        return Response(serializer.errors, status=400)