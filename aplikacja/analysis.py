import os
from django.conf import settings

def match_results_with_data(age, height, weight, activity_level, budget, like_animals):

    csv_path = os.path.join(settings.BASE_DIR, 'aplikacja', 'sport_averages.csv')

    # TODO

    results = ""
    return results