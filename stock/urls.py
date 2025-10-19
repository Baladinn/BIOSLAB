from django.urls import path
from . import views

app_name = 'stock'

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('client/new/', views.client_create, name='client_create'),
    path('order/new/', views.order_create, name='order_create'),
    path('order/<int:pk>/', views.order_detail, name='order_detail'),
    path('order/<int:order_id>/invoice/', views.generate_invoice, name='generate_invoice'),
    path('order/<int:order_id>/delivery-note/', views.generate_delivery_note, name='generate_delivery_note'),
    path('order/<int:order_id>/invoice/', views.invoice_pdf, name='invoice_pdf'),
    path('order/<int:order_id>/delivery-note/', views.delivery_note_pdf, name='delivery_note_pdf'),
    path('orders/', views.order_list, name='order_list'),

]
