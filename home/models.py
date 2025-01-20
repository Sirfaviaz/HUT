from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now

class Supplier(models.Model):
    """Model to store supplier details."""
    name = models.CharField(max_length=255)
    contact_number = models.CharField(max_length=20)
    email = models.EmailField()
    address = models.TextField()

    def __str__(self):
        return self.name


class Product(models.Model):
    """Model to store product details with timestamps."""
    name_english = models.CharField(max_length=255)
    name_arabic = models.CharField(max_length=255, blank=True, null=True)
    description_english = models.TextField()
    description_arabic = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    created_at = models.DateTimeField(default=now)  # Add default for existing rows
    updated_at = models.DateTimeField(default=now)
    def __str__(self):
        return self.name_english


class Store(models.Model):
    """Model to represent a store or warehouse."""
    name = models.CharField(max_length=255)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='store')
    address = models.TextField()

    def __str__(self):
        return self.name


class Van(models.Model):
    """Model to represent sales vans."""
    name = models.CharField(max_length=255)
    driver = models.OneToOneField(User, on_delete=models.CASCADE, related_name='van')
    capacity = models.PositiveIntegerField(help_text="Capacity in terms of number of products or weight, e.g., 100kg")
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} - {self.driver.username}"


class Stock(models.Model):
    """Model to track stock in a store or warehouse."""
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='stocks')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stocks')
    quantity = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('store', 'product')  # Ensures each store has one stock entry per product

    def __str__(self):
        return f"{self.store.name} - {self.product.name_english}: {self.quantity} in stock"


class VanStock(models.Model):
    """Model to track stock in sales vans."""
    van = models.ForeignKey(Van, on_delete=models.CASCADE, related_name='stocks')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='van_stocks')
    quantity = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('van', 'product')  # Ensures each van has one stock entry per product

    def __str__(self):
        return f"{self.van.name} - {self.product.name_english}: {self.quantity} in stock"


class StockTransfer(models.Model):
    """Model to track stock transfers between locations."""
    from_store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='outgoing_transfers', null=True, blank=True)
    to_store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='incoming_transfers', null=True, blank=True)
    from_van = models.ForeignKey(Van, on_delete=models.CASCADE, related_name='outgoing_transfers', null=True, blank=True)
    to_van = models.ForeignKey(Van, on_delete=models.CASCADE, related_name='incoming_transfers', null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='transfers')
    quantity = models.PositiveIntegerField()
    transfer_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Transfer {self.product.name_english} - {self.quantity} units"


class Invoice(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('finalized', 'Finalized'),
    ]

    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='invoices')
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='invoices', blank=True, null=True)
    transaction_type = models.CharField(
        max_length=20,
        choices=(('purchase', 'Purchase'), ('sale', 'Sale'))
    )
    date = models.DateField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    reference = models.CharField(max_length=255, unique=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')

    def __str__(self):
        return f"Invoice {self.reference} - {self.transaction_type}"

class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='invoice_items')
    quantity = models.PositiveIntegerField()
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.invoice.reference} - {self.product.name_english} ({self.quantity})"


class VanSale(models.Model):
    """Model to track sales directly from a van."""
    van = models.ForeignKey(Van, on_delete=models.CASCADE, related_name='sales')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='van_sales')
    quantity = models.PositiveIntegerField()
    sale_date = models.DateTimeField(auto_now_add=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Sale from {self.van.name} - {self.product.name_english} ({self.quantity})"
