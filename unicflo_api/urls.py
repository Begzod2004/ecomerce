from django.urls import path
from .generic_views import (
    # User views
    UserList, UserDetail, UserMe,
    # Category views
    CategoryList, CategoryDetail,
    # Product views
    ProductList, ProductDetail, SimilarProducts,
    # Product Review views
    ProductReviewList, ProductReviewDetail, ProductReviewsByProduct,
    # Wishlist views
    WishlistList, WishlistDetail, AddProductToWishlist, RemoveProductFromWishlist,
    # Cart views
    CartList, CartDetail, MyCart,
    # CartItem views
    CartItemList, CartItemDetail, AddToCart,
    # Coupon views
    CouponList, CouponDetail, ValidateCoupon,
    # Order views
    OrderList, OrderDetail, CancelOrder,
    # Address views
    AddressList, AddressDetail, DefaultAddress
)

app_name = 'unicflo_api'

urlpatterns = [
    # User URLs
    path('users/', UserList.as_view(), name='user-list'),
    path('users/<int:pk>/', UserDetail.as_view(), name='user-detail'),
    path('users/me/', UserMe.as_view(), name='user-me'),
    
    # Category URLs
    path('categories/', CategoryList.as_view(), name='category-list'),
    path('categories/<int:pk>/', CategoryDetail.as_view(), name='category-detail'),
    
    # Product URLs
    path('products/', ProductList.as_view(), name='product-list'),
    path('products/<int:pk>/', ProductDetail.as_view(), name='product-detail'),
    path('products/<int:pk>/similar/', SimilarProducts.as_view(), name='product-similar'),
    
    # Product Review URLs
    path('reviews/', ProductReviewList.as_view(), name='review-list'),
    path('reviews/<int:pk>/', ProductReviewDetail.as_view(), name='review-detail'),
    path('reviews/product/', ProductReviewsByProduct.as_view(), name='product-reviews'),
    
    # Wishlist URLs
    path('wishlist/', WishlistList.as_view(), name='wishlist-list'),
    path('wishlist/<int:pk>/', WishlistDetail.as_view(), name='wishlist-detail'),
    path('wishlist/add-product/', AddProductToWishlist.as_view(), name='wishlist-add-product'),
    path('wishlist/remove-product/', RemoveProductFromWishlist.as_view(), name='wishlist-remove-product'),
    
    # Cart URLs
    path('carts/', CartList.as_view(), name='cart-list'),
    path('carts/<int:pk>/', CartDetail.as_view(), name='cart-detail'),
    path('carts/my-cart/', MyCart.as_view(), name='my-cart'),
    
    # CartItem URLs
    path('cart-items/', CartItemList.as_view(), name='cart-item-list'),
    path('cart-items/<int:pk>/', CartItemDetail.as_view(), name='cart-item-detail'),
    path('cart-items/add/', AddToCart.as_view(), name='add-to-cart'),
    
    # Coupon URLs
    path('coupons/', CouponList.as_view(), name='coupon-list'),
    path('coupons/<int:pk>/', CouponDetail.as_view(), name='coupon-detail'),
    path('coupons/validate/', ValidateCoupon.as_view(), name='validate-coupon'),
    
    # Order URLs
    path('orders/', OrderList.as_view(), name='order-list'),
    path('orders/<int:pk>/', OrderDetail.as_view(), name='order-detail'),
    path('orders/<int:pk>/cancel/', CancelOrder.as_view(), name='cancel-order'),
    
    # Address URLs
    path('addresses/', AddressList.as_view(), name='address-list'),
    path('addresses/<int:pk>/', AddressDetail.as_view(), name='address-detail'),
    path('addresses/default/', DefaultAddress.as_view(), name='default-address'),
]
