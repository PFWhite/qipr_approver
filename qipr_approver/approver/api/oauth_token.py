from django.http import JsonResponse

def oauth_token(request):
    apidata = {
        'code': request.GET.get('code'),
        'state': request.GET.get('state')
    }
    return JsonResponse(apidata)
