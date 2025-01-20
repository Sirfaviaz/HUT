from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
urlpatterns = [
    path('add-product/', views.add_product, name='add_product'),
    path('success/', views.product_success, name='product_success'),
    path('translate/', views.translate_text_api, name='translate_text_api'),
    path('login/', auth_views.LoginView.as_view(template_name='home/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('', views.dashboard, name='dashboard'),
    path('view-stock/', views.view_stock, name='view_stock'), 
    path('recent-purchases/', views.recent_purchases, name='recent_purchases'),
    path('existing-entries/', views.existing_entries, name='existing_entries'),
    path('new-invoice/', views.new_invoice, name='new_invoice'),
    path('add-product-to-invoice/<int:invoice_id>/', views.add_product_to_invoice, name='add_product_to_invoice'),
    path('add-supplier/', views.add_supplier, name='add_supplier'),
    path('change-invoice-status/<int:invoice_id>/', views.change_invoice_status, name='change_invoice_status'),
    path('search-products/', views.search_products, name='search_products'),
    path('edit-product/<int:product_id>/',views.edit_product, name = "edit_product"),
]
