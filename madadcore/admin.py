from django.contrib import admin
from .models import *
# Register your models here.


class HospitalAdmin(admin.ModelAdmin):
    list_display = ('safe_id', 'name', 'mobile', 'phone', 'user')


class DrugAdmin(admin.ModelAdmin):
    list_display = ('safe_id', 'name')


class SurplusDrugAdmin(admin.ModelAdmin):
    list_display = ('safe_id', 'count', 'expiration_date', 'hospital', 'drug')


class OrderedDrugAdmin(admin.ModelAdmin):
    list_display = ('safe_id', 'ordered_count', 'client_hospital', 'surplus_drug')


admin.site.register(Hospital, HospitalAdmin)
admin.site.register(Drug, DrugAdmin)
admin.site.register(SurplusDrug, SurplusDrugAdmin)
admin.site.register(OrderedDrug, OrderedDrugAdmin)