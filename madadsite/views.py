from django.shortcuts import render
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.urls import reverse
from madadcore.models import Hospital, Drug, SurplusDrug, OrderedDrug
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from secrets import token_hex
from datetime import date
from django.db.models import Sum, Q
import calendar
import json


def register(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        hospital_name = request.POST.get('hospital_name')
        address = request.POST.get('address')
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
                                        mobile=mobile, phone=phone, user=user, address=address)
                done = True
            except Exception as e:
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
                    return HttpResponseRedirect(reverse('my_drugs', kwargs={'safe_id': user.hospital.safe_id}))
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


def my_drugs(request, safe_id):
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
                SurplusDrug.objects.create(safe_id=safe_id, current_count=count, initial_count=count, expiration_date=drug_date,
                                           drug=drug, hospital=hospital)
                done = True
            except Exception as e:
                err = e
                safe_id = False
                done = False
            response_dict = {'access': True, 'done': done, 'safe_id': safe_id}
        else:
            response_dict = {'access': False}
        return JsonResponse(response_dict)
    if access:
        surplus_drugs = SurplusDrug.objects.filter(hospital=hospital).values('safe_id','drug__name', 'expiration_date',
                                                                             'current_count','ordered__state')
        context_dict = {'access': access, 'surplus_drugs': list(surplus_drugs), 'safe_id': request.user.hospital.safe_id}
        return render(request, 'madadsite/drugs.html', context_dict)
    else:
        return render(request, 'madadsite/drugs.html', {'access': access})


def ordered_drugs(request, safe_id):
    if request.method == 'POST':
        search_text = request.POST.get('search_text')
        sort_by = int(request.POST.get('sorted_by', 1))
        all_drugs = OrderedDrug.objects.filter(client_hospital__safe_id=safe_id)
        if search_text:
            all_drugs = all_drugs.filter(
                Q(surplus_drug__drug__name__icontains=search_text) | Q(surplus_drug__hospital__name__icontains=search_text))
        if sort_by == 1:
            all_drugs = all_drugs.order_by('surplus_drug__expiration_date')
        elif sort_by == 2:
            all_drugs = all_drugs.order_by('-surplus_drug__expiration_date')
        if sort_by == 3:
            all_drugs = all_drugs.order_by('-ordered_count')
        elif sort_by == 4:
            all_drugs = all_drugs.order_by('ordered_count')
        all_drugs = all_drugs.values(
            'surplus_drug__drug__name', 'ordered_count', 'surplus_drug__expiration_date',
            'surplus_drug__hospital__name', 'safe_id')

        for drug in all_drugs:
            drug['surplus_drug__expiration_date'] = "{}/{}".format(drug['surplus_drug__expiration_date'].year, drug['surplus_drug__expiration_date'].month)
        response_dict = {'drugs': list(all_drugs)}
        return JsonResponse(response_dict)

    ordered_drugs = OrderedDrug.objects.filter(client_hospital__safe_id=safe_id).values(
        'surplus_drug__drug__name', 'ordered_count', 'surplus_drug__expiration_date',
        'surplus_drug__hospital__name', 'safe_id').order_by('surplus_drug__expiration_date')
    context_dict = {'drugs': list(ordered_drugs), 'safe_id': request.user.hospital.safe_id}
    return render(request, 'madadsite/drugs_ordered.html', context_dict)


def order_token_drugs(request, safe_id):
    if request.method == 'POST':
        search_text = request.POST.get('search_text')
        sort_by = int(request.POST.get('sorted_by', 0))
        all_drugs = OrderedDrug.objects.filter(surplus_drug__hospital__safe_id=safe_id)
        if search_text:
            all_drugs = all_drugs.filter(
                Q(surplus_drug__drug__name__icontains=search_text) | Q(client_hospital__name__icontains=search_text))
        if sort_by == 1:
            all_drugs = all_drugs.order_by('surplus_drug__expiration_date')
        elif sort_by == 2:
            all_drugs = all_drugs.order_by('-surplus_drug__expiration_date')
        elif sort_by == 3:
            all_drugs = all_drugs.order_by('-ordered_count')
        elif sort_by == 4:
            all_drugs = all_drugs.order_by('ordered_count')
        all_drugs = all_drugs.values(
            'surplus_drug__drug__name', 'ordered_count', 'surplus_drug__expiration_date',
            'client_hospital__name', 'safe_id')
        # import ipdb; ipdb.set_trace()

        for drug in all_drugs:
            drug['surplus_drug__expiration_date'] = "{}/{}".format(drug['surplus_drug__expiration_date'].year,
                                                                drug['surplus_drug__expiration_date'].month)
        response_dict = {'drugs': list(all_drugs)}
        return JsonResponse(response_dict)

    all_drugs = OrderedDrug.objects.filter(surplus_drug__hospital__safe_id=safe_id).values(
        'surplus_drug__drug__name', 'ordered_count', 'surplus_drug__expiration_date',
        'client_hospital__name', 'safe_id').order_by('surplus_drug__expiration_date')
    context_dict = {'drugs': list(all_drugs), 'safe_id': request.user.hospital.safe_id}
    return render(request, 'madadsite/drugs_ordertaken.html', context_dict)


def all_hospitals(request):
    if request.method == 'POST':
        search_text = request.POST.get('search_text')
        hospitals = Hospital.objects.filter(name__icontains=search_text).all().values('name', 'safe_id', 'address', 'phone')
        response_dict = {'hospitals': list(hospitals)}
        return JsonResponse(response_dict)
    hospitals = Hospital.objects.all().values('name', 'safe_id', 'address', 'phone')
    context_dict = {'hospitals': list(hospitals), 'safe_id': request.user.hospital.safe_id}
    return render(request, 'madadsite/hospitals.html', context_dict)


def all_drugs(request):
    if request.method == 'POST':
        search_text = request.POST.get('search_text')
        sort_by = int(request.POST.get('sorted_by', 0))
        all_drugs = SurplusDrug.objects.all().values('drug__name', 'drug__safe_id').annotate(sum_count=Sum('current_count'))
        if search_text:
            all_drugs = all_drugs.filter(
                Q(drug__name__icontains=search_text) | Q(drug__name__icontains=search_text)).values(
                'drug__name', 'drug__safe_id').annotate(sum_count=Sum('current_count'))
        if sort_by == 1:
            all_drugs = all_drugs.order_by('-sum_count')
        elif sort_by == 2:
            all_drugs = all_drugs.order_by('sum_count')
        response_dict = {'drugs': list(all_drugs)}
        return JsonResponse(response_dict)
    all_drugs = SurplusDrug.objects.all().distinct().values(
        'drug__name', 'drug__safe_id').annotate(
        sum_count=Sum('current_count')).order_by('-sum_count')
    context_dict = {'drugs': list(all_drugs), 'safe_id': request.user.hospital.safe_id}
    return render(request, 'madadsite/all_drugs.html', context_dict)


def drugs_name(request):
    if request.is_ajax():
        searched_text = request.GET.get('term', '')
        drugs = Drug.objects.filter(name__icontains=searched_text).distinct().values(
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


def change_order_state(request):
    return 1


def hospitals_drug(request):
    drug_id = request.POST.get('drug_id')
    drun_name = Drug.objects.filter(safe_id=drug_id).first().name
    hospitals = SurplusDrug.objects.filter(drug__safe_id=drug_id).values(
        'hospital__name', 'expiration_date', 'current_count', 'safe_id')

    return JsonResponse({'hospitals': list(hospitals), 'drun_name': drun_name})


def save_order(request):
    drug_id = request.POST.get('drug_id')
    count = float(request.POST.get('count'))
    surplus_drug = SurplusDrug.objects.filter(safe_id=drug_id).first()
    response_dict = {}
    try:
        if surplus_drug.current_count >= count:
            safe_id = token_hex(8)
            OrderedDrug.objects.create(safe_id=safe_id, ordered_count=count, client_hospital=request.user.hospital,
                                       surplus_drug=surplus_drug)
            surplus_drug.current_count -= count
            surplus_drug.save()
            response_dict = {'done': True}
        else:
            response_dict = {'not_exist': True}
    except Exception as e:
        err = e
    return JsonResponse(response_dict)


def delete_my_drugs(request):
    drug_id = request.POST.get('drug_id')
    surplus_drug = SurplusDrug.objects.filter(safe_id=drug_id).first()
    response_dict = {}
    try:
        # if surplus_drug.ordered:
        #     if surplus_drug.ordered.state != 2:
        #         surplus_drug.delete()
        #     else:
        #         response_dict['done'] = False
        # else:
        surplus_drug.delete()
        response_dict['done'] = True
    except Exception as e:
        err = e
        response_dict['done'] = False
    return JsonResponse(response_dict)