from django.db import models
from django.contrib.auth.models import User
# Create your models here.


class Hospital(models.Model):
    safe_id = models.CharField(max_length=16, null=False, unique=True)
    name = models.CharField(max_length=100, null=False)
    mobile = models.CharField(max_length=11, null=False)
    phone = models.CharField(max_length=30, blank=True, default='')
    address = models.TextField(max_length=256, blank=True, default='')
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

    def __str__(self):
        return "%s" % self.name


class SurplusDrug(models.Model):
    safe_id = models.CharField(max_length=16, null=False, unique=True)
    current_count = models.IntegerField(default=0)
    initial_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
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
        return "{} - {}".format(self.hospital.name ,self.drug.name)


class OrderedDrug(models.Model):
    PENDING = 0
    SENT = 1
    DELIVERED = 2
    MODE_CHOICES = (
        (PENDING, 'درحال بررسی'),
        (SENT, 'ارسال شده'),
        (DELIVERED, 'دریافت شده'),
    )
    MODE_DICT = dict((k, v) for k, v in MODE_CHOICES)

    state = models.SmallIntegerField(default=0, choices=MODE_CHOICES)
    safe_id = models.CharField(max_length=16, null=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(auto_now=True)
    delivered_at = models.DateTimeField(auto_now=True)
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
        return "{} - {}".format(self.client_hospital.name, self.surplus_drug.hospital.name)