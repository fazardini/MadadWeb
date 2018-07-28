from operator import itemgetter

from django.shortcuts import render
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.urls import reverse
from madadcore.models import Hospital, Drug, SurplusDrug, OrderedDrug
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from madadcore.helpers.mysecrets import token_hex
from datetime import date, timezone, timedelta
from django.db.models import Sum, Q, F
import calendar
import json
import xlwt

from madadsite.helpers.datetime_helpers import the_today


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


def create_my_drugs(request):
    user = request.user
    hospital = user.hospital
    access = hospital
    if request.method == 'POST':
        if access:
            try:
                name = request.POST.get('drug_name')
                safe_id = request.POST.get('drug_id')
                count = request.POST.get('drug_count')
                price = request.POST.get('drug_price', 0)
                cat = request.POST.get('drug_cat', 0)
                drug_type = request.POST.get('drug_type', 0)
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
                SurplusDrug.objects.create(safe_id=safe_id, current_count=count, initial_count=count,
                                           expiration_date=drug_date,
                                           drug=drug, hospital=hospital, cat=cat,
                                           drug_type=drug_type, price=price)
                done = True
            except Exception as e:
                err = e
                safe_id = False
                done = False
            response_dict = {'access': True, 'done': done, 'safe_id': safe_id}
        else:
            response_dict = {'access': False}
        return JsonResponse(response_dict)


def my_drugs(request, safe_id):
    user = request.user
    hospital = Hospital.objects.filter(safe_id=safe_id).first()
    access = (hospital.user == user)
    if access:
        surplus_drugs = SurplusDrug.objects.filter(hospital=hospital).exclude(
            Q(expiration_date__lt=the_today()) |
            Q(current_count=0)
        ).distinct()
        if request.method == 'POST':
            sort_by = int(request.POST.get('sorted_by', 0))
            drug_type = request.POST.get('drug_type', 'all')
            if drug_type != 'all':
                surplus_drugs = surplus_drugs.filter(drug_type=drug_type)
            if sort_by == 4:
                surplus_drugs = surplus_drugs.order_by('current_count')
            elif sort_by == 3:
                surplus_drugs = surplus_drugs.order_by('-current_count')
            elif sort_by == 2:
                surplus_drugs = surplus_drugs.order_by('-expiration_date')
            elif sort_by == 1:
                surplus_drugs = surplus_drugs.order_by('expiration_date')
            else:
                surplus_drugs = surplus_drugs.order_by('drug__name')
            surplus_drugs = surplus_drugs.values(
                'safe_id', 'drug__name', 'expiration_date', 'current_count', 'cat',
                'drug_type', 'price')
        surplus_drugs = surplus_drugs.values(
            'safe_id', 'drug__name', 'expiration_date', 'current_count', 'cat',
            'drug_type', 'price')
        for drug in surplus_drugs:
            drug['ordered'] = not OrderedDrug.objects.filter(surplus_drug__safe_id=drug['safe_id']).exists()
            drug['cat'] = SurplusDrug.CAT_DICT[drug['cat']]
            drug['drug_type'] = SurplusDrug.TYPE_DICT[drug['drug_type']]
            if drug['expiration_date'] - the_today() <= timedelta(days=90):
                drug['exp_state'] = "lte3"
            elif drug['expiration_date'] - the_today() <= timedelta(days=180):
                drug['exp_state'] = "lte6"
            else:
                drug['exp_state'] = "gt6"
        context_dict = {'access': access, 'surplus_drugs': list(surplus_drugs), 'safe_id': request.user.hospital.safe_id}
        if request.method == 'POST':
            return JsonResponse(context_dict)
        return render(request, 'madadsite/drugs.html', context_dict)
    else:
        return render(request, 'madadsite/drugs.html', {'access': access})


def ordered_drugs(request, safe_id):
    """
    اقلام دریافتی
    :param request: 
    :param safe_id: 
    :return: 
    """
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
            'surplus_drug__hospital__name', 'safe_id', 'state',
            price=F('surplus_drug__price'))

        for drug in all_drugs:
            if drug['surplus_drug__expiration_date'] - the_today() <= timedelta(days=90):
                drug['exp_state'] = "lte3"
            elif drug['surplus_drug__expiration_date'] - the_today() <= timedelta(days=180):
                drug['exp_state'] = "lte6"
            else:
                drug['exp_state'] = "gt6"
            drug['surplus_drug__expiration_date'] = "{}/{}".format(drug['surplus_drug__expiration_date'].year, drug['surplus_drug__expiration_date'].month)
        response_dict = {'drugs': list(all_drugs)}
        return JsonResponse(response_dict)

    ordered_drugs = OrderedDrug.objects.filter(client_hospital__safe_id=safe_id).values(
        'surplus_drug__drug__name', 'ordered_count', 'surplus_drug__expiration_date',
        'surplus_drug__hospital__name', 'safe_id', 'state',
        price=F('surplus_drug__price')).order_by('surplus_drug__expiration_date')
    for drug in ordered_drugs:
        if drug['surplus_drug__expiration_date'] - the_today() <= timedelta(days=90):
            drug['exp_state'] = "lte3"
        elif drug['surplus_drug__expiration_date'] - the_today() <= timedelta(days=180):
            drug['exp_state'] = "lte6"
        else:
            drug['exp_state'] = "gt6"
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
            'client_hospital__name', 'safe_id', 'state',
            price=F('surplus_drug__price'))

        for drug in all_drugs:
            if drug['surplus_drug__expiration_date'] - the_today() <= timedelta(days=90):
                drug['exp_state'] = "lte3"
            elif drug['surplus_drug__expiration_date'] - the_today() <= timedelta(days=180):
                drug['exp_state'] = "lte6"
            else:
                drug['exp_state'] = "gt6"
            drug['surplus_drug__expiration_date'] = "{}/{}".format(drug['surplus_drug__expiration_date'].year,
                                                                drug['surplus_drug__expiration_date'].month)
        response_dict = {'drugs': list(all_drugs)}
        return JsonResponse(response_dict)

    all_drugs = OrderedDrug.objects.filter(surplus_drug__hospital__safe_id=safe_id).values(
        'surplus_drug__drug__name', 'ordered_count', 'surplus_drug__expiration_date',
        'client_hospital__name', 'safe_id', 'state',price=F('surplus_drug__price')
    ).order_by('surplus_drug__expiration_date')
    for drug in all_drugs:
        if drug['surplus_drug__expiration_date'] - the_today() <= timedelta(days=90):
            drug['exp_state'] = "lte3"
        elif drug['surplus_drug__expiration_date'] - the_today() <= timedelta(days=180):
            drug['exp_state'] = "lte6"
        else:
            drug['exp_state'] = "gt6"
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
    all_drugs = SurplusDrug.objects.all().exclude(Q(expiration_date__lt=the_today()) |
                                                  Q(current_count=0)).distinct().values(
        'drug__name', 'drug__safe_id').annotate(
        sum_count=Sum('current_count')).order_by('-sum_count')
    sort_by = 1
    if request.method == 'POST':
        search_text = request.POST.get('search_text')
        sort_by = int(request.POST.get('sorted_by', 0))
        # all_drugs = SurplusDrug.objects.all().exclude(
        #     Q(expiration_date__lt=the_today()) |
        #     Q(current_count=0)
        # ).values('drug__name', 'drug__safe_id').annotate(sum_count=Sum('current_count'))
        if search_text:
            all_drugs = all_drugs.filter(
                Q(drug__name__icontains=search_text) | Q(drug__name__icontains=search_text)).values(
                'drug__name', 'drug__safe_id').annotate(sum_count=Sum('current_count'))
        if sort_by == 1:
            all_drugs = all_drugs.order_by('-sum_count')
        elif sort_by == 2:
            all_drugs = all_drugs.order_by('sum_count')

    for drug in all_drugs:
        exp_drug = SurplusDrug.objects.filter(drug__safe_id=drug['drug__safe_id']).exclude(
            Q(expiration_date__lt=the_today()) |
            Q(current_count=0)).order_by('expiration_date').first()
        if sort_by in (3, 4):
            drug['exp_date'] = exp_drug.expiration_date
        elif sort_by in (5, 6):
            first_drug = SurplusDrug.objects.filter(drug__safe_id=drug['drug__safe_id']).exclude(
                Q(expiration_date__lt=the_today()) |
                Q(current_count=0)).order_by('created_at').first()
            drug['create_date'] = first_drug.created_at
        if exp_drug.expiration_date - the_today() <= timedelta(days=90):
            drug['exp_state'] = "lte3"
        elif exp_drug.expiration_date - the_today() <= timedelta(days=180):
            drug['exp_state'] = "lte6"
        else:
            drug['exp_state'] = "gt6"
    if request.method == 'POST':
        if sort_by == 3:
            all_drugs = sorted(all_drugs, key=itemgetter('exp_date'), reverse=False)
        elif sort_by == 4:
            all_drugs = sorted(all_drugs, key=itemgetter('exp_date'), reverse=True)
        elif sort_by == 5:
            all_drugs = sorted(all_drugs, key=itemgetter('create_date'), reverse=True)
        elif sort_by == 6:
            all_drugs = sorted(all_drugs, key=itemgetter('create_date'), reverse=False)
        response_dict = {'drugs': list(all_drugs)}
        return JsonResponse(response_dict)
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
    safe_id = request.POST.get('item_id')
    state = request.POST.get('state', 0)
    orderd_drug = OrderedDrug.objects.filter(safe_id=safe_id).first()
    response_dict = {}
    try:
        orderd_drug.state = state
        if state == 1:
            orderd_drug.sent_at = timezone.now
        elif state == 2:
            orderd_drug.delivered_at = timezone.now
        orderd_drug.save()
        response_dict['done'] = True
    except Exception as e:
        err = e
        response_dict['done'] = False
    return JsonResponse(response_dict)


def hospitals_drug(request):
    drug_id = request.POST.get('drug_id')
    drun_name = Drug.objects.filter(safe_id=drug_id).first().name
    hospitals = SurplusDrug.objects.filter(drug__safe_id=drug_id).exclude(
        current_count=0).order_by('-created_at').values(
        'hospital__name', 'expiration_date', 'current_count', 'safe_id', 'price')
    for drug in hospitals:
        if drug['expiration_date'] - the_today() <= timedelta(days=90):
            drug['exp_state'] = "lte3"
        elif drug['expiration_date'] - the_today() <= timedelta(days=180):
            drug['exp_state'] = "lte6"
        else:
            drug['exp_state'] = "gt6"
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
        ordered = OrderedDrug.objects.filter(surplus_drug__safe_id=surplus_drug.safe_id).exists()
        if ordered:
            # if surplus_drug.ordered.state != 2:
            #     surplus_drug.delete()
            # else:
            response_dict['done'] = False
        else:
            surplus_drug.delete()
            response_dict['done'] = True
    except Exception as e:
        err = e
        response_dict['done'] = False
    return JsonResponse(response_dict)


def create_all_drugs_excel(request):
    search_text = request.GET.get('search_text', '')
    sort_by = int(request.GET.get('sorted_by', 1))
    all_drugs = SurplusDrug.objects.all().exclude(current_count=0)
    if search_text:
        all_drugs = all_drugs.filter(
            Q(drug__name__icontains=search_text) | Q(drug__name__icontains=search_text))
    if sort_by == 1:
        all_drugs = all_drugs.order_by('-current_count')
    elif sort_by == 2:
        all_drugs = all_drugs.order_by('current_count')
    all_drugs = all_drugs.values('drug__name', 'current_count', 'expiration_date', 'hospital__name')
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="Drugs.xls"'
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('همه اقلام')

    row_num = 0
    columns = ['نام دارو', 'نام بیمارستان', 'تعداد مازاد', 'تاریخ انقضا']
    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num])
    for drug in all_drugs:
        row_num += 1
        expiration_date = '{}/{}/{}'.format(drug['expiration_date'].year, drug['expiration_date'].month, drug['expiration_date'].day)
        result_list = [drug['drug__name'], drug['hospital__name'],
                       drug['current_count'], expiration_date]

        for col_num in range(len(columns)):
            ws.write(row_num, col_num, result_list[col_num])
    wb.save(response)
    return response


def exchange_drugs(request):
    # if request.method == 'POST':
    #     search_text = request.POST.get('search_text')
    #     sort_by = int(request.POST.get('sorted_by', 0))
    #     all_drugs = OrderedDrug.objects.filter(surplus_drug__hospital__safe_id=safe_id)
    #     if search_text:
    #         all_drugs = all_drugs.filter(
    #             Q(surplus_drug__drug__name__icontains=search_text) | Q(client_hospital__name__icontains=search_text))
    #     if sort_by == 1:
    #         all_drugs = all_drugs.order_by('surplus_drug__expiration_date')
    #     elif sort_by == 2:
    #         all_drugs = all_drugs.order_by('-surplus_drug__expiration_date')
    #     elif sort_by == 3:
    #         all_drugs = all_drugs.order_by('-ordered_count')
    #     elif sort_by == 4:
    #         all_drugs = all_drugs.order_by('ordered_count')
    #     all_drugs = all_drugs.values(
    #         'surplus_drug__drug__name', 'ordered_count', 'surplus_drug__expiration_date',
    #         'client_hospital__name', 'safe_id', 'state')
    #
    #     for drug in all_drugs:
    #         drug['surplus_drug__expiration_date'] = "{}/{}".format(drug['surplus_drug__expiration_date'].year,
    #                                                             drug['surplus_drug__expiration_date'].month)
    #     response_dict = {'drugs': list(all_drugs)}
    #     return JsonResponse(response_dict)
    if request.user.is_staff:
        all_drugs = OrderedDrug.objects.all().values(
            'surplus_drug__drug__name', 'surplus_drug__hospital__name', 'ordered_count', 'surplus_drug__expiration_date',
            'client_hospital__name', 'safe_id', 'state').order_by('surplus_drug__expiration_date')
        context_dict = {'drugs': list(all_drugs), 'safe_id': request.user.hospital.safe_id}
        return render(request, 'madadsite/exchange_drugs.html', context_dict)
    context_dict = {'err_access': True, 'safe_id': request.user.hospital.safe_id}
    return render(request, 'madadsite/exchange_drugs.html', context_dict)


def create_exchange_drugs_excel(request):
    if request.user.is_staff:
        all_drugs = OrderedDrug.objects.all()

        all_drugs = all_drugs.values('surplus_drug__drug__name',
                                     'surplus_drug__hospital__name',
                                     'ordered_count',
                                     'surplus_drug__expiration_date',
                                     'client_hospital__name', 'state')
        response = HttpResponse(content_type='application/ms-excel')
        response['Content-Disposition'] = 'attachment; filename="ExchangeDrugs.xls"'
        wb = xlwt.Workbook(encoding='utf-8')
        ws = wb.add_sheet('داروهای مبادله شده')

        row_num = 0
        columns = ['سفارش دهنده', 'سفارش گیرنده', 'نام دارو', 'تعداد سفارش', 'تاریخ انقضا', 'وضعیت']
        for col_num in range(len(columns)):
            ws.write(row_num, col_num, columns[col_num])
        for drug in all_drugs:
            row_num += 1
            expiration_date = '{}/{}/{}'.format(drug['surplus_drug__expiration_date'].year,
                                                drug['surplus_drug__expiration_date'].month,
                                                drug['surplus_drug__expiration_date'].day)
            if drug['state'] == 0:
                state = 'درحال بررسی'
            elif drug['state'] == 1:
                state = 'ارسال شده'
            else:
                state = 'تحویل داده شده'

            result_list = [drug['client_hospital__name'], drug['surplus_drug__hospital__name'],
                           drug['surplus_drug__drug__name'],
                           drug['ordered_count'],
                           expiration_date,
                           state]

            for col_num in range(len(columns)):
                ws.write(row_num, col_num, result_list[col_num])
        wb.save(response)
        return response