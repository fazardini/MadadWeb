from django.db import models
from django.contrib.auth.models import User
# Create your models here.


class Hospital(models.Model):
    safe_id = models.CharField(max_length=16, null=False, unique=True)
    name = models.CharField(max_length=100, null=False)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='hospital'
    )

    def __str__(self):
        return "%s" % self.name


class Drug(models.Model):
    safe_id = models.CharField(max_length=16, null=False, unique=True)
    name = models.CharField(max_length=100, null=False)


class SurplusDrug(models.Model):
    safe_id = models.CharField(max_length=16, null=False, unique=True)
    count = models.IntegerField()
    expiration_date = models.DateField(auto_now=False)
    hospital = models.ForeignKey(
        Hospital,
        db_index=True,
        on_delete=models.CASCADE,
        related_name='surplus_drug'
    )
    drug = models.ForeignKey(
        Drug,
        db_index=True,
        on_delete=models.CASCADE,
        related_name='surplus'
    )

    class Meta:
        unique_together = (('hospital', 'drug'),)

    def __str__(self):
        return "%s - %s" % self.hospital.name % self.drug.name


class OrderedDrug(models.Model):
    safe_id = models.CharField(max_length=16, null=False, unique=True)
    ordered_count = models.IntegerField()
    client_hospital = models.ForeignKey(
        Hospital,
        db_index=True,
        on_delete=models.CASCADE,
        related_name='client'
    )
    surplus_drug = models.ForeignKey(
        SurplusDrug,
        db_index=True,
        on_delete=models.CASCADE,
        related_name='ordered'
    )

    def __str__(self):
        return "%s - %s" % self.client_hospital.name % self.surplus_drug.hospital.name