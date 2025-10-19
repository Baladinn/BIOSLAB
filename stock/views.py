from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from .models import Client, Product, Order, OrderItem, Invoice, DeliveryNote
from .forms import ClientForm, ProductForm, OrderForm, OrderItemFormSet
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
import math
from decimal import Decimal


def product_list(request):
    products = Product.objects.all()
    return render(request, 'stock/product_list.html', {'products': products})

def client_create(request):
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Client créé.")
            return redirect('stock:product_list')
    else:
        form = ClientForm()
    return render(request, 'stock/client_form.html', {'form': form})

@transaction.atomic
def order_create(request):
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            formset = OrderItemFormSet(request.POST, instance=order)
            if formset.is_valid():
                order.save()
                formset.save()
                messages.success(request, "Commande créée.")
                return redirect('stock:order_detail', order.id)
    else:
        form = OrderForm(initial={'reference': f"CMD-{Order.objects.count()+1:05d}"})
        formset = OrderItemFormSet()
    return render(request, 'stock/order_create.html', {'form': form, 'formset': formset})

def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk)

    price_ht = order.total()          
    taux_tva = Decimal('0.20')   
    price_ttc = Decimal('0.00')         
    price_ttc = float(price_ht * (Decimal('1.00') + taux_tva)) 

    return render(request, 'stock/order_detail.html', {'order': order,'orderttc': price_ttc})

# def order_detail(request, pk):
#     order = get_object_or_404(Order, id=pk)
#     items = order.orderitem_set.all()  # Récupère tous les produits liés
#     return render(request, 'stock/order_detail.html', {
#         'order': order,
#         'items': items
#     })

def generate_invoice(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    # Création basique de la facture si inexistante
    invoice, created = Invoice.objects.get_or_create(
        order=order,
        defaults={'numero': f"FAC-{order.reference}"}
    )
    price_ht = invoice.total()          
    taux_tva = Decimal('0.20')           
    price_ttc = float(price_ht * (Decimal('1.00') + taux_tva))
    return render(request, 'stock/invoice.html', {'invoice': invoice, 'order': order,'price_ttc':price_ttc })

def generate_delivery_note(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    dn, created = DeliveryNote.objects.get_or_create(
        order=order,
        defaults={'numero': f"BL-{order.reference}"}
    )
    price_ht = order.total()          
    taux_tva = Decimal('0.20')           
    price_ttc = float(price_ht * (Decimal('1.00') + taux_tva))
    return render(request, 'stock/delivery_note.html', {'dn': dn, 'order': order,'price_ttc':price_ttc})







def invoice_pdf(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    # Préparation de la réponse HTTP en PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'filename="facture_{order.id}.pdf"'

    # Création du PDF avec ReportLab
    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    # 🧾 En-tête
    p.setFont("Helvetica-Bold", 16)
    p.drawString(2 * cm, height - 2 * cm, "FACTURE")

    p.setFont("Helvetica", 10)
    p.drawString(2 * cm, height - 3 * cm, f"N° de commande : {order.id}")
    p.drawString(2 * cm, height - 3.5 * cm, f"Date : {order.date.strftime('%d/%m/%Y %H:%M')}")
    p.drawString(2 * cm, height - 4.5 * cm, f"Client : {order.client.name}")
    p.drawString(2 * cm, height - 5 * cm, f"Email : {order.client.email}")
    p.drawString(2 * cm, height - 5.5 * cm, f"Téléphone : {order.client.phone}")
    p.drawString(2 * cm, height - 6 * cm, f"Adresse : {order.client.address}")

    # 🛍 Tableau des produits
    y = height - 7.5 * cm
    p.setFont("Helvetica-Bold", 10)
    p.drawString(2 * cm, y, "Produit")
    p.drawString(9 * cm, y, "PU (MAD)")
    p.drawString(12 * cm, y, "Qté")
    p.drawString(14 * cm, y, "Total HT")
    p.drawString(18 * cm, y, "Total TTC")
    y -= 0.5 * cm

    p.setFont("Helvetica", 10)
    for item in order.orderitem_set.all():
        if y < 2 * cm:  # Saut de page si on atteint le bas
            p.showPage()
            y = height - 3 * cm
            p.setFont("Helvetica", 10)

        p.drawString(2 * cm, y, item.product.name[:25])  # Tronque si trop long
        p.drawRightString(11 * cm, y, f"{item.product.price:.2f}")
        p.drawRightString(13 * cm, y, str(item.quantity))
        p.drawRightString(17 * cm, y, f"{item.get_total():.2f}")
        p.drawString(19 * cm, y, f"{price_ttc:.2f} DH")
        y -= 0.5 * cm

    # 💰 Total général
    y -= 1 * cm
    p.setFont("Helvetica-Bold", 11)
    p.drawRightString(17 * cm, y, f"TOTAL : {order.get_total():.2f} MAD")

    # ✅ Finalisation du PDF
    p.showPage()
    p.save()
    return response


def delivery_note_pdf(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    # Réponse HTTP PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'filename="bon_livraison_{order.id}.pdf"'

    # Création du PDF
    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    # 🚚 En-tête
    p.setFont("Helvetica-Bold", 16)
    p.drawString(2 * cm, height - 2 * cm, "BON DE LIVRAISON")

    p.setFont("Helvetica", 10)
    p.drawString(2 * cm, height - 3 * cm, f"N° de commande : {order.id}")
    p.drawString(2 * cm, height - 3.5 * cm, f"Date : {order.date.strftime('%d/%m/%Y %H:%M')}")
    p.drawString(2 * cm, height - 4.5 * cm, f"Client : {order.client.name}")
    p.drawString(2 * cm, height - 5 * cm, f"Adresse : {order.client.address}")
    p.drawString(2 * cm, height - 5.5 * cm, f"Téléphone : {order.client.phone}")

    # 🧾 Tableau produits
    y = height - 7 * cm
    p.setFont("Helvetica-Bold", 10)
    p.drawString(2 * cm, y, "Produit")
    p.drawRightString(9 * cm, y, "Quantité")
    p.drawRightString(13 * cm, y, "Prix TTC (DH)")
    p.drawRightString(17.5 * cm, y, "Total TTC (DH)")
    y -= 0.5 * cm

    p.setFont("Helvetica", 10)
    total_ttc_commande = Decimal('0.00')
    taux_tva = Decimal('0.20')  # 20% TVA — adapte si besoin

    for item in order.orderitem_set.all():
        if y < 3 * cm:  # saut de page si nécessaire
            p.showPage()
            y = height - 3 * cm
            p.setFont("Helvetica", 10)

        # Calculs TTC
        prix_unitaire_ht = item.product.price
        prix_unitaire_ttc = prix_unitaire_ht * (Decimal('1.00') + taux_tva)
        total_ligne_ttc = prix_unitaire_ttc * item.quantity

        total_ttc_commande += total_ligne_ttc

        # Ligne produit
        p.drawString(2 * cm, y, item.product.name[:35])
        p.drawRightString(9 * cm, y, str(item.quantity))
        p.drawRightString(13 * cm, y, f"{prix_unitaire_ttc:.2f}")
        p.drawRightString(17.5 * cm, y, f"{total_ligne_ttc:.2f}")
        y -= 0.5 * cm

    # 📝 Total TTC en bas
    y -= 1 * cm
    p.setFont("Helvetica-Bold", 11)
    p.drawString(2 * cm, y, "Total TTC de la commande :")
    p.drawRightString(17.5 * cm, y, f"{total_ttc_commande:.2f} DH")

    # ✍️ Zone de signature
    y -= 2 * cm
    p.setFont("Helvetica-Bold", 11)
    p.drawString(2 * cm, y, "Signature Client :")
    p.drawString(10 * cm, y, "Signature Livreurs :")
    y -= 3 * cm
    p.line(2 * cm, y, 8 * cm, y)      # ligne signature client
    p.line(10 * cm, y, 16 * cm, y)    # ligne signature livreur

    # ✅ Finalisation
    p.showPage()
    p.save()
    return response

def order_list(request):
    orders = Order.objects.all().order_by('-date')  # Les plus récentes en premier
    return render(request, 'stock/order_list.html', {'orders': orders})

