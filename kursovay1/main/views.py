from django.shortcuts import render, redirect, HttpResponseRedirect, get_object_or_404
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login, logout
from .models import OrderCust, OrderCustItem, OrderSup, OrderSupItem, Supplier, SparePart, Invoice, InvoiceItem
from django.urls import reverse
from .forms import OrderCustForm, OrderCustItemForm, InvoiceItemForm, InvoicesForm
from django.db.models import Sum, Q
from datetime import datetime, date
from rest_framework.views import APIView
from rest_framework.response import Response
import io
from django.http import FileResponse
from reportlab.platypus.tables import Table, TableStyle
from reportlab.lib.units import inch
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib import colors




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
    return render(request, 'main/workspace.html', )


def order_sup(request):
    context = {'title': 'Заказы для поставщиков',
               'orders': OrderSup.objects.all(),
               }
    return render(request, 'main/order_sup.html', context)


def form_order_sup(request, order_id):
    order = get_object_or_404(OrderSup, pk=order_id)
    buffer = io.BytesIO()

    # Create the PDF object, using the buffer as its "file."
    p = canvas.Canvas(buffer)
    document_title = f'form_order_sup_{order.id}'
    supplier = order.supplier
    title = f'Заказ {supplier}'
    date_ = str(order.date)
    id_ = '0' * (10 - len((str(order.id)))) + str(order.id)
    items = OrderSupItem.objects.filter(order=order)

    p.setTitle(document_title)
    pdfmetrics.registerFont(
        TTFont('abc', 'timesnewromanpsmt.ttf')
    )

    # creating the title by setting it's font
    # and putting it on the canvas
    p.setFont('abc', 16)
    p.drawCentredString(300, 770, title)

    # Draw things on the PDF. Here's where the PDF generation happens.
    # See the ReportLab documentation for the full list of functionality.
    p.setFont('abc', 14)

    p.drawString(50, 700, 'Код: ' + id_)
    p.drawString(50, 680, 'Дата: ' + date_)

    my_data = [['Название детали', 'Количество'], ]

    for i in items:
        my_data.append([i.spare_part, i.quantity])

    c_width = [3 * inch, 1.5 * inch]
    t = Table(my_data, rowHeights=20, repeatRows=1, colWidths=c_width)
    t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                           ('FONTSIZE', (0, 0), (-1, -1), 14),
                           ('FONTNAME', (0, 0), (-1, -1), 'abc'),
                           ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                           ('GRID', (0, 0), (-1, -1), 1, colors.black),
                           ]))

    h = 550 - (10 * items.count())
    t.wrapOn(p, 300, 50)
    t.drawOn(p, 50, h)

    p.showPage()
    p.save()

    # FileResponse sets the Content-Disposition header so that browsers
    # present the option to save the file.
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=f"form_order_sup_{order.id}.pdf")


def create_order_sup(request):
    m = []
    today = date.today()
    gd = datetime(today.year, today.month, today.day, 0, 0, 0)
    ld = datetime(today.year, today.month, today.day + 1, 0, 0, 0)
    order_cust = OrderCust.objects.filter(Q(date__gte=gd) & Q(date__lte=ld))
    for ord in order_cust:
        m.append(ord)
    orders_sup = OrderCustItem.objects.filter(order__in=m).values('supplier').annotate(Sum('quantity'))
    suppliers = Supplier.objects.all()
    for order in orders_sup:
        o = OrderSup.objects.filter(Q(supplier=suppliers.get(id=order['supplier'])) & Q(date__gte=gd) & Q(date__lte=ld))
        if o.count() == 0:
            o = OrderSup(supplier=suppliers.get(id=order['supplier']))
            o.save()
        else:
            o = o.get(supplier=suppliers.get(id=order['supplier']))
        items = OrderCustItem.objects.filter(order__in=m, supplier=suppliers.get(id=order['supplier'])).values('spare_part').annotate(sum_quantity=Sum('quantity'))
        for item in items:
            defaults = {'quantity': item['sum_quantity']}
            obj, created = OrderSupItem.objects.update_or_create(order=o,
                                                  spare_part=SparePart.objects.get(id=item['spare_part']),
                                                  defaults=defaults)
    return HttpResponseRedirect(reverse('main:order_sup'))


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


def order_cust(request):
    context = {'title': 'Заказы покупателей',
               'orders': OrderCust.objects.all(),
               }
    return render(request, 'main/order_cust.html', context)


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
        spare_part = SparePart.objects.all()
        for sup in Supplier.objects.all():
            data1 = Invoice.objects.filter(supplier=sup).values('supplier', 'items__spare_part').annotate(sum_of_=Sum('items__sum_of'))
            labels.append([spare_part.get(id=i['items__spare_part']).name for i in data1])
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


def form_order_cust(request, order_id):
    order = get_object_or_404(OrderCust, pk=order_id)
    buffer = io.BytesIO()

    # Create the PDF object, using the buffer as its "file."
    p = canvas.Canvas(buffer)
    document_title = f'form_order_cust_{order.id}'
    customer = order.customer_name
    title = f'Заказ {customer}'
    id_ = '0' * (10 - len((str(order.id)))) + str(order.id)
    customer_phone = order.customer_phone
    car = order.car
    prepayment = str(order.prepayment)
    delivery_time = str(order.delivery_time)
    items = OrderCustItem.objects.filter(order=order)

    p.setTitle(document_title)
    pdfmetrics.registerFont(
        TTFont('abc', 'timesnewromanpsmt.ttf')
    )

    # creating the title by setting it's font
    # and putting it on the canvas
    p.setFont('abc', 16)
    p.drawCentredString(300, 770, title)

    # Draw things on the PDF. Here's where the PDF generation happens.
    # See the ReportLab documentation for the full list of functionality.
    p.setFont('abc', 14)

    p.drawString(50, 700, 'Код: ' + id_)
    p.drawString(50, 680, 'Имя: ' + customer)
    p.drawString(50, 660, 'Телефон: ' + customer_phone)
    p.drawString(50, 640, 'Автомобиль: ' + car)
    p.drawString(50, 620, 'Срок доставки: ' + delivery_time)
    p.drawString(50, 600, 'Предоплата: ' + prepayment + ' руб.')

    my_data = [['Название детали', 'Количество', 'Цена'],]

    for i in items:
        my_data.append([i.spare_part, i.quantity, i.price])

    c_width = [3 * inch, 1.5 * inch, 1.5 * inch]
    t = Table(my_data, rowHeights=20, repeatRows=1, colWidths=c_width)
    t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                           ('FONTSIZE', (0, 0), (-1, -1), 14),
                           ('FONTNAME', (0, 0), (-1, -1), 'abc'),
                           ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                           ('GRID', (0, 0), (-1, -1), 1, colors.black),
                           ]))

    h = 550 - (10 * items.count())
    t.wrapOn(p, 300, 50)
    t.drawOn(p, 50, h)

    p.drawString(380, 130, 'Подпись:')
    p1_style = ParagraphStyle('My Para style',
                              fontName='Times-Roman',
                              fontSize=16,
                              borderColor='#000000',
                              borderWidth=2,
                              borderPadding=(20, 20, 20),
                              leading=20,
                              alignment=0
                              )
    p1 = Paragraph(''' ''', p1_style)
    p1.wrapOn(p, 100, 100)
    p1.drawOn(p, 400, 100)
    p.showPage()
    p.save()

    # FileResponse sets the Content-Disposition header so that browsers
    # present the option to save the file.
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=f"form_order_cust_{order.id}.pdf")

