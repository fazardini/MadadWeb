from madadcore.models import OrderedDrug


def pending_drugs_count(hospital):

    drugs_count = OrderedDrug.objects.filter(
        surplus_drug__hospital=hospital, state=0
    ).count()
    return drugs_count
