from django.contrib import admin
from .models import Product, Store, Supplier, Stock, VanStock, Invoice, InvoiceItem

admin.site.register(Product)
admin.site.register(Supplier)
admin.site.register(Store)
admin.site.register(Stock)
admin.site.register(VanStock)
admin.site.register(Invoice)
admin.site.register(InvoiceItem)
