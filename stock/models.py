from django.db import models
from django.utils import timezone
from django.urls import reverse

class Client(models.Model):
    nom = models.CharField(max_length=200)
    adresse = models.TextField(blank=True)
    telephone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
    #     return f"{self.nom}"
        return f"{self.nom} - {self.telephone} ({self.email})"

class Product(models.Model):
    reference = models.CharField(max_length=50, unique=True)
    nom = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2)
    quantite_stock = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Produit"
    def __str__(self):
        return f"{self.reference} - {self.nom} - {self.description}   -  Quantite_stock: {self.quantite_stock}"
    


class Order(models.Model):
    """
    Représente une commande client (peut être convertie en facture/BL)
    """
    client = models.ForeignKey(Client, on_delete=models.PROTECT, related_name="orders")
    date = models.DateTimeField(default=timezone.now)
    reference = models.CharField(max_length=100, unique=True)
    validated = models.BooleanField(default=False)  # Si validée -> reduction stock et possible génération facture
    note = models.TextField(blank=True)


    class Meta:
        verbose_name = "Commande"
    def __str__(self):
        return f"Commande {self.reference} - {self.client.nom}"

    def total(self):
        return sum(item.subtotal() for item in self.items.all())

    def get_absolute_url(self):
        return reverse('stock:order_detail', args=[self.pk])

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantite = models.PositiveIntegerField()
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2)

    def subtotal(self):
        return self.quantite * self.prix_unitaire

    def __str__(self):
        return f"{self.product.nom} x {self.quantite}"

class Invoice(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="invoice")
    numero = models.CharField(max_length=100, unique=True)
    date = models.DateTimeField(default=timezone.now)
    paid = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Facture"
    def total(self):
        return self.order.total()

    def __str__(self):
        return f"Facture {self.numero} pour {self.order.reference}"

class DeliveryNote(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="delivery_note")
    numero = models.CharField(max_length=100, unique=True)
    date = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Bon de livraison"

    def __str__(self):
        return f"BL {self.numero} pour {self.order.reference}"




