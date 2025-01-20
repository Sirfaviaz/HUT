from django.shortcuts import render, redirect
from .forms import ProductForm
from django.contrib.auth.decorators import login_required

from decimal import Decimal

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Store, Stock, Invoice, Supplier, InvoiceItem

@login_required
def dashboard(request):
    """Dashboard for the logged-in user's store."""
    # Get the store associated with the logged-in user
    try:
        store = Store.objects.get(user=request.user)
    except Store.DoesNotExist:
        store = None

    # Fetch data to display on the dashboard
    recent_purchases = Invoice.objects.filter(store=store, transaction_type='purchase').order_by('-date')[:5]
    suppliers = Supplier.objects.all()
    stock_items = Stock.objects.filter(store=store).order_by('product__name_english')

    context = {
        'store': store,
        'recent_purchases': recent_purchases,
        'suppliers': suppliers,
        'stock_items': stock_items,
    }
    return render(request, 'home/dashboard.html', context)


from django.http import JsonResponse
from django.db.models import Q
from .models import Product

def search_products(request):
    """Search for products by name."""
    query = request.GET.get('query', '').strip()

    if len(query) < 2:  # Prevent short queries
        return JsonResponse({'results': []})

    try:
        products = Product.objects.filter(name_english__icontains=query)[:10]  # Limit results to 10
        results = [
            {
                'id': product.id,
                'name_english': product.name_english,
                'arabic_name': product.name_arabic,
                'description_english': product.description_english,
                'description_arabic': product.description_arabic,
                'price': str(product.price),
                'image_url': product.image.url if product.image else '/static/default-product.png',
            }
            for product in products
        ]
        return JsonResponse({'results': results})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product updated successfully.')
            return redirect('view_stock')  # Redirect back to stock overview
    else:
        form = ProductForm(instance=product)
    return render(request, 'home/edit_product.html', {'form': form, 'product': product})




@login_required
def view_stock(request):
    """View to display current stock with purchase price and selling price."""
    user_store = Store.objects.get(user=request.user)
    stock_items = Stock.objects.filter(store=user_store).order_by('product__name_english')

    # Fetch related invoice items for cost price
    stock_with_prices = []
    for stock_item in stock_items:
        # Get the latest invoice item for cost price (if multiple purchases of the same product)
        latest_invoice_item = (
            InvoiceItem.objects.filter(product=stock_item.product)
            .order_by('-invoice__date')
            .first()
        )
        stock_with_prices.append({
            'stock': stock_item,
            'cost_price': latest_invoice_item.price_per_unit if latest_invoice_item else None,
            'selling_price': stock_item.product.price
        })

    return render(request, 'home/view_stock.html', {'stock_with_prices': stock_with_prices})

@login_required
def recent_purchases(request):
    """View to display recent purchases."""
    user_store = Store.objects.get(user=request.user)
    recent_purchases = Invoice.objects.filter(store=user_store, transaction_type='purchase').order_by('-date')
    return render(request, 'home/recent_purchases.html', {'recent_purchases': recent_purchases})



@login_required
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('product_success')  # Redirect to a success page
    else:
        form = ProductForm()
    return render(request, 'home/add_product.html', {'form': form})

def product_success(request):
    return render(request, 'home/product_success.html')


@login_required
def existing_entries(request):
    """View to list all unfinished invoices."""
    user_store = Store.objects.get(user=request.user)
    invoices = Invoice.objects.filter(store=user_store, status='draft').order_by('-date')

    return render(request, 'home/existing_entries.html', {'invoices': invoices})

@login_required
def new_invoice(request):
    """View to create a new invoice."""
    user_store = Store.objects.get(user=request.user)
    suppliers = Supplier.objects.all()

    if request.method == 'POST':
        supplier_id = request.POST.get('supplier')
        reference = request.POST.get('reference')
        supplier = Supplier.objects.get(id=supplier_id)

        invoice = Invoice.objects.create(
            store=user_store,
            supplier=supplier,
            reference=reference,
        )
        return redirect('add_product_to_invoice', invoice.id)

    return render(request, 'home/new_invoice.html', {'suppliers': suppliers})

from decimal import Decimal
from django.db.models import F
from django.shortcuts import get_object_or_404, redirect, render
from .models import Invoice, InvoiceItem, Product, Stock
from .forms import ProductForm
from django.contrib.auth.decorators import login_required


@login_required
def add_product_to_invoice(request, invoice_id):
    """View to add products to an existing invoice, update stock, and set transaction type."""
    # Get the invoice with draft status
    invoice = get_object_or_404(Invoice, id=invoice_id, status='draft')

    # Ensure the invoice transaction type is 'purchase'
    if invoice.transaction_type != 'purchase':
        invoice.transaction_type = 'purchase'
        invoice.save()

    user_store = invoice.store  # Get the store linked to the invoice

    if request.method == 'POST':
        product_id = request.POST.get('existing_product_id')
        product = None  # Initialize product variable
        
        if product_id:
            try:
                product = Product.objects.get(id=product_id)
            except Product.DoesNotExist:
                return JsonResponse({'error': 'Selected product does not exist'}, status=400)
        else:
            form = ProductForm(request.POST, request.FILES)
            if form.is_valid():
                product = form.save()
            else:
                invoice_items = InvoiceItem.objects.filter(invoice=invoice)
                return render(request, 'home/add_product_to_invoice.html', {
                    'invoice': invoice,
                    'form': form,
                    'invoice_items': invoice_items,
                })

        # Retrieve quantity and price per unit
        try:
            quantity = int(request.POST.get('quantity', 0))
            price_per_unit = Decimal(request.POST.get('price_per_unit', 0))
        except (ValueError, Decimal.InvalidOperation):
            return JsonResponse({'error': 'Invalid quantity or price per unit'}, status=400)

        # Check if the product is already in the invoice
        invoice_item, created = InvoiceItem.objects.get_or_create(
            invoice=invoice,
            product=product,
            defaults={'quantity': quantity, 'price_per_unit': price_per_unit},
        )

        if not created:
            # Update the existing invoice item
            invoice_item.quantity += quantity
            invoice_item.price_per_unit = price_per_unit
            invoice_item.save()

        # Update stock for the product in the current store
        stock, created = Stock.objects.get_or_create(
            store=user_store,
            product=product,
            defaults={'quantity': 0}
        )
        stock.quantity = F('quantity') + quantity
        stock.save()

        # Update the invoice total
        invoice.total_amount += quantity * price_per_unit
        invoice.save()

        return redirect('add_product_to_invoice', invoice_id)

    else:
        form = ProductForm()

    invoice_items = InvoiceItem.objects.filter(invoice=invoice)
    return render(request, 'home/add_product_to_invoice.html', {
        'invoice': invoice,
        'form': form,
        'invoice_items': invoice_items,
    })



from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

@login_required
def change_invoice_status(request, invoice_id):
    """View to change the status of an invoice."""
    invoice = get_object_or_404(Invoice, id=invoice_id)
    if request.method == 'POST':
        if invoice.status == 'draft':
            invoice.status = 'finalized'
            invoice.save()
            messages.success(request, f"Invoice {invoice.reference} has been finalized.")
        else:
            messages.warning(request, "Invoice is already finalized.")

    # Redirect to the dashboard after success
    return redirect('dashboard')  # Replace 'dashboard' with the name of your dashboard URL pattern




from django.shortcuts import redirect
from django.contrib import messages

@login_required
def add_supplier(request):
    """View to handle adding a new supplier."""
    if request.method == 'POST':
        name = request.POST.get('name')
        contact_number = request.POST.get('contact_number')
        email = request.POST.get('email')
        address = request.POST.get('address')

        # Create a new supplier
        Supplier.objects.create(
            name=name,
            contact_number=contact_number,
            email=email,
            address=address,
        )
        messages.success(request, "Supplier added successfully!")
        return redirect('new_invoice')  # Redirect back to the create invoice page
    return redirect('dashboard')


import os
import google.generativeai as genai
from django.http import JsonResponse
from decouple import config

# Configure the API key from environment or .env file
gemini_api_key = config("GEMINI_API_KEY")  # Ensure GEMINI_API_KEY is defined in .env
genai.configure(api_key=gemini_api_key)

def translate_text_api(request):
    """Translate English text to Arabic using Google's Gemini API."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=400)

    text = request.POST.get('text', '').strip()
    if not text:
        return JsonResponse({'error': 'No text provided'}, status=400)

    try:
        # Debug: Log the text being translated and API key usage
        print(f"Translating text: {text}")
        print(f"Using Gemini API key: {gemini_api_key}")

        # Initialize the generative model
        model = genai.GenerativeModel("gemini-1.5-flash")  # Replace with the actual model if different

        # Create the translation prompt
        prompt = f"Translate the following English text to Arabic (Qatar), it is required to put in a ecommerce platform make it in market centric. Response should be just the arabic translation: {text}"

        # Generate the translation
        response = model.generate_content(prompt)

        # Debug: Log the API response
        print(f"Gemini API response: {response}")

        # Extract and return the translated text
        if response and hasattr(response, 'text'):
            translated_text = response.text.strip()
            return JsonResponse({'translatedText': translated_text})
        else:
            return JsonResponse({'error': 'Failed to generate translation from Gemini API'}, status=500)

    except Exception as e:
        # Debug: Log the exception
        print(f"Error during translation: {str(e)}")
        return JsonResponse({'error': f'Unexpected error: {str(e)}'}, status=500)
