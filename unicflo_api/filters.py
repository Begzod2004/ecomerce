from django_filters import rest_framework as filters
from django.db.models import Q

from .models import Category, Subcategory, Product, User


class CategoryFilter(filters.FilterSet):
    gender = filters.NumberFilter(field_name='gender')
    search = filters.CharFilter(method='filter_search')

    class Meta:
        model = Category
        fields = ['gender']

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value) |
            Q(description__icontains=value)
        )


class SubcategoryFilter(filters.FilterSet):
    gender = filters.NumberFilter(field_name='gender')
    category = filters.NumberFilter(field_name='category')
    search = filters.CharFilter(method='filter_search')

    class Meta:
        model = Subcategory
        fields = ['gender', 'category']

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value) |
            Q(description__icontains=value)
        )


class ProductFilter(filters.FilterSet):
    # Category and Gender filters
    gender = filters.NumberFilter(field_name='gender')
    category = filters.NumberFilter(field_name='subcategory__category')
    subcategory = filters.NumberFilter(field_name='subcategory')
    
    # Brand filter
    brand = filters.NumberFilter(field_name='brand')
    
    # Price filters
    price_min = filters.NumberFilter(field_name='price', lookup_expr='gte')
    price_max = filters.NumberFilter(field_name='price', lookup_expr='lte')
    has_discount = filters.BooleanFilter(method='filter_has_discount')
    
    # Size filters
    size = filters.CharFilter(method='filter_size')
    size_eu = filters.NumberFilter(field_name='variants__size__size_eu')
    size_us = filters.NumberFilter(field_name='variants__size__size_us')
    size_uk = filters.NumberFilter(field_name='variants__size__size_uk')
    
    # Status filters
    is_featured = filters.BooleanFilter(field_name='is_featured')
    is_active = filters.BooleanFilter(field_name='is_active')
    in_stock = filters.BooleanFilter(method='filter_in_stock')
    
    # Delivery filters
    delivery_min = filters.NumberFilter(field_name='shipping_methods__min_days', lookup_expr='gte')
    delivery_max = filters.NumberFilter(field_name='shipping_methods__max_days', lookup_expr='lte')
    
    # Search
    search = filters.CharFilter(method='filter_search')

    class Meta:
        model = Product
        fields = [
            'gender', 'category', 'subcategory', 'brand',
            'price_min', 'price_max', 'has_discount',
            'size', 'size_eu', 'size_us', 'size_uk',
            'is_featured', 'is_active', 'in_stock',
            'delivery_min', 'delivery_max'
        ]

    def filter_has_discount(self, queryset, name, value):
        if value:
            return queryset.filter(discount_price__isnull=False)
        return queryset

    def filter_size(self, queryset, name, value):
        if value:
            return queryset.filter(variants__size__name__iexact=value)
        return queryset

    def filter_in_stock(self, queryset, name, value):
        if value:
            return queryset.filter(variants__stock__gt=0)
        return queryset.filter(variants__stock=0)

    def filter_search(self, queryset, name, value):
        if value:
            return queryset.filter(
                Q(name__icontains=value) |
                Q(description__icontains=value) |
                Q(brand__name__icontains=value) |
                Q(subcategory__name__icontains=value) |
                Q(subcategory__category__name__icontains=value)
            ).distinct()
        return queryset


class UserFilter(filters.FilterSet):
    is_telegram_admin = filters.BooleanFilter(field_name='is_telegram_admin')
    is_telegram_user = filters.BooleanFilter(field_name='is_telegram_user')
    is_verified = filters.BooleanFilter(field_name='is_verified')
    search = filters.CharFilter(method='filter_search')

    class Meta:
        model = User
        fields = ['is_telegram_admin', 'is_telegram_user', 'is_verified']

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(username__icontains=value) |
            Q(telegram_username__icontains=value) |
            Q(first_name__icontains=value) |
            Q(last_name__icontains=value)
        ) 