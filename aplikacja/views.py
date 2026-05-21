from django.shortcuts import render, redirect
from django.http import HttpResponse

# Create your views here.


def index(request):
    return render(request, 'home_page.html')

def submit_form(request):
    if request.method == 'POST':
        age = request.POST.get('age')
        height = request.POST.get('height')
        weight = request.POST.get('weight')
        activity_level = request.POST.get('activity_level')
        budget = request.POST.get('budget')
        like_animals = request.POST.get('like_animals')

        if not age or not height or not weight:
            return render(request, 'home_page.html', {'error': 'Please fill in all fields.'})

        context = {
            'age': age,
            'height': height,
            'weight': weight,
            'activity_level': activity_level,
            'budget': budget,
            'like_animals': like_animals,
        }
        return render(request, 'results.html', context)
    else:
        return HttpResponse('Invalid request method.')
    
