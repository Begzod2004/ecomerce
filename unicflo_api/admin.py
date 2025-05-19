from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline, StackedInline
from .models import (
    User, UserProfile, Category, Product, ProductImage, ProductReview,
    Wishlist, Cart, CartItem, Coupon, Order, OrderItem, Address
)


class UserProfileInline(StackedInline):
    model = UserProfile
    can_delete = False
    classes = ["collapse"]


class CustomUserAdmin(UserAdmin, ModelAdmin):
    inlines = [UserProfileInline]
    list_display = ('username', 'email', 'is_staff', 'is_verified', 'created_at')
    list_filter = ('is_staff', 'is_verified', 'created_at')
    search_fields = ('username', 'email', 'phone_number')
    unfold_form_actions = True
    warn_unsaved_form = True
    ordering = ('-date_joined',)
    

class ProductImageInline(TabularInline):
    model = ProductImage
    extra = 1
    show_change_link = True
    fields = ('image', 'is_primary', 'image_preview')
    readonly_fields = ('image_preview',)
    
    def image_preview(self, obj):
        if obj.image:
            try:
                return format_html('<img src="{}" style="max-height: 100px; max-width: 100px;" />', obj.image.url)
            except:
                return "Image URL error"
        return "No image"
    image_preview.short_description = "Preview"


class ProductReviewInline(TabularInline):
    model = ProductReview
    extra = 0
    readonly_fields = ('user', 'rating', 'comment', 'created_at')
    show_change_link = True


class OrderItemInline(TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'quantity', 'price', 'item_total')
    show_change_link = True
    
    def item_total(self, obj):
        return f"${obj.price * obj.quantity}"
    item_total.short_description = "Total"


class CategoryAdmin(ModelAdmin):
    list_display = ('name', 'parent', 'created_at', 'product_count')
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ('parent',)
    search_fields = ('name', 'description')
    unfold_form_actions = True
    warn_unsaved_form = True
    
    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = "Products"


class ProductAdmin(ModelAdmin):
    list_display = ('name', 'category', 'price', 'discount_price', 'stock', 'is_featured', 'is_active', 'created_at')
    list_filter = ('category', 'brand', 'is_featured', 'is_active')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'description', 'brand')
    inlines = [ProductImageInline, ProductReviewInline]
    readonly_fields = ('preview_images',)
    unfold_form_actions = True
    warn_unsaved_form = True
    fieldsets = (
        ("Basic Information", {
            "fields": ("name", "slug", "description", "category"),
        }),
        ("Pricing & Inventory", {
            "fields": ("price", "discount_price", "stock"),
        }),
        ("Product Details", {
            "fields": ("brand", "size", "color"),
        }),
        ("Display Settings", {
            "fields": ("is_featured", "is_active"),
        }),
        ("Images", {
            "fields": ("preview_images",),
        })
    )
    
    def preview_images(self, obj):
        html = '<div style="display: flex; flex-wrap: wrap; gap: 10px;">'
        for img in obj.images.all():
            if img.image:
                try:
                    html += f'<img src="{img.image.url}" style="max-height: 150px; max-width: 150px; object-fit: cover;" />'
                except:
                    html += '<span>Image URL error</span>'
        html += '</div>'
        return format_html(html)
    preview_images.short_description = "Product Images"


class ProductReviewAdmin(ModelAdmin):
    list_display = ('product', 'user', 'rating_stars', 'is_approved', 'created_at')
    list_filter = ('rating', 'is_approved', 'created_at')
    search_fields = ('product__name', 'user__username', 'comment')
    readonly_fields = ('user', 'product', 'rating', 'comment', 'created_at')
    unfold_list_actions = True
    unfold_form_actions = True
    list_select = True
    
    def rating_stars(self, obj):
        stars = '★' * obj.rating + '☆' * (5 - obj.rating)
        return format_html('<span style="color:#FFD700;">{}</span>', stars)
    rating_stars.short_description = "Rating"


class CartItemInline(TabularInline):
    model = CartItem
    extra = 0
    show_change_link = True
    readonly_fields = ('total_price',)
    
    def total_price(self, obj):
        return f"${obj.product.price * obj.quantity}"
    total_price.short_description = "Total"


class CartAdmin(ModelAdmin):
    list_display = ('user', 'created_at', 'total_price', 'item_count')
    search_fields = ('user__username',)
    inlines = [CartItemInline]
    unfold_list_actions = True
    list_select = True
    
    def item_count(self, obj):
        return obj.items.count()
    item_count.short_description = "Items"


class CartItemAdmin(ModelAdmin):
    list_display = ('cart', 'product', 'quantity', 'total_price')
    list_filter = ('cart__user',)
    search_fields = ('product__name',)
    unfold_list_actions = True
    list_select = True


class CouponAdmin(ModelAdmin):
    list_display = ('code', 'discount_amount', 'discount_percent', 'valid_from', 'valid_to', 'is_active')
    list_filter = ('is_active', 'valid_from', 'valid_to')
    search_fields = ('code', 'description')
    unfold_list_actions = True
    unfold_form_actions = True
    list_select = True
    fieldsets = (
        ("Coupon Information", {
            "fields": ("code", "description", "is_active"),
        }),
        ("Discount Settings", {
            "fields": ("discount_percent", "discount_amount", "min_purchase"),
        }),
        ("Validity Period", {
            "fields": ("valid_from", "valid_to"),
        }),
    )


class OrderAdmin(ModelAdmin):
    list_display = ('id', 'user', 'total_amount', 'final_amount', 'status_badge', 'payment_status', 'created_at')
    list_filter = ('status', 'payment_status', 'payment_method', 'created_at')
    search_fields = ('user__username', 'tracking_number')
    inlines = [OrderItemInline]
    readonly_fields = ('created_at', 'updated_at', 'order_summary')
    unfold_list_actions = True
    unfold_form_actions = True
    list_select = True
    fieldsets = (
        ("Order Information", {
            "fields": ("user", "status", "payment_method", "payment_status", "tracking_number"),
        }),
        ("Pricing", {
            "fields": ("total_amount", "discount_amount", "shipping_amount", "final_amount", "coupon"),
        }),
        ("Addresses", {
            "fields": ("shipping_address", "billing_address"),
        }),
        ("Notes & Dates", {
            "fields": ("order_note", "created_at", "updated_at"),
        }),
        ("Summary", {
            "fields": ("order_summary",),
        }),
    )
    
    def status_badge(self, obj):
        status_colors = {
            'pending': '#FFA500',  # Orange
            'processing': '#3498DB',  # Blue
            'shipped': '#9B59B6',  # Purple
            'delivered': '#2ECC71',  # Green
            'canceled': '#E74C3C',  # Red
            'returned': '#95A5A6',  # Gray
        }
        color = status_colors.get(obj.status, '#000000')
        return format_html(
            '<span style="background-color:{}; color:white; padding:5px 10px; border-radius:3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = "Status"
    
    def order_summary(self, obj):
        items = obj.items.all()
        html = '<div style="padding: 10px; background-color: #f9f9f9; border-radius: 5px;">'
        html += f'<h3 style="margin-top:0;">Order #{obj.id}</h3>'
        html += '<table style="width: 100%; border-collapse: collapse;">'
        html += '<tr style="background-color: #f2f2f2;"><th style="padding: 8px; text-align: left;">Product</th><th style="padding: 8px; text-align: right;">Quantity</th><th style="padding: 8px; text-align: right;">Price</th><th style="padding: 8px; text-align: right;">Total</th></tr>'
        
        for item in items:
            html += f'<tr><td style="padding: 8px; border-top: 1px solid #ddd;">{item.product.name}</td>'
            html += f'<td style="padding: 8px; border-top: 1px solid #ddd; text-align: right;">{item.quantity}</td>'
            html += f'<td style="padding: 8px; border-top: 1px solid #ddd; text-align: right;">${item.price}</td>'
            html += f'<td style="padding: 8px; border-top: 1px solid #ddd; text-align: right;">${item.price * item.quantity}</td></tr>'
        
        html += '<tr style="border-top: 2px solid #ddd;"><td colspan="3" style="padding: 8px; text-align: right;"><strong>Subtotal</strong></td>'
        html += f'<td style="padding: 8px; text-align: right;">${obj.total_amount}</td></tr>'
        
        if obj.discount_amount > 0:
            html += '<tr><td colspan="3" style="padding: 8px; text-align: right;"><strong>Discount</strong></td>'
            html += f'<td style="padding: 8px; text-align: right;">-${obj.discount_amount}</td></tr>'
        
        html += '<tr><td colspan="3" style="padding: 8px; text-align: right;"><strong>Shipping</strong></td>'
        html += f'<td style="padding: 8px; text-align: right;">${obj.shipping_amount}</td></tr>'
        
        html += '<tr><td colspan="3" style="padding: 8px; text-align: right;"><strong>Final Total</strong></td>'
        html += f'<td style="padding: 8px; text-align: right;"><strong>${obj.final_amount}</strong></td></tr>'
        html += '</table></div>'
        
        return format_html(html)
    order_summary.short_description = "Order Summary"


class AddressAdmin(ModelAdmin):
    list_display = ('user', 'full_name', 'address_type', 'city', 'country', 'is_default')
    list_filter = ('address_type', 'country', 'is_default')
    search_fields = ('user__username', 'full_name', 'street', 'city')
    unfold_list_actions = True
    unfold_form_actions = True
    list_select = True
    fieldsets = (
        ("User Information", {
            "fields": ("user", "full_name", "phone"),
        }),
        ("Address Type", {
            "fields": ("address_type", "is_default"),
        }),
        ("Address Details", {
            "fields": ("street", "apartment", "city", "state", "country", "postal_code"),
        }),
    )


class WishlistAdmin(ModelAdmin):
    list_display = ('user', 'created_at', 'product_count')
    search_fields = ('user__username',)
    filter_horizontal = ('products',)
    unfold_list_actions = True
    list_select = True
    
    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = "Products"


admin.site.register(User, CustomUserAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(ProductReview, ProductReviewAdmin)
admin.site.register(Wishlist, WishlistAdmin)
admin.site.register(Cart, CartAdmin)
admin.site.register(CartItem, CartItemAdmin)
admin.site.register(Coupon, CouponAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(Address, AddressAdmin)
