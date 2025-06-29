import graphene
from graphene_django import DjangoObjectType
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
import re

from .models import Customer, Product, Order


# GraphQL Types
class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = "__all__"


class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = "__all__"


class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = "__all__"


# Input Types
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


# Mutation Classes
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
                phone_pattern = r'^\+?1?-?\d{3}-?\d{3}-?\d{4}$|^\+?\d{10,15}$'
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


# Query Class
class Query(graphene.ObjectType):
    customers = graphene.List(CustomerType)
    products = graphene.List(ProductType)
    orders = graphene.List(OrderType)
    
    customer = graphene.Field(CustomerType, id=graphene.ID(required=True))
    product = graphene.Field(ProductType, id=graphene.ID(required=True))
    order = graphene.Field(OrderType, id=graphene.ID(required=True))
    
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


# Mutation Class
class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()