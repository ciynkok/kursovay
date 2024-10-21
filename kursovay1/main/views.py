from django.shortcuts import render, redirect, HttpResponseRedirect, get_object_or_404
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login, logout
from .models import OrderCust, OrderCustItem, OrderSup, OrderSupItem, Supplier, SparePart, Invoice, InvoiceItem
from django.urls import reverse
from .forms import OrderCustForm, OrderCustItemForm, InvoiceItemForm, InvoicesForm
from django.db.models import Sum, Q, Count
from datetime import datetime, date
from rest_framework.views import APIView
from rest_framework.response import Response
from weasyprint import HTML
from django.http import HttpResponse
from django.http import HttpResponse
from django.template import loader
import weasyprint


# Create your views here.


def index(request):
    error = ''
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('main/')
        else:
            error = 'Ошибка'
    else:
        form = AuthenticationForm()

    context = {'form': form,
               'error': error,
               'title': 'Авторизация'
               }
    return render(request, 'main/index.html', context)


def main(request):
    user = request.user
    orders = OrderCust.objects.filter(customer=user)
    context = {'title': 'Главная',
               'staff': request.user.is_staff,
               'orders': orders,
               'user': user,
               }
    return render(request, 'main/main.html', context)


def order_cust_type(request, order_id):
    user = request.user
    ordercust = get_object_or_404(OrderCust, pk=order_id)
    if request.method == 'POST':
        type_sale = request.POST['calculation']
        OrderCust.objects.filter(id=ordercust.id).update(type_sale=type_sale)
        return HttpResponseRedirect(reverse('main:main'))

    context = {'title': 'Главная',
               'staff': request.user.is_staff,
               'ordercust': ordercust}
    return render(request, 'main/create_order_type.html', context)


def workspace(request):
    return render(request, 'main/workspace.html', {'x':
                                                       Invoice.objects.values('supplier', 'items__spare_part').annotate(sum_of_=Sum('items__sum_of'))})


def create_order_sup(request):
    m = []
    today = date.today()
    order_cust = OrderCust.objects.filter(Q(date__gte=datetime(today.year, today.month, today.day, 0, 0, 0))
                                          & Q(date__lte=datetime(today.year, today.month, today.day + 1, 0, 0, 0)))
    for ord in order_cust:
        m.append(ord)
    orders_sup = OrderCustItem.objects.filter(order__in=m).values('supplier').annotate(Sum('quantity'))
    suppliers = Supplier.objects.all()
    for order in orders_sup:
        o = OrderSup.objects.get_or_create(
            supplier=suppliers.get(Q(id=order['supplier'])) & Q(date__gte=datetime(today.year, today.month, today.day, 0, 0, 0))
                                        & Q(date__lte=datetime(today.year, today.month, today.day + 1, 0, 0, 0)))[0]
        items = OrderCustItem.objects.filter(supplier=suppliers.get(id=order['supplier'])).values('spare_part').annotate(sum_quantity=Sum('quantity'))
        for item in items:
            sup_item = OrderSupItem(order=o, spare_part=SparePart.objects.get(id=item['spare_part']), quantity=item['sum_quantity'])
            if OrderSupItem.objects.filter(order=o, spare_part=SparePart.objects.get(id=item['spare_part'])).exists():
                OrderSupItem.objects.filter(order=o, spare_part=SparePart.objects.get(id=item['spare_part'])).update(quantity=item['sum_quantity'])
            else:
                sup_item.save()
    return HttpResponseRedirect(reverse('main:workspace'))


def invoices(request):
    error = ''
    if request.method == 'POST':
        form = InvoicesForm(data=request.POST)
        if form.is_valid():
            form.save()
            order_sup = OrderSup.objects.get(id=request.POST['order'])
            items = OrderSupItem.objects.filter(order=order_sup)
            supplier = Supplier.objects.get(id=request.POST['supplier'])
            invoice = Invoice.objects.filter(date=request.POST['date'], supplier=supplier).first()
            for item in items:
                InvoiceItem(invoice=invoice, spare_part=item.spare_part, quantity=item.quantity, price=0, sum_of=0).save()
            return HttpResponseRedirect(reverse('main:invoices'))
        else:
            error = 'Ошибка'
    else:
        form = InvoicesForm()

    context = {'title': 'Накладные',
               'form': form,
               'error': error,
               'orders': Invoice.objects.all()}
    return render(request, 'main/invoices.html', context)


def report(request):
    today = datetime.today()
    sum_to = Invoice.objects.filter(Q(date__gte=datetime(today.year, today.month, 1, 0, 0, 0))
                                          & Q(date__lte=datetime(today.year, today.month + 1,  1, 0, 0, 0))).aggregate(sum_of_=Sum('items__sum_of'))
    sum_pre = Invoice.objects.filter(Q(date__gte=datetime(today.year, today.month - 1, 1, 0, 0, 0))
                                          & Q(date__lte=datetime(today.year, today.month,  1, 0, 0, 0))).aggregate(sum_of_=Sum('items__sum_of'))
    sum_prep = sum_to['sum_of_'] + (sum_to['sum_of_'] - sum_pre['sum_of_'])/2
    context = {'title': 'Отчет',
               'data': Invoice.objects.values('supplier', 'items__spare_part').annotate(sum_of_=Sum('items__sum_of')),
               'sum_prep': sum_prep
               }
    return render(request, 'main/report.html', context)


def logout_user(request):
    logout(request)
    return HttpResponseRedirect(reverse('main:index'))


def create_order_cust(request):
    error = ''
    if request.method == 'POST':
        form = OrderCustForm(data=request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('main:create_order_cust'))
        else:
            error = 'Ошибка'
    else:
        form = OrderCustForm()
    context = {'title': 'Заказы покупателей',
               'form': form,
               'error': error,
               'orders': OrderCust.objects.all()}
    return render(request, 'main/create_order_cust.html', context)


def create_order_cust_detail(request, order_id):
    order = get_object_or_404(OrderCust, pk=order_id)
    error = ''
    if request.method == 'POST':
        form = OrderCustItemForm(data=request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('main:create_order_cust_detail', args=[order.pk, ]))
        else:
            error = 'Ошибка'
    else:
        form = OrderCustItemForm()

    context = {'title': 'Детали заказа',
               'form': form,
               'error': error,
               'order': order,
               'items': OrderCustItem.objects.filter(order=order)}
    return render(request, 'main/create_order_cust_detail.html', context)


def invoice_detail(request, order_id):
    order = get_object_or_404(Invoice, pk=order_id)
    context = {'title': 'Детали накладной',
               'items': InvoiceItem.objects.filter(invoice=order),
               'order': order}
    return render(request, 'main/invoice_detail.html', context)


def add_invoice_detail(request, order_id, item_id):
    order = get_object_or_404(Invoice, pk=order_id)
    item = get_object_or_404(InvoiceItem, pk=item_id)
    error = ''
    if request.method == 'POST':
        price = request.POST['price']
        InvoiceItem.objects.filter(id=item_id).update(price=int(price), sum_of=item.quantity * int(price))
        return HttpResponseRedirect(reverse('main:invoice_detail', args=[order.pk, ]))
    else:
        form = InvoiceItemForm()

    context = {'title': 'Детали накладной',
               'form': form,
               'error': error,
               'order': order,
               'items': InvoiceItem.objects.filter(invoice=order),
               'item': item}
    return render(request, 'main/add_invoice_detail.html', context)


class ChartData(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, format=None):
        data = Invoice.objects.values('supplier', 'items__spare_part').annotate(sum_of_=Sum('items__sum_of'))
        labels = []
        d = []
        for sup in Supplier.objects.all():
            data1 = Invoice.objects.filter(supplier=sup).values('supplier', 'items__spare_part').annotate(sum_of_=Sum('items__sum_of'))
            labels.append([i['items__spare_part'] for i in data1])
            d.append([i['sum_of_'] if i['sum_of_'] is not None else 0 for i in data1])
        data = {
            'data': data,
            'labels1': labels[0],
            'label1': 'Поставщик 1',
            'data1': map(int, d[0]),
            'labels2': labels[1],
            'label2': 'Поставщик 2',
            'data2': map(int, d[1]),
            'labels3': labels[2],
            'label3': 'Поставщик 3',
            'data3': map(int, d[2]),
            'labels4': labels[3],
            'label4': 'Поставщик 4',
            'data4': map(int, d[3]),
        }
        return Response(data=data)


def generate_pdf_order_cust(request, order_id):
    def generate_pdf(request):
        # Load your HTML template
        template = loader.get_template('my_template.html')

        # Render the HTML content
        context = {'context_variable': 'some_value'}  # Replace with your context data
        html_content = template.render(context)

        # Create a PDF object
        pdf = weasyprint.HTML(string=html_content)

        # Generate the PDF file
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="my_pdf.pdf"'
        pdf.write_pdf(response)

        return response

