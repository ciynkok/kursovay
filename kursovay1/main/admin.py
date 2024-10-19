from django.contrib import admin
from .models import OrderCust, OrderCustItem, OrderSup, OrderSupItem, SparePart, Supplier, Invoice, InvoiceItem

# Register your models here.

admin.site.register(OrderCust)
admin.site.register(OrderSup)
admin.site.register(OrderCustItem)
admin.site.register(OrderSupItem)
admin.site.register(SparePart)
admin.site.register(Supplier)
admin.site.register(Invoice)
admin.site.register(InvoiceItem)
