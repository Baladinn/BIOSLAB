from django.contrib import admin
from .models import Client, Product, Order, OrderItem, Invoice, DeliveryNote
from django.contrib.auth.models import Group, User

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('reference', 'client', 'date', 'validated')
    inlines = [OrderItemInline]
    actions = ['validate_orders']

    def validate_orders(self, request, queryset):
        # validation simple: décrémente stock et coche validated
        for order in queryset:
            if order.validated:
                continue
            for item in order.items.all():
                product = item.product
                if product.quantite_stock < item.quantite:
                    self.message_user(request, f"Stock insuffisant pour {product}")
                    break
            else:
                # tout ok -> décrémente
                for item in order.items.all():
                    p = item.product
                    p.quantite_stock -= item.quantite
                    p.save()
                order.validated = True
                order.save()
        self.message_user(request, "Opération de validation terminée.")
    validate_orders.short_description = "Valider les commandes sélectionnées (maj stock)"

admin.site.register(Client)
admin.site.register(Product)
admin.site.register(Invoice)
admin.site.register(DeliveryNote)

admin.site.unregister(Group)
admin.site.unregister(User)
