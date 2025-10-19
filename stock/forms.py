from django import forms
from .models import Client, Product, Order, OrderItem

class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['nom', 'adresse', 'telephone', 'email']

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['reference', 'nom', 'description', 'prix_unitaire', 'quantite_stock']

class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ['product', 'quantite', 'prix_unitaire']

OrderItemFormSet = forms.inlineformset_factory(
    Order, OrderItem, form=OrderItemForm,
    fields=['product','quantite','prix_unitaire'], extra=1, can_delete=True
)

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['client', 'reference', 'note']
