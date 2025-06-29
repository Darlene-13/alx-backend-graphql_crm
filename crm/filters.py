import django_filters
from django.db.models import Q, Count
from .models import Customer, Product, Order


class CustomerFilter(django_filters.FilterSet):
    """Filter for Customer model with comprehensive search capabilities"""
    
    # Name filtering - case-insensitive partial match
    name = django_filters.CharFilter(
        field_name='name',
        lookup_expr='icontains',
        help_text="Filter by customer name (case-insensitive partial match)"
    )
    
    # Email filtering - case-insensitive partial match
    email = django_filters.CharFilter(
        field_name='email',
        lookup_expr='icontains',
        help_text="Filter by email (case-insensitive partial match)"
    )
    
    # Date range filtering
    created_at_gte = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='gte',
        help_text="Filter customers created after this date"
    )
    
    created_at_lte = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='lte',
        help_text="Filter customers created before this date"
    )
    
    # Custom phone pattern filter
    phone_pattern = django_filters.CharFilter(
        method='filter_phone_pattern',
        help_text="Filter by phone pattern (e.g., '+1' for US numbers)"
    )
    
    def filter_phone_pattern(self, queryset, name, value):
        """Custom filter for phone number patterns"""
        if value:
            return queryset.filter(phone__icontains=value)
        return queryset
    
    class Meta:
        model = Customer
        fields = ['name', 'email', 'created_at_gte', 'created_at_lte', 'phone_pattern']


class ProductFilter(django_filters.FilterSet):
    """Filter for Product model with price and stock filtering"""
    
    # Name filtering - case-insensitive partial match
    name = django_filters.CharFilter(
        field_name='name',
        lookup_expr='icontains',
        help_text="Filter by product name (case-insensitive partial match)"
    )
    
    # Price range filtering
    price_gte = django_filters.NumberFilter(
        field_name='price',
        lookup_expr='gte',
        help_text="Filter products with price greater than or equal to this value"
    )
    
    price_lte = django_filters.NumberFilter(
        field_name='price',
        lookup_expr='lte',
        help_text="Filter products with price less than or equal to this value"
    )
    
    # Stock filtering
    stock = django_filters.NumberFilter(
        field_name='stock',
        lookup_expr='exact',
        help_text="Filter by exact stock amount"
    )
    
    stock_gte = django_filters.NumberFilter(
        field_name='stock',
        lookup_expr='gte',
        help_text="Filter products with stock greater than or equal to this value"
    )
    
    stock_lte = django_filters.NumberFilter(
        field_name='stock',
        lookup_expr='lte',
        help_text="Filter products with stock less than or equal to this value"
    )
    
    # Low stock filter (custom method)
    low_stock = django_filters.BooleanFilter(
        method='filter_low_stock',
        help_text="Filter products with low stock (less than 10)"
    )
    
    def filter_low_stock(self, queryset, name, value):
        """Custom filter for low stock products"""
        if value:
            return queryset.filter(stock__lt=10)
        return queryset
    
    class Meta:
        model = Product
        fields = ['name', 'price_gte', 'price_lte', 'stock', 'stock_gte', 'stock_lte', 'low_stock']


class OrderFilter(django_filters.FilterSet):
    """Filter for Order model with comprehensive filtering including related fields"""
    
    # Total amount range filtering
    total_amount_gte = django_filters.NumberFilter(
        field_name='total_amount',
        lookup_expr='gte',
        help_text="Filter orders with total amount greater than or equal to this value"
    )
    
    total_amount_lte = django_filters.NumberFilter(
        field_name='total_amount',
        lookup_expr='lte',
        help_text="Filter orders with total amount less than or equal to this value"
    )
    
    # Order date range filtering
    order_date_gte = django_filters.DateTimeFilter(
        field_name='order_date',
        lookup_expr='gte',
        help_text="Filter orders placed after this date"
    )
    
    order_date_lte = django_filters.DateTimeFilter(
        field_name='order_date',
        lookup_expr='lte',
        help_text="Filter orders placed before this date"
    )
    
    # Customer name filtering (related field lookup)
    customer_name = django_filters.CharFilter(
        field_name='customer__name',
        lookup_expr='icontains',
        help_text="Filter orders by customer name (case-insensitive partial match)"
    )
    
    # Customer email filtering (related field lookup)
    customer_email = django_filters.CharFilter(
        field_name='customer__email',
        lookup_expr='icontains',
        help_text="Filter orders by customer email (case-insensitive partial match)"
    )
    
    # Product name filtering (related field lookup through many-to-many)
    product_name = django_filters.CharFilter(
        field_name='products__name',
        lookup_expr='icontains',
        help_text="Filter orders by product name (case-insensitive partial match)"
    )
    
    # Specific product ID filter
    product_id = django_filters.NumberFilter(
        field_name='products__id',
        lookup_expr='exact',
        help_text="Filter orders that include a specific product ID"
    )
    
    # Custom filter for orders with specific number of products
    product_count = django_filters.NumberFilter(
        method='filter_product_count',
        help_text="Filter orders with specific number of products"
    )
    
    # Custom filter for high-value orders
    high_value = django_filters.BooleanFilter(
        method='filter_high_value',
        help_text="Filter high-value orders (total amount > 500)"
    )
    
    def filter_product_count(self, queryset, name, value):
        """Custom filter for orders with specific number of products"""
        if value:
            return queryset.annotate(
                product_count=Count('products')
            ).filter(product_count=value)
        return queryset
    
    def filter_high_value(self, queryset, name, value):
        """Custom filter for high-value orders"""
        if value:
            return queryset.filter(total_amount__gt=500)
        return queryset
    
    class Meta:
        model = Order
        fields = [
            'total_amount_gte', 'total_amount_lte',
            'order_date_gte', 'order_date_lte',
            'customer_name', 'customer_email',
            'product_name', 'product_id',
            'product_count', 'high_value'
        ]