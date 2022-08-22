from django.shortcuts import render


def home(request):
    query = request.GET.get('q', None)
    return render(request, 'home_page/home_page.html')
