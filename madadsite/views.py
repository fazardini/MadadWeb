from django.shortcuts import render
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.urls import reverse
from madadcore.models import Hospital
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from secrets import token_hex


def register(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        hospital_name = request.POST.get('hospital_name')
        phone = request.POST.get('phone')
        mobile = request.POST.get('mobile')
        password = request.POST.get('password')
        user = User.objects.filter(username=username).first()
        if user:
            return JsonResponse({'error': True})
        else:
            try:
                user = User(username=username, first_name=first_name, last_name=last_name)
                user.set_password(password)
                user.save()
                safe_id = token_hex(8)
                Hospital.objects.create(safe_id=safe_id, name=hospital_name,
                                        mobile=mobile, phone=phone, user=user)
                done = True
            except:
                done = False
            return JsonResponse({'done': done})
    else:
        return render(request, 'madadsite/register.html', {})


def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        if user:
            if user.is_active:
                login(request, user)
                html = "<html><body>It is now.</body></html>"
                return HttpResponse(html)
                # return HttpResponseRedirect(reverse('home'))
                # # return JsonResponse({'done': True})
            else:
                return render(request, 'madadsite/login.html', {'active_error': True})
        else:
            return render(request, 'madadsite/login.html', {'error': True})
    return render(request, 'madadsite/login.html', {})


def user_logout(request):

    logout(request)
    return HttpResponseRedirect(reverse('login'))