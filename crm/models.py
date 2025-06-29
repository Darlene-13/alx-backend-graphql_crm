from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
from decimal import Decimal


class Customer(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        validators=[
            RegexValidator(
                regex=r'^\+?1?-?\d{3}-?\d{3}-?\d{4}$|^\+?\d{10,15}$',
                message="Phone number must be in format: '+1234567890' or '123-456-7890'"
            )
        ]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.email})"


class Product(models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def clean(self):
        if self.price <= 0:
            raise ValueError("Price must be positive")
    
    def __str__(self):
        return f"{self.name} - ${self.price}"


class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='orders')
    products = models.ManyToManyField(Product, related_name='orders')
    order_date = models.DateTimeField(default=timezone.now)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    created_at = models.DateTimeField(auto_now_add=True)
    
    def calculate_total(self):
        """Calculate total amount based on associated products"""
        total = sum(product.price for product in self.products.all())
        self.total_amount = total
        return total
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.pk:  # Only calculate after initial save
            self.calculate_total()
            super().save(update_fields=['total_amount'])
    
    def __str__(self):
        return f"Order {self.id} - {self.customer.name} - ${self.total_amount}"