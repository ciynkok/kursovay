from django.shortcuts import render

# Create your views here.


def index(request):
    return render(request, 'main/index.html')


def main(request):
    return render(request, 'main/main.html')


def invoices(request):
    return render(request, 'main/invoices.html')


def report(request):
    return render(request, 'main/report.html')
