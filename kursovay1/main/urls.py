from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
    path('', views.index, name='index'),
    path('main/', views.main, name='main'),
    path('invoices/', views.invoices, name='invoices'),
    path('report/', views.report, name='report'),
    path('workspace/', views.workspace, name='workspace'),
    path('create_order_sup/', views.create_order_sup, name='create_order_sup'),
    path('logout/', views.logout_user, name='logout'),
    path('create_order_cust/', views.create_order_cust, name='create_order_cust'),
    path('order_cust_type/<int:order_id>', views.order_cust_type, name='order_cust_type'),
    path('create_order_cust_detail/<int:order_id>', views.create_order_cust_detail, name='create_order_cust_detail'),
    path('invoice_detail/<int:order_id>', views.invoice_detail, name='invoice_detail'),
    path('add_invoice_detail/<int:order_id>/<int:item_id>', views.add_invoice_detail, name='add_invoice_detail'),
    path('func/', views.ChartData.as_view(), name='func'),
    path('form_order_cust/<int:order_id>', views.generate_pdf_order_cust, name='form_order_cust'),
]

