from django.shortcuts import render, redirect
from django.http import HttpResponse
from .analysis import match_results_with_data

from django.contrib import messages # test

def index(request):
    return render(request, 'aplikacja/index.html')

def submit_form(request):
    if request.method == 'POST':

        age = request.POST.get('age')
        height = request.POST.get('height')
        weight = request.POST.get('weight')
        activity_level = request.POST.get('activity_level')
        budget = request.POST.get('budget')
        like_animals = request.POST.get('like_animals')

        if not age or not height or not weight:

            messages.error(request, 'Please fill in all fields.')
            return redirect('index')
            # return render(request, 'aplikacja/index.html', {'error': 'Please fill in all fields.'})
        
        recommendation = match_results_with_data(age, height, weight, activity_level, budget, like_animals)

        context = {
            'recommendation': recommendation,
            'age': age,
            'height': height,
            'weight': weight,
            'activity_level': activity_level,
            'budget': budget,
            'like_animals': like_animals,
        }
        return render(request, 'results.html', context)
    else:
        return HttpResponse('Invalid request method.', status=405) # added status