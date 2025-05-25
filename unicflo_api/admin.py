from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.admin import ModelAdmin, TabularInline, StackedInline
from django.contrib.admin.widgets import AdminFileWidget
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.db.models import Count
from .models import (
    User, Category, Product, ProductImage,
    Wishlist, Cart, CartItem, Order, OrderItem, Address, Subcategory,
    Brand, Color, Size, Material, Season, ShippingMethod,
    ProductVariant, GenderCategory, PromoCode
)
from django.utils import timezone


class CustomUserAdmin(UserAdmin, ModelAdmin):
    list_display = ('username', 'telegram_id', 'telegram_username', 'is_telegram_admin', 'is_telegram_user', 'is_verified')
    list_filter = ('is_telegram_admin', 'is_telegram_user', 'is_verified')
    search_fields = ('username', 'telegram_username', 'telegram_id', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    fieldsets = (
        ('Personal Info', {
            'fields': ('username', 'telegram_id', 'telegram_username', 'first_name', 'last_name')
        }),
        ('Telegram Status', {
            'fields': ('is_telegram_user', 'is_telegram_admin', 'is_verified')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Important dates', {
            'fields': ('last_login', 'date_joined')
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'telegram_id', 'telegram_username', 'is_telegram_admin'),
        }),
    )

    def save_model(self, request, obj, form, change):
        # If making user a Telegram admin, ensure they have a telegram_id
        if obj.is_telegram_admin and not obj.telegram_id:
            self.message_user(request, "Cannot make user Telegram admin without telegram_id", level='ERROR')
            return
        super().save_model(request, obj, form, change)


class ProductImageInline(TabularInline):
    model = ProductImage
    extra = 1
    show_change_link = True
    fields = ('color', 'image', 'is_primary', 'alt_text', 'image_preview')
    readonly_fields = ('image_preview',)
    verbose_name = "Product Image"
    verbose_name_plural = "Product Images"
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 100px;" />',
                obj.image.url
            )
        return "No image"
    image_preview.short_description = "Предпросмотр"


class ProductVariantInline(TabularInline):
    model = ProductVariant
    extra = 1
    show_change_link = True
    fields = ('color', 'size', 'stock')
    verbose_name = "Product Variant"
    verbose_name_plural = "Product Variants"


class OrderItemInline(TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'quantity', 'price', 'item_total')
    show_change_link = True
    verbose_name = "Order Item"
    verbose_name_plural = "Order Items"
    can_delete = False

    def item_total(self, obj):
        if obj.price is None:
            return '-'
        return f"{obj.total_price:.2f}"
    item_total.short_description = 'Total'


class SubcategoryInline(TabularInline):
    model = Subcategory
    extra = 1
    show_change_link = True
    fields = ('name', 'slug', 'image', 'created_at')
    readonly_fields = ('created_at',)
    verbose_name = "Subcategory"
    verbose_name_plural = "Subcategories"


class CategoryAdmin(ModelAdmin):
    list_display = ('name', 'gender', 'created_at', 'product_count')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'description')
    list_filter = ('gender',)
    ordering = ('name',)
    readonly_fields = ('created_at',)
    verbose_name = "Категория"
    verbose_name_plural = "Категории"
    inlines = [SubcategoryInline]
    actions = ['delete_selected']

    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'slug', 'description', 'gender', 'image')
        }),
    )

    def product_count(self, obj):
        return obj.subcategories.aggregate(total=Count('products'))['total']
    product_count.short_description = "Количество товаров"


class BrandAdmin(ModelAdmin):
    list_display = ('name', 'created_at')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'description')
    ordering = ('name',)
    verbose_name = "Бренд"
    verbose_name_plural = "Бренды"
    actions = ['delete_selected']

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'logo')
        }),
    )


class ColorAdmin(ModelAdmin):
    list_display = ('name', 'hex_code', 'color_preview')
    search_fields = ('name', 'hex_code')
    ordering = ('name',)
    verbose_name = "Цвет"
    verbose_name_plural = "Цвета"
    actions = ['delete_selected']

    def color_preview(self, obj):
        return format_html(
            '<div style="background-color: {}; width: 30px; height: 30px;"></div>',
            obj.hex_code
        )
    color_preview.short_description = "Color"


class SizeAdmin(ModelAdmin):
    list_display = ('name', 'size_eu', 'size_us', 'size_uk', 'size_fr')
    search_fields = ('name',)
    ordering = ('name',)
    verbose_name = "Размер"
    verbose_name_plural = "Размеры"
    actions = ['delete_selected']


class MaterialAdmin(ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('name',)
    verbose_name = "Материал"
    verbose_name_plural = "Материалы"
    actions = ['delete_selected']


class SeasonAdmin(ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('name',)
    verbose_name = "Сезон"
    verbose_name_plural = "Сезоны"
    actions = ['delete_selected']


class ShippingMethodAdmin(ModelAdmin):
    list_display = ('name', 'min_days', 'max_days', 'price', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)
    ordering = ('name',)
    verbose_name = "Метод доставки"
    verbose_name_plural = "Методы доставки"
    actions = ['delete_selected']


class ProductAdmin(ModelAdmin):
    list_display = ('id', 'name', 'subcategory', 'brand', 'price', 'discount_price', 'is_featured', 'is_active', 'created_at')
    list_filter = ('subcategory', 'brand', 'is_featured', 'is_active', 'gender', 'season')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'description', 'brand__name')
    inlines = [ProductVariantInline, ProductImageInline]
    readonly_fields = ('preview_images',)
    filter_horizontal = ('materials', 'shipping_methods')
    verbose_name = "Товар"
    verbose_name_plural = "Товары"
    actions = ['delete_selected']
    list_per_page = 20

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'gender')
        }),
        ('Categorization', {
            'fields': ('subcategory', 'brand', 'season', 'materials')
        }),
        ('Pricing', {
            'fields': ('price', 'discount_price')
        }),
        ('Shipping', {
            'fields': ('shipping_methods',)
        }),
        ('Status', {
            'fields': ('is_featured', 'is_active')
        }),
        ('Images', {
            'fields': ('preview_images',)
        }),
    )

    def preview_images(self, obj):
        html = []
        for image in obj.images.filter(is_primary=True):
            html.append(
                format_html(
                    '<img src="{}" style="max-height: 100px; max-width: 100px; margin-right: 10px;" />',
                    image.image.url
                )
            )
        return format_html(''.join(html))
    preview_images.short_description = "Primary Images"


class ProductVariantAdmin(ModelAdmin):
    list_display = ('product', 'color', 'size', 'stock')
    list_filter = ('product', 'color', 'size')
    search_fields = ('product__name', 'color__name', 'size__name')
    ordering = ('product', 'color', 'size')
    verbose_name = "Вариант товара"
    verbose_name_plural = "Варианты товара"
    actions = ['delete_selected']


class CartItemInline(TabularInline):
    model = CartItem
    extra = 0
    show_change_link = True
    readonly_fields = ('total_price',)
    verbose_name = "Cart Item"
    verbose_name_plural = "Cart Items"
    
    def total_price(self, obj):
        return obj.total_price
    total_price.short_description = "Итого"


class CartAdmin(ModelAdmin):
    list_display = ('user', 'created_at', 'total_price', 'item_count')
    search_fields = ('user__username',)
    inlines = [CartItemInline]
    verbose_name = "Корзина"
    verbose_name_plural = "Корзины"
    actions = ['delete_selected']
    
    def item_count(self, obj):
        return obj.items.count()
    item_count.short_description = "Количество товаров"


class CartItemAdmin(ModelAdmin):
    list_display = ('cart', 'product', 'quantity', 'total_price')
    list_filter = ('cart__user',)
    search_fields = ('product__name',)
    verbose_name = "Товар в корзине"
    verbose_name_plural = "Товары в корзине"
    actions = ['delete_selected']


class OrderAdmin(ModelAdmin):
    list_display = ('id', 'user', 'phone_number', 'total_amount', 'final_amount', 'status_badge', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'tracking_number', 'phone_number')
    inlines = [OrderItemInline]
    readonly_fields = ('created_at', 'updated_at', 'order_summary')
    actions = ['delete_selected']
    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'status', 'phone_number', 'order_summary')
        }),
        ('Оплата', {
            'fields': ('total_amount', 'discount_amount', 'shipping_amount', 'final_amount')
        }),
        ('Доставка', {
            'fields': ('shipping_address', 'billing_address', 'tracking_number')
        }),
        ('Дополнительно', {
            'fields': ('order_note', 'created_at', 'updated_at')
        }),
    )
    verbose_name = "Заказ"
    verbose_name_plural = "Заказы"
    
    def status_badge(self, obj):
        status_colors = {
            'pending': '#ffc107',      # желтый
            'processing': '#17a2b8',   # синий
            'shipped': '#007bff',      # голубой
            'delivered': '#28a745',    # зеленый
            'canceled': '#dc3545',     # красный
            'returned': '#6c757d',     # серый
        }
        status_names = {
            'pending': 'Ожидает',
            'processing': 'Обработка',
            'shipped': 'Отправлен',
            'delivered': 'Доставлен',
            'canceled': 'Отменен',
            'returned': 'Возвращен',
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; '
            'border-radius: 15px;">{}</span>',
            status_colors[obj.status],
            status_names[obj.status]
        )
    status_badge.short_description = "Статус"
    
    def order_summary(self, obj):
        html = '<div style="margin-bottom: 20px;">'
        html += '<h3 style="margin-bottom: 10px;">Состав заказа:</h3>'
        html += '<table style="width: 100%; border-collapse: collapse;">'
        html += '<tr style="background-color: #f8f9fa;">'
        html += '<th style="padding: 8px; border: 1px solid #dee2e6;">Товар</th>'
        html += '<th style="padding: 8px; border: 1px solid #dee2e6;">Количество</th>'
        html += '<th style="padding: 8px; border: 1px solid #dee2e6;">Цена</th>'
        html += '<th style="padding: 8px; border: 1px solid #dee2e6;">Итого</th>'
        html += '</tr>'
        
        for item in obj.items.all():
            html += '<tr>'
            html += f'<td style="padding: 8px; border: 1px solid #dee2e6;">{item.product.name}</td>'
            html += f'<td style="padding: 8px; border: 1px solid #dee2e6;">{item.quantity}</td>'
            html += f'<td style="padding: 8px; border: 1px solid #dee2e6;">{item.price}</td>'
            html += f'<td style="padding: 8px; border: 1px solid #dee2e6;">{item.total_price}</td>'
            html += '</tr>'
        
        html += '</table>'
        html += '<div style="margin-top: 15px;">'
        html += f'<p><strong>Сумма заказа:</strong> {obj.total_amount}</p>'
        if obj.discount_amount:
            html += f'<p><strong>Скидка:</strong> {obj.discount_amount}</p>'
        html += f'<p><strong>Доставка:</strong> {obj.shipping_amount}</p>'
        html += f'<p><strong>Итого к оплате:</strong> {obj.final_amount}</p>'
        html += '</div>'
        html += '</div>'
        return mark_safe(html)
    order_summary.short_description = "Информация о заказе"


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'branch_type', 'city', 'region', 
        'phone', 'is_active', 'is_24_hours'
    ]
    list_filter = [
        'branch_type', 'city', 'region', 'is_active',
        'has_fitting_room', 'has_parking', 'is_24_hours'
    ]
    search_fields = ['name', 'street', 'city', 'region', 'phone']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = [
        ('Basic Information', {
            'fields': [
                'name', 'branch_type', 'is_active',
                'working_hours', 'is_24_hours'
            ]
        }),
        ('Location', {
            'fields': [
                'street', 'district', 'city', 'region',
                'country', 'postal_code', 'location_link'
            ]
        }),
        ('Contact Information', {
            'fields': [
                'phone', 'manager_name', 'manager_phone'
            ]
        }),
        ('Facilities', {
            'fields': [
                'has_fitting_room', 'has_parking'
            ]
        }),
        ('System Information', {
            'classes': ['collapse'],
            'fields': ['created_at', 'updated_at']
        })
    ]
    list_per_page = 20
    ordering = ['city', 'name']
    save_on_top = True

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if obj:  # editing an existing object
            readonly_fields.extend(['created_at', 'updated_at'])
        return readonly_fields


class WishlistAdmin(ModelAdmin):
    list_display = ('user', 'created_at', 'product_count')
    search_fields = ('user__username',)
    filter_horizontal = ('products',)
    verbose_name = "Список желаний"
    verbose_name_plural = "Списки желаний"
    actions = ['delete_selected']
    
    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = "Количество товаров"


class SubcategoryAdmin(ModelAdmin):
    list_display = ('name', 'category', 'gender', 'created_at')
    list_filter = ('category', 'gender')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'description', 'category__name')
    ordering = ('category', 'name')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'category', 'gender', 'description')
        }),
        ('Media', {
            'fields': ('image',)
        }),
    )


class GenderCategoryAdmin(ModelAdmin):
    list_display = ('name', 'created_at')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'description')
    ordering = ('name',)
    verbose_name = "Гендерная категория"
    verbose_name_plural = "Гендерные категории"
    actions = ['delete_selected']


@admin.register(PromoCode)
class PromoCodeAdmin(ModelAdmin):
    list_display = ('code', 'discount_type', 'discount_value', 'status', 'usage_count', 'validity_period', 'is_active')
    list_filter = ('status', 'discount_type', 'is_first_purchase_only', 'is_new_user_only', 'is_birthday_only', 'is_seasonal')
    search_fields = ('code', 'description')
    readonly_fields = ('usage_count', 'created_at', 'updated_at')
    filter_horizontal = ('applicable_categories', 'applicable_products', 'excluded_products')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('code', 'description', 'status')
        }),
        ('Скидка', {
            'fields': ('discount_type', 'discount_value', 'min_order_amount', 'max_discount_amount')
        }),
        ('Период действия', {
            'fields': ('start_date', 'end_date')
        }),
        ('Ограничения использования', {
            'fields': ('usage_limit', 'per_user_limit', 'min_items_in_cart', 'max_items_in_cart')
        }),
        ('Специальные условия', {
            'fields': (
                'is_first_purchase_only',
                'is_new_user_only',
                'is_birthday_only',
                'is_seasonal',
                'seasonal_start_month',
                'seasonal_end_month'
            )
        }),
        ('Применимость', {
            'fields': ('applicable_categories', 'applicable_products', 'excluded_products')
        }),
        ('Статистика', {
            'fields': ('usage_count', 'created_at', 'updated_at')
        }),
    )
    
    def validity_period(self, obj):
        return f"{obj.start_date.strftime('%d.%m.%Y')} - {obj.end_date.strftime('%d.%m.%Y')}"
    validity_period.short_description = 'Период действия'
    
    def is_active(self, obj):
        now = timezone.now()
        return obj.start_date <= now <= obj.end_date and obj.status == 'active'
    is_active.boolean = True
    is_active.short_description = 'Активен'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only on creation
            # Generate a random code if not provided
            if not obj.code:
                import random
                import string
                code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
                while PromoCode.objects.filter(code=code).exists():
                    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
                obj.code = code
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Auto-update status based on dates
        now = timezone.now()
        qs.filter(end_date__lt=now, status='active').update(status='expired')
        return qs


# Register all models
admin.site.register(User, CustomUserAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Subcategory, SubcategoryAdmin)
admin.site.register(Brand, BrandAdmin)
admin.site.register(Color, ColorAdmin)
admin.site.register(Size, SizeAdmin)
admin.site.register(Material, MaterialAdmin)
admin.site.register(Season, SeasonAdmin)
admin.site.register(ShippingMethod, ShippingMethodAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(ProductVariant, ProductVariantAdmin)
admin.site.register(Cart, CartAdmin)
admin.site.register(CartItem, CartItemAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(Wishlist, WishlistAdmin)
admin.site.register(GenderCategory, GenderCategoryAdmin)
