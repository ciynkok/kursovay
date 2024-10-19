from django import forms
from .models import OrderCust, OrderCustItem, Invoice, InvoiceItem, OrderSup


class OrderCustForm(forms.ModelForm):
    class Meta:
        model = OrderCust
        fields = '__all__'


class OrderCustItemForm(forms.ModelForm):
    class Meta:
        model = OrderCustItem
        fields = '__all__'


class InvoicesForm(forms.ModelForm):
    order = forms.ModelChoiceField(queryset=OrderSup.objects.all(), label='Заказа поставщика',
                                   widget=forms.Select(attrs={'class': 'form-control py-4'}))

    class Meta:
        model = Invoice
        fields = '__all__'


class InvoiceItemForm(forms.Form):
    price = forms.DecimalField(max_digits=10, decimal_places=2)
