from django.core import serializers
from django.contrib.auth.models import User

import requests
import approver.models
from approver.constants import registry_endpoints, api_username

def jsonify(model):
    return serializers.serialize('json', [model], use_natural_foreign_keys=True, use_natural_primary_keys=True)

def push_model(model):
    api_user = User.objects.get(username=api_username)
    json_data = jsonify(model)

    response = requests.post(registry_endpoints.get('add_model'), data=json_data)
    if response.status_code == 200:
        model.register()
        model.save(api_user)
    return response

