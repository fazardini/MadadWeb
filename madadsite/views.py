from django.shortcuts import render
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.urls import reverse
from madadcore.models import Hospital, Drug, SurplusDrug, OrderedDrug
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from secrets import token_hex
from datetime import date
import calendar
import json


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
                user = User(username=username, first_name=first_name, last_name=last_name, is_active=False)
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
        user = User.objects.filter(username=username).first()
        if user:
            if user.is_active:
                user = authenticate(username=username, password=password)
                if user:
                    login(request, user)
                    return HttpResponseRedirect(reverse('hospital_drugs', kwargs={'safe_id': user.hospital.safe_id}))
                else:
                    return render(request, 'madadsite/login.html', {'error': True})
            else:
                return render(request, 'madadsite/login.html', {'active_error': True})
        else:
            return render(request, 'madadsite/login.html', {'error': True})
    return render(request, 'madadsite/login.html', {})


def user_logout(request):

    logout(request)
    return HttpResponseRedirect(reverse('login'))


def hospital_drugs(request, safe_id):
    user = request.user
    hospital = Hospital.objects.filter(safe_id=safe_id).first()
    access = (hospital.user == user)
    if request.method == 'POST':
        if access:
            try:
                name = request.POST.get('drug_name')
                safe_id = request.POST.get('drug_id')
                count = request.POST.get('drug_count')
                month = int(request.POST.get('drug_month'))
                year = int(request.POST.get('drug_year'))
                last_day_this_month = calendar.monthrange(year, month)[1]
                drug_date = date(year, month, last_day_this_month)
                if safe_id:
                    drug = Drug.objects.filter(safe_id=safe_id).first()
                else:
                    safe_id = token_hex(8)
                    drug = Drug.objects.create(name=name, safe_id=safe_id)
                safe_id = token_hex(8)
                SurplusDrug.objects.create(safe_id=safe_id, count=count, expiration_date=drug_date,
                                           drug=drug, hospital=hospital)
                done = True
            except:
                done = False
            response_dict = {'access': True, 'done': done}
        else:
            response_dict = {'access':False}
        return JsonResponse(response_dict)
    if access:
        surplus_drugs = SurplusDrug.objects.filter(hospital=hospital).values('drug__name', 'expiration_date',
                                                                            'count')
        context_dict = {'access': access, 'hospital_id': safe_id, 'surplus_drugs': list(surplus_drugs), 'safe_id': request.user.hospital.safe_id}
        return render(request, 'madadsite/drugs.html', context_dict)
    else:
        return render(request, 'madadsite/drugs.html', {'access': access})


def all_hospitals(request):
    hospitals = Hospital.objects.all().values('name', 'safe_id', 'address', 'phone')
    context_dict = {'hospitals': list(hospitals), 'safe_id': request.user.hospital.safe_id}
    return render(request, 'madadsite/hospitals.html', context_dict)


def all_drugs(request):
    all_drugs = SurplusDrug.objects.all().values('drug__name', 'drug__safe_id')
    context_dict = {'drugs': list(all_drugs), 'safe_id': request.user.hospital.safe_id}
    return render(request, 'madadsite/all_drugs.html', context_dict)


def drugs_name(request):
    if request.is_ajax():
        searched_text = request.GET.get('term', '')
        drugs = Drug.objects.filter(name__icontains=searched_text).values(
            'name', 'safe_id').order_by('name')[:10]
        results = []
        for drug in drugs:
            drugs_json = {'label': drug['name'], 'value': drug['name'],
                          'id': drug['safe_id']}
            results.append(drugs_json)
        data = json.dumps(results)
    else:
        data = 'fail'
    mimetype = 'application/json'
    return HttpResponse(data, mimetype)