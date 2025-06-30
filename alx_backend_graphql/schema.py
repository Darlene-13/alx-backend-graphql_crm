import graphene
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
import re

from ..crm.models import Customer, Product, Order
from ..crm.filters import CustomerFilter, ProductFilter, OrderFilter


# GraphQL Types
class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = "__all__"
        filter_fields = ['name', 'email', 'phone']
        interfaces = (graphene.relay.Node, )


class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = "__all__"
        filter_fields = ['name', 'price', 'stock']
        interfaces = (graphene.relay.Node, )


class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = "__all__"
        filter_fields = ['total_amount', 'order_date']
        interfaces = (graphene.relay.Node, )


# Input Types for Filtering
class CustomerFilterInput(graphene.InputObjectType):
    name = graphene.String(description="Filter by customer name (case-insensitive partial match)")
    email = graphene.String(description="Filter by email (case-insensitive partial match)")
    created_at_gte = graphene.DateTime(description="Filter customers created after this date")
    created_at_lte = graphene.DateTime(description="Filter customers created before this date")
    phone_pattern = graphene.String(description="Filter by phone pattern (e.g., '+1' for US numbers)")


class ProductFilterInput(graphene.InputObjectType):
    name = graphene.String(description="Filter by product name (case-insensitive partial match)")
    price_gte = graphene.Decimal(description="Filter products with price >= this value")
    price_lte = graphene.Decimal(description="Filter products with price <= this value")
    stock_gte = graphene.Int(description="Filter products with stock >= this value")
    stock_lte = graphene.Int(description="Filter products with stock <= this value")
    low_stock = graphene.Boolean(description="Filter products with low stock (< 10)")


class OrderFilterInput(graphene.InputObjectType):
    total_amount_gte = graphene.Decimal(description="Filter orders with total amount >= this value")
    total_amount_lte = graphene.Decimal(description="Filter orders with total amount <= this value")
    order_date_gte = graphene.DateTime(description="Filter orders placed after this date")
    order_date_lte = graphene.DateTime(description="Filter orders placed before this date")
    customer_name = graphene.String(description="Filter orders by customer name")
    customer_email = graphene.String(description="Filter orders by customer email")
    product_name = graphene.String(description="Filter orders by product name")
    product_id = graphene.Int(description="Filter orders that include a specific product ID")
    high_value = graphene.Boolean(description="Filter high-value orders (> $500)")


# Input Types for Mutations (keeping existing ones)
class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String()


class ProductInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    price = graphene.Decimal(required=True)
    stock = graphene.Int()


class OrderInput(graphene.InputObjectType):
    customer_id = graphene.ID(required=True)
    product_ids = graphene.List(graphene.ID, required=True)
    order_date = graphene.DateTime()


# Mutation Classes (keeping all existing mutations)
class CreateCustomer(graphene.Mutation):
    class Arguments:
        input = CustomerInput(required=True)
    
    customer = graphene.Field(CustomerType)
    message = graphene.String()
    success = graphene.Boolean()
    
    def mutate(self, info, input):
        try:
            # Validate email uniqueness
            if Customer.objects.filter(email=input.email).exists():
                return CreateCustomer(
                    customer=None,
                    message="Email already exists",
                    success=False
                )
            
            # Validate phone format if provided
            if input.phone:
                phone_pattern = r'^\+?1?-?\d{3}-?\d{3}-?\d{4}$|^\+?\d{10,15}'
                if not re.match(phone_pattern, input.phone):
                    return CreateCustomer(
                        customer=None,
                        message="Phone number must be in format: '+1234567890' or '123-456-7890'",
                        success=False
                    )
            
            # Create customer
            customer = Customer.objects.create(
                name=input.name,
                email=input.email,
                phone=input.phone or None
            )
            
            return CreateCustomer(
                customer=customer,
                message="Customer created successfully",
                success=True
            )
            
        except Exception as e:
            return CreateCustomer(
                customer=None,
                message=f"Error creating customer: {str(e)}",
                success=False
            )


class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        input = graphene.List(CustomerInput, required=True)
    
    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)
    success_count = graphene.Int()
    
    def mutate(self, info, input):
        created_customers = []
        errors = []
        
        with transaction.atomic():
            for i, customer_data in enumerate(input):
                try:
                    # Check email uniqueness
                    if Customer.objects.filter(email=customer_data.email).exists():
                        errors.append(f"Customer {i+1}: Email '{customer_data.email}' already exists")
                        continue
                    
                    # Validate phone if provided
                    if customer_data.phone:
                        phone_pattern = r'^\+?1?-?\d{3}-?\d{3}-?\d{4}$|^\+?\d{10,15}$'
                        if not re.match(phone_pattern, customer_data.phone):
                            errors.append(f"Customer {i+1}: Invalid phone format")
                            continue
                    
                    # Create customer
                    customer = Customer.objects.create(
                        name=customer_data.name,
                        email=customer_data.email,
                        phone=customer_data.phone or None
                    )
                    created_customers.append(customer)
                    
                except Exception as e:
                    errors.append(f"Customer {i+1}: {str(e)}")
        
        return BulkCreateCustomers(
            customers=created_customers,
            errors=errors,
            success_count=len(created_customers)
        )


class CreateProduct(graphene.Mutation):
    class Arguments:
        input = ProductInput(required=True)
    
    product = graphene.Field(ProductType)
    message = graphene.String()
    success = graphene.Boolean()
    
    def mutate(self, info, input):
        try:
            # Validate price is positive
            if input.price <= 0:
                return CreateProduct(
                    product=None,
                    message="Price must be positive",
                    success=False
                )
            
            # Validate stock is not negative
            stock = input.stock if input.stock is not None else 0
            if stock < 0:
                return CreateProduct(
                    product=None,
                    message="Stock cannot be negative",
                    success=False
                )
            
            # Create product
            product = Product.objects.create(
                name=input.name,
                price=input.price,
                stock=stock
            )
            
            return CreateProduct(
                product=product,
                message="Product created successfully",
                success=True
            )
            
        except Exception as e:
            return CreateProduct(
                product=None,
                message=f"Error creating product: {str(e)}",
                success=False
            )


class CreateOrder(graphene.Mutation):
    class Arguments:
        input = OrderInput(required=True)
    
    order = graphene.Field(OrderType)
    message = graphene.String()
    success = graphene.Boolean()
    
    def mutate(self, info, input):
        try:
            # Validate customer exists
            try:
                customer = Customer.objects.get(id=input.customer_id)
            except Customer.DoesNotExist:
                return CreateOrder(
                    order=None,
                    message=f"Customer with ID {input.customer_id} does not exist",
                    success=False
                )
            
            # Validate at least one product is selected
            if not input.product_ids:
                return CreateOrder(
                    order=None,
                    message="At least one product must be selected",
                    success=False
                )
            
            # Validate all products exist
            products = []
            for product_id in input.product_ids:
                try:
                    product = Product.objects.get(id=product_id)
                    products.append(product)
                except Product.DoesNotExist:
                    return CreateOrder(
                        order=None,
                        message=f"Product with ID {product_id} does not exist",
                        success=False
                    )
            
            # Create order with transaction to ensure consistency
            with transaction.atomic():
                order = Order.objects.create(
                    customer=customer,
                    order_date=input.order_date or timezone.now()
                )
                
                # Add products to order
                order.products.set(products)
                
                # Calculate and save total amount
                order.calculate_total()
                order.save(update_fields=['total_amount'])
            
            return CreateOrder(
                order=order,
                message="Order created successfully",
                success=True
            )
            
        except Exception as e:
            return CreateOrder(
                order=None,
                message=f"Error creating order: {str(e)}",
                success=False
            )


# Query Class with Filtering Support
class Query(graphene.ObjectType):
    # Basic queries (existing)
    customers = graphene.List(CustomerType)
    products = graphene.List(ProductType)
    orders = graphene.List(OrderType)
    
    customer = graphene.Field(CustomerType, id=graphene.ID(required=True))
    product = graphene.Field(ProductType, id=graphene.ID(required=True))
    order = graphene.Field(OrderType, id=graphene.ID(required=True))
    
    # Filtered queries with Connection support
    all_customers = DjangoFilterConnectionField(CustomerType, filterset_class=CustomerFilter)
    all_products = DjangoFilterConnectionField(ProductType, filterset_class=ProductFilter)
    all_orders = DjangoFilterConnectionField(OrderType, filterset_class=OrderFilter)
    
    # Custom filtered queries with input types
    filter_customers = graphene.List(
        CustomerType,
        filter=CustomerFilterInput(),
        order_by=graphene.String(description="Order by field (prefix with '-' for descending)")
    )
    
    filter_products = graphene.List(
        ProductType,
        filter=ProductFilterInput(),
        order_by=graphene.String(description="Order by field (prefix with '-' for descending)")
    )
    
    filter_orders = graphene.List(
        OrderType,
        filter=OrderFilterInput(),
        order_by=graphene.String(description="Order by field (prefix with '-' for descending)")
    )
    
    # Basic resolvers
    def resolve_customers(self, info):
        return Customer.objects.all()
    
    def resolve_products(self, info):
        return Product.objects.all()
    
    def resolve_orders(self, info):
        return Order.objects.all().select_related('customer').prefetch_related('products')
    
    def resolve_customer(self, info, id):
        try:
            return Customer.objects.get(id=id)
        except Customer.DoesNotExist:
            return None
    
    def resolve_product(self, info, id):
        try:
            return Product.objects.get(id=id)
        except Product.DoesNotExist:
            return None
    
    def resolve_order(self, info, id):
        try:
            return Order.objects.select_related('customer').prefetch_related('products').get(id=id)
        except Order.DoesNotExist:
            return None
    
    # Custom filtered query resolvers
    def resolve_filter_customers(self, info, filter=None, order_by=None):
        queryset = Customer.objects.all()
        
        if filter:
            # Apply filters using the CustomerFilter
            filter_instance = CustomerFilter(data=filter, queryset=queryset)
            queryset = filter_instance.qs
        
        if order_by:
            queryset = queryset.order_by(order_by)
        
        return queryset
    
    def resolve_filter_products(self, info, filter=None, order_by=None):
        queryset = Product.objects.all()
        
        if filter:
            # Apply filters using the ProductFilter
            filter_instance = ProductFilter(data=filter, queryset=queryset)
            queryset = filter_instance.qs
        
        if order_by:
            queryset = queryset.order_by(order_by)
        
        return queryset
    
    def resolve_filter_orders(self, info, filter=None, order_by=None):
        queryset = Order.objects.all().select_related('customer').prefetch_related('products')
        
        if filter:
            # Apply filters using the OrderFilter
            filter_instance = OrderFilter(data=filter, queryset=queryset)
            queryset = filter_instance.qs
        
        if order_by:
            queryset = queryset.order_by(order_by)
        
        return queryset


# Mutation Class
class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()