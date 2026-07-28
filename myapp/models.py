import uuid
from django.db import models

class Plumber(models.Model):
    name = models.CharField(max_length=30)
    phone = models.CharField(max_length=10, unique=True)
    address = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Product(models.Model):

    name = models.CharField(
        max_length=100,
        unique=True
    )

    def __str__(self):
        return self.name

class RewardRule(models.Model):

    CASH = "Cash"
    PRODUCT = "Product"

    PRIZE_CHOICES = [
        (CASH, "Cash"),
        (PRODUCT, "Product"),
    ]

    min_purchase = models.PositiveIntegerField()
    max_purchase = models.PositiveIntegerField()

    prize_type = models.CharField(
        max_length=10,
        choices=PRIZE_CHOICES,
        default=CASH
    )

    min_reward = models.PositiveIntegerField(null=True, blank=True)
    max_reward = models.PositiveIntegerField(null=True, blank=True)

    purchase_product = models.CharField(
        max_length=100
    )


    buy_quantity = models.PositiveIntegerField(default=11)

    reward_product = models.CharField(
        max_length=100,
        blank=True
    )
    
    def __str__(self):
        return f"{self.purchase_product} ({self.min_purchase}-{self.max_purchase})"

class ScratchCard(models.Model):
    reward_rule = models.ForeignKey(
    RewardRule,
    on_delete=models.SET_NULL,
    null=True,
    blank=True
    )
    plumber = models.ForeignKey(Plumber, on_delete=models.CASCADE)
    purchase_amount = models.PositiveIntegerField()
    note = models.TextField(blank=True)
    reward_text = models.CharField(max_length=100)

    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    is_scratched = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.plumber.name

class PurchaseHistory(models.Model):

    plumber = models.ForeignKey(
        Plumber,
        on_delete=models.CASCADE
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT
    )

    quantity = models.PositiveIntegerField(default=1)

    rate = models.PositiveIntegerField(default=0)

    total = models.PositiveIntegerField(default=0)

    note = models.CharField(
        max_length=200,
        blank=True
    )

    purchase_date = models.DateField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.plumber.name} - {self.product.name} ({self.quantity})"

class FreeRewardHistory(models.Model):

    plumber = models.ForeignKey(
        Plumber,
        on_delete=models.CASCADE
    )

    reward_product = models.CharField(max_length=100)

    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.PositiveIntegerField(default=0)

    note = models.CharField(
        max_length=200,
        blank=True
    )

    given_date = models.DateField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Free Reward History"
        verbose_name_plural = "Free Reward History"

    def __str__(self):
        return f"{self.plumber.name} - {self.reward_product}"