from django.shortcuts import render, redirect
from django.http import HttpResponse
from pathlib import Path
from aplikacja.silnik_sportowcy import build_profile_from_post, recommend

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

        user = build_profile_from_post(request.POST)

        csv_path = Path(__file__).resolve().parent.parent / 'aplikacja' / 'sport_averages.csv'
        results = recommend(user, csv_path=csv_path, top_n=5)

        context = {
            'results': results,
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