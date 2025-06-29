#!/usr/bin/env python
"""
Database seeding script for CRM GraphQL project
Run this with: python seed_db.py
Make sure to run from the directory containing manage.py
"""

import os
import sys
import django
from decimal import Decimal

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alx_backend_graphql_crm.settings')
django.setup()

from crm.models import Customer, Product, Order


def seed_customers():
    """Create sample customers"""
    customers_data = [
        {"name": "John Doe", "email": "john@example.com", "phone": "+1234567890"},
        {"name": "Jane Smith", "email": "jane@example.com", "phone": "123-456-7890"},
        {"name": "Bob Johnson", "email": "bob@example.com", "phone": None},
        {"name": "Alice Williams", "email": "alice@example.com", "phone": "+9876543210"},
        {"name": "Charlie Brown", "email": "charlie@example.com", "phone": "987-654-3210"},
    ]
    
    created_customers = []
    for customer_data in customers_data:
        customer, created = Customer.objects.get_or_create(
            email=customer_data["email"],
            defaults=customer_data
        )
        if created:
            created_customers.append(customer)
            print(f"Created customer: {customer.name}")
        else:
            print(f"Customer already exists: {customer.name}")
    
    return created_customers


def seed_products():
    """Create sample products"""
    products_data = [
        {"name": "Laptop", "price": Decimal("999.99"), "stock": 10},
        {"name": "Mouse", "price": Decimal("25.50"), "stock": 50},
        {"name": "Keyboard", "price": Decimal("75.00"), "stock": 30},
        {"name": "Monitor", "price": Decimal("299.99"), "stock": 15},
        {"name": "Headphones", "price": Decimal("89.99"), "stock": 25},
        {"name": "Webcam", "price": Decimal("65.00"), "stock": 20},
    ]
    
    created_products = []
    for product_data in products_data:
        product, created = Product.objects.get_or_create(
            name=product_data["name"],
            defaults=product_data
        )
        if created:
            created_products.append(product)
            print(f"Created product: {product.name} - ${product.price}")
        else:
            print(f"Product already exists: {product.name}")
    
    return created_products


def seed_orders():
    """Create sample orders"""
    customers = Customer.objects.all()
    products = Product.objects.all()
    
    if not customers.exists() or not products.exists():
        print("No customers or products found. Please seed customers and products first.")
        return []
    
    # Create some sample orders
    created_orders = []
    
    # Order 1: John buys laptop and mouse
    if customers.filter(name="John Doe").exists() and products.filter(name__in=["Laptop", "Mouse"]).exists():
        john = customers.get(name="John Doe")
        order1 = Order.objects.create(customer=john)
        order1.products.set(products.filter(name__in=["Laptop", "Mouse"]))
        order1.calculate_total()
        order1.save()
        created_orders.append(order1)
        print(f"Created order for {john.name}: ${order1.total_amount}")
    
    # Order 2: Jane buys keyboard and headphones
    if customers.filter(name="Jane Smith").exists() and products.filter(name__in=["Keyboard", "Headphones"]).exists():
        jane = customers.get(name="Jane Smith")
        order2 = Order.objects.create(customer=jane)
        order2.products.set(products.filter(name__in=["Keyboard", "Headphones"]))
        order2.calculate_total()
        order2.save()
        created_orders.append(order2)
        print(f"Created order for {jane.name}: ${order2.total_amount}")
    
    return created_orders


def main():
    """Main seeding function"""
    print("Starting database seeding...")
    
    print("\n--- Seeding Customers ---")
    customers = seed_customers()
    
    print("\n--- Seeding Products ---")
    products = seed_products()
    
    print("\n--- Seeding Orders ---")
    orders = seed_orders()
    
    print(f"\n--- Seeding Complete ---")
    print(f"Created {len(customers)} new customers")
    print(f"Created {len(products)} new products") 
    print(f"Created {len(orders)} new orders")
    
    print(f"\nTotal in database:")
    print(f"Customers: {Customer.objects.count()}")
    print(f"Products: {Product.objects.count()}")
    print(f"Orders: {Order.objects.count()}")


if __name__ == "__main__":
    main()