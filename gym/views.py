from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from .models import Gym


def index(request: HttpRequest) -> HttpResponse:
    gyms = Gym.objects.all()

    gyms_info = []
    for gym in gyms:
        unique_trainers_count = gym.sessions.values('trainer').distinct().count()
        unique_clients_count = gym.sessions.values_list('clients', flat=True).distinct().count()

        gyms_info.append(
            {
                'gym': gym,
                'unique_trainers_count': unique_trainers_count,
                'unique_clients_count': unique_clients_count,
            }
        )

    context = {
        'num_gyms': gyms.count(),
        'gyms_info': gyms_info,
    }

    return render(request, 'gym/index.html', context)
