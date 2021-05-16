from django.shortcuts import render, resolve_url

# Create your views here.
def getData(request) : 
    return render(request, 'base.html', {
        'data' : "FUCKER",
    })