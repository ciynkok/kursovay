from django.db import models
from django.contrib.auth.models import User
from datetime import datetime

# Create your models here.


class OrderCust(models.Model):
    date = models.DateTimeField(default=datetime.now())
    customer = models.ForeignKey(to=User, on_delete=models.CASCADE, default=None)
    customer_name = models.CharField(max_length=100)
    customer_phone = models.CharField(max_length=20)
    car = models.CharField(max_length=100)
    prepayment = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_time = models.DateTimeField()
    type_sale = models.CharField(default='Наличный расчёт', max_length=100)

    def __str__(self):
        return f"Заказ для {self.customer_name}"


class SparePart(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.name


class Supplier(models.Model):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    email = models.EmailField()

    def __str__(self):
        return self.name


class OrderCustItem(models.Model):
    order = models.ForeignKey(OrderCust, on_delete=models.CASCADE, related_name='items')
    spare_part = models.ForeignKey(SparePart, on_delete=models.CASCADE)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.spare_part.name}"


class OrderSup(models.Model):
    date = models.DateTimeField(default=datetime.now())
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)

    def __str__(self):
        return f"Заказ для {self.supplier}"


class OrderSupItem(models.Model):
    order = models.ForeignKey(OrderSup, on_delete=models.CASCADE, related_name='items')
    spare_part = models.ForeignKey(SparePart, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.quantity} x {self.spare_part.name}"


class Invoice(models.Model):
    date = models.DateTimeField(default=datetime.now())
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)

    def __str__(self):
        return f"Накладная для {self.supplier}"


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    spare_part = models.ForeignKey(SparePart, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    sum_of = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.spare_part.name}"


