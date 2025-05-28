from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    # User views
    UserListCreateView, UserRetrieveUpdateDestroyView, UserMeView,
    # Category views
    CategoryListCreateView, CategoryRetrieveUpdateDestroyView,
    # Subcategory views
    SubcategoryListCreateView, SubcategoryRetrieveUpdateDestroyView,
    # Product views
    ProductListCreateView, ProductRetrieveUpdateDestroyView, SimilarProductsView,
    # Wishlist views
    WishlistListCreateView, AddToWishlistView,
    # Cart views
    CartListCreateView, MyCartView,
    # CartItem views
    CartItemListCreateView, CartItemRetrieveUpdateDestroyView, AddToCartView,
    # Order views
    OrderListCreateView, OrderRetrieveUpdateDestroyView, CancelOrderView,
    # Address views
    AddressListCreateView, AddressRetrieveUpdateDestroyView,
    # Brand views
    BrandListCreateView, BrandRetrieveUpdateDestroyView,
    # Color views
    ColorListCreateView, ColorRetrieveUpdateDestroyView,
    # Size views
    SizeListCreateView, SizeRetrieveUpdateDestroyView,
    # Material views
    MaterialListCreateView, MaterialRetrieveUpdateDestroyView,
    # Season views
    SeasonListCreateView, SeasonRetrieveUpdateDestroyView,
    # Shipping Method views
    ShippingMethodListCreateView, ShippingMethodRetrieveUpdateDestroyView,
    # Promo Code views
    PromoCodeListCreateView, PromoCodeRetrieveUpdateDestroyView,
    ApplyPromoCodeView, RemovePromoCodeView,
    CartViewSet,
    ProductRecommendationViewSet,
    CartAddItemView,
    CartRemoveItemView,
    CartUpdateQuantityView,
    CartClearView,
    DirectPurchaseView,
    ActiveBranchesView,
)

app_name = 'unicflo_api'

router = DefaultRouter()
router.register(r'carts', CartViewSet, basename='cart')

# Product recommendations
router.register(
    r'products/(?P<product_id>\d+)/recommendations',
    ProductRecommendationViewSet,
    basename='product-recommendations'
)

urlpatterns = [
    # User URLs
    path('users/', UserListCreateView.as_view(), name='user-list'),
    path('users/<int:pk>/', UserRetrieveUpdateDestroyView.as_view(), name='user-detail'),
    path('users/me/', UserMeView.as_view(), name='user-me'),
    
    # Category URLs
    path('categories/', CategoryListCreateView.as_view(), name='category-list'),
    path('categories/<slug:slug>/', CategoryRetrieveUpdateDestroyView.as_view(), name='category-detail'),
    
    # Subcategory URLs
    path('subcategories/', SubcategoryListCreateView.as_view(), name='subcategory-list'),
    path('subcategories/<slug:slug>/', SubcategoryRetrieveUpdateDestroyView.as_view(), name='subcategory-detail'),
    
    # Brand URLs
    path('brands/', BrandListCreateView.as_view(), name='brand-list'),
    path('brands/<slug:slug>/', BrandRetrieveUpdateDestroyView.as_view(), name='brand-detail'),
    
    # Color URLs
    path('colors/', ColorListCreateView.as_view(), name='color-list'),
    path('colors/<int:pk>/', ColorRetrieveUpdateDestroyView.as_view(), name='color-detail'),
    
    # Size URLs
    path('sizes/', SizeListCreateView.as_view(), name='size-list'),
    path('sizes/<int:pk>/', SizeRetrieveUpdateDestroyView.as_view(), name='size-detail'),
    
    # Material URLs
    path('materials/', MaterialListCreateView.as_view(), name='material-list'),
    path('materials/<int:pk>/', MaterialRetrieveUpdateDestroyView.as_view(), name='material-detail'),
    
    # Season URLs
    path('seasons/', SeasonListCreateView.as_view(), name='season-list'),
    path('seasons/<int:pk>/', SeasonRetrieveUpdateDestroyView.as_view(), name='season-detail'),
    
    # Shipping Method URLs
    path('shipping-methods/', ShippingMethodListCreateView.as_view(), name='shipping-method-list'),
    path('shipping-methods/<int:pk>/', ShippingMethodRetrieveUpdateDestroyView.as_view(), name='shipping-method-detail'),
    
    # Product URLs
    path('products/', ProductListCreateView.as_view(), name='product-list'),
    path('products/<slug:slug>/', ProductRetrieveUpdateDestroyView.as_view(), name='product-detail'),
    path('products/<int:pk>/similar/', SimilarProductsView.as_view(), name='similar-products'),
    
    # Wishlist URLs
    path('wishlist/', WishlistListCreateView.as_view(), name='wishlist-list'),
    path('wishlist/add/', AddToWishlistView.as_view(), name='add-to-wishlist'),
    
    # Cart URLs
    path('cart/items/', CartItemListCreateView.as_view(), name='cart-item-list'),
    path('cart/items/<int:pk>/', CartItemRetrieveUpdateDestroyView.as_view(), name='cart-item-detail'),
    path('cart/add/', AddToCartView.as_view(), name='add-to-cart'),
    path('cart/', MyCartView.as_view(), name='my-cart'),
    path('carts/', CartListCreateView.as_view(), name='cart-list'),
    path('carts/<int:pk>/', CartViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='cart-detail'),
    path('carts/<int:pk>/add-item/', CartAddItemView.as_view(), name='cart-add-item'),
    path('carts/<int:pk>/remove-item/', CartRemoveItemView.as_view(), name='cart-remove-item'),
    path('carts/<int:pk>/update-quantity/', CartUpdateQuantityView.as_view(), name='cart-update-quantity'),
    path('carts/<int:pk>/apply-promo/', ApplyPromoCodeView.as_view(), name='cart-apply-promo'),
    path('carts/<int:pk>/remove-promo/', RemovePromoCodeView.as_view(), name='cart-remove-promo'),
    path('carts/<int:pk>/clear/', CartClearView.as_view(), name='cart-clear'),
    
    # Order URLs
    path('orders/', OrderListCreateView.as_view(), name='order-list'),
    path('orders/<int:id>/', OrderRetrieveUpdateDestroyView.as_view(), name='order-detail'),
    path('orders/<int:id>/cancel/', CancelOrderView.as_view(), name='cancel-order'),
    
    # Address URLs
    path('addresses/', AddressListCreateView.as_view(), name='address-list'),
    path('addresses/<int:pk>/', AddressRetrieveUpdateDestroyView.as_view(), name='address-detail'),
    
    # Branch URLs
    path('branches/', ActiveBranchesView.as_view(), name='active-branches'),
    
    # Promo Code URLs
    path('promo-codes/', PromoCodeListCreateView.as_view(), name='promo-code-list'),
    path('promo-codes/<int:pk>/', PromoCodeRetrieveUpdateDestroyView.as_view(), name='promo-code-detail'),
    path('promo-codes/apply/', ApplyPromoCodeView.as_view(), name='apply-promo-code'),
    path('promo-codes/remove/', RemovePromoCodeView.as_view(), name='remove-promo-code'),

    # Direct Purchase URL
    path('direct-purchase/', DirectPurchaseView.as_view(), name='direct-purchase'),
    
    path('', include(router.urls)),
]
