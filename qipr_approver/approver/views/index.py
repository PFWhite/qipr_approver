from django.shortcuts import render
from django.http import HttpResponse, Http404
from django.views.decorators.csrf import csrf_protect
from approver.forms import AboutYouForm, ProjectForm
from django.contrib.auth.models import User
from approver.models import Project

import approver.constants as constants
import approver.utils as utils
from approver.views.dashboard import dashboard

def index(request):
    context = {
        'content': 'approver/index.html',
        'registry_search_url': constants.registry_search_path
    }

    return render(request, 'approver/index.html', context )
