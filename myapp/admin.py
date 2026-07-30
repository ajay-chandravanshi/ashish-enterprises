from django.contrib import admin
from django.db import models
from django.utils.html import format_html
from urllib.parse import quote
from .models import (
    Product,
    Plumber,
    RewardRule,
    ScratchCard,
    PurchaseHistory,
    FreeRewardHistory,
)
import random
from django.urls import path
from django.shortcuts import redirect,render
from django.contrib import messages

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):

    list_display = (
        "name",
    )

    search_fields = (
        "name",
    )

    ordering = (
        "name",
    )

def get_rule():
    return RewardRule.objects.first()
    
@admin.register(Plumber)
class PlumberAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "phone",
        "address",
        "view_progress",
    )
    list_per_page = 50
    search_fields = ("name", "phone")
    ordering = ("name",)
    
    def view_progress(self, obj):

        return format_html(
            '<a class="button" href="/admin/myapp/plumber/{}/progress/">📊 View Progress</a>',
            obj.id
        )

    view_progress.short_description = "Product Progress"

    def total_sheet(self, obj):

        rule = get_rule()

        if not rule:
            return 0

        total = PurchaseHistory.objects.filter(
            plumber=obj,
            product=rule.purchase_product
        ).aggregate(
            total=models.Sum("quantity")
        )["total"] or 0

        return total

    total_sheet.short_description = "Purchased"

    def free_sheet_given(self, obj):

        rule = get_rule()

        if not rule:
            return 0

        return FreeRewardHistory.objects.filter(
            plumber=obj,
            reward_product=rule.reward_product
        ).count()

    free_sheet_given.short_description = "Free Given"

    def progress(self, obj):

        rule = get_rule()

        if not rule:
            return "0/0"

        total = PurchaseHistory.objects.filter(
            plumber=obj,
            product=rule.purchase_product
        ).aggregate(
            total=models.Sum("quantity")
        )["total"] or 0

        free = FreeRewardHistory.objects.filter(
            plumber=obj,
            reward_product=rule.reward_product
        ).count()

        remaining = total - (free * rule.buy_quantity)

        return f"{remaining}/{rule.buy_quantity}"

    progress.short_description = "Progress"

    def status(self, obj):

        rule = get_rule()

        if not rule:
            return "🔴 No Rule"

        total = PurchaseHistory.objects.filter(
            plumber=obj,
            product=rule.purchase_product
        ).aggregate(
            total=models.Sum("quantity")
        )["total"] or 0

        free = FreeRewardHistory.objects.filter(
            plumber=obj,
            reward_product=rule.reward_product
        ).count()

        remaining = total - (free * rule.buy_quantity)

        if remaining >= rule.buy_quantity:
            return "🟢 Eligible"

        return "🔴 Not Eligible"

    status.short_description = "Status"

    def give_free(self, obj):

        rule = get_rule()

        if not rule:
            return "No Rule"

        total = PurchaseHistory.objects.filter(
            plumber=obj,
            product=rule.purchase_product
        ).aggregate(
            total=models.Sum("quantity")
        )["total"] or 0

        free = FreeRewardHistory.objects.filter(
            plumber=obj,
            reward_product=rule.reward_product
        ).count()

        remaining = total - (free * rule.buy_quantity)

        if remaining >= rule.buy_quantity:
            return format_html(
                '<a class="button" href="/admin/myapp/plumber/give-free/{}/">🎁 Give</a>',
                obj.id
            )

        return "Disable"

    give_free.short_description = "Give Free"
    
    def get_urls(self):
        urls = super().get_urls()

        custom_urls = [
            path(
                "give-free/<int:plumber_id>/",
                self.admin_site.admin_view(self.give_free_view),
                name="give-free",
            ),
            path(
                "<int:plumber_id>/progress/",
                self.admin_site.admin_view(self.progress_view),
                name="plumber-progress",
            ),
            path(
                "<int:plumber_id>/give-product/<int:rule_id>/",
                self.admin_site.admin_view(self.give_product_reward),
                name="give-product-reward",
            ),
        ]

        return custom_urls + urls

    def give_free_view(self, request, plumber_id):

        from datetime import date

        rule = get_rule()

        if not rule:
            messages.error(request, "No Reward Rule Found.")
            return redirect("/admin/myapp/plumber/")

        plumber = Plumber.objects.only(
            "id",
            "name",
        ).get(id=plumber_id)
        
        total = PurchaseHistory.objects.filter(
            plumber=plumber,
            product=rule.purchase_product
        ).aggregate(
            total=models.Sum("quantity")
        )["total"] or 0

        free = FreeRewardHistory.objects.filter(
            plumber=plumber,
            reward_product=rule.reward_product
        ).count()

        remaining = total - (free * rule.buy_quantity)

        if remaining < rule.buy_quantity:
            messages.error(request, "Not Eligible For Free Reward.")
            return redirect("/admin/myapp/plumber/")

        FreeRewardHistory.objects.create(
            plumber=plumber,
            reward_product=rule.reward_product,
            quantity=1,
            given_date=date.today(),
        )

        messages.success(request, "Reward Given Successfully.")

        return redirect("/admin/myapp/plumber/")
    
    def progress_view(self, request, plumber_id):

        plumber = Plumber.objects.get(id=plumber_id)

        progress_list = []

        rules = RewardRule.objects.only(
            "id",
            "purchase_product",
            "reward_product",
            "buy_quantity",
        )

        for rule in rules:

            purchased = PurchaseHistory.objects.filter(
                plumber=plumber,
                product=rule.purchase_product
            ).aggregate(
                total=models.Sum("quantity")
            )["total"] or 0

            free_given = FreeRewardHistory.objects.filter(
                plumber=plumber,
                reward_product=rule.reward_product
            ).count()

            remaining = purchased - (free_given * rule.buy_quantity)

            progress_list.append({
                "rule_id": rule.id,
                "purchase_product": rule.purchase_product.name,
                "reward_product": rule.reward_product,
                "buy_quantity": rule.buy_quantity,
                "purchased": purchased,
                "free_given": free_given,
                "remaining": remaining,
                "eligible": remaining >= rule.buy_quantity,
            })

        context = {
            "plumber": plumber,
            "plumber_id": plumber.id,
            "progress_list": progress_list,
        }

        return render(
            request,
            "admin/product_progress.html",
            context,
        )
    

    def give_product_reward(self, request, plumber_id, rule_id):

        from datetime import date

        plumber = Plumber.objects.get(id=plumber_id)
        rule = RewardRule.objects.get(id=rule_id)

        purchased = PurchaseHistory.objects.filter(
            plumber=plumber,
            product=rule.purchase_product
        ).aggregate(
            total=models.Sum("quantity")
        )["total"] or 0

        free_given = FreeRewardHistory.objects.filter(
            plumber=plumber,
            reward_product=rule.reward_product
        ).count()

        remaining = purchased - (free_given * rule.buy_quantity)

        if remaining < rule.buy_quantity:
            messages.error(request, "Not Eligible.")
            return redirect(
                f"/admin/myapp/plumber/{plumber.id}/progress/"
            )

        FreeRewardHistory.objects.create(
            plumber=plumber,
            reward_product=rule.reward_product,
            quantity=1,
            note=f"Reward : {rule.reward_product}",
            given_date=date.today(),
        )

        messages.success(
            request,
            f"{rule.reward_product} Reward Given Successfully."
        )

        return redirect(
            f"/admin/myapp/plumber/{plumber.id}/progress/"
        )

@admin.register(RewardRule)
class RewardRuleAdmin(admin.ModelAdmin):
    list_display = (
        "purchase_product",
        "buy_quantity",
        "reward_product",
        "min_purchase",
        "max_purchase",
        "prize_type",
        "min_reward",
        "max_reward",
    )
    list_per_page = 50

    search_fields = (
        "purchase_product",
        "reward_product",
    )

@admin.register(ScratchCard)
class ScratchCardAdmin(admin.ModelAdmin):

    list_display = (
        "plumber",
        "purchase_amount",
        "reward_text",
        "note",
        "created_date",
        "is_scratched",
        "scratch_link",
        "copy_link",
        "whatsapp_link",
    )
    list_select_related = (
        "plumber",
        "reward_rule",
    )

    list_per_page = 50

    search_fields = (
        "plumber__name",
        "reward_text",
    )

    exclude = (
        "reward_rule",
        "reward_text",
        "is_scratched",
    )

    readonly_fields = (
        "token",
        "created_at",
    )

    def save_model(self, request, obj, form, change):

        rule = (
            RewardRule.objects
            .only(
                "id",
                "prize_type",
                "reward_product",
                "min_reward",
                "max_reward",
            )
            .filter(
                min_purchase__lte=obj.purchase_amount,
                max_purchase__gte=obj.purchase_amount
            )
            .first()
        )

        if rule:

            obj.reward_rule = rule

            if rule.prize_type == "Cash":

                amount = random.randint(
                    rule.min_reward,
                    rule.max_reward
                )

                obj.reward_text = f"₹{amount}"

            else:

                obj.reward_text = rule.reward_product

        super().save_model(request, obj, form, change)

    def created_date(self, obj):
        return obj.created_at.strftime("%d-%m-%Y %I:%M %p")

    created_date.short_description = "Created On"

    def scratch_link(self, obj):

        url = f"http://127.0.0.1:8000/scratch/{obj.token}/"

        return format_html(
            '<a href="{}" target="_blank">🔗 Open</a>',
            url
        )

    scratch_link.short_description = "Scratch Card"

    # ===========================
    # COPY LINK BUTTON
    # ===========================
    def copy_link(self, obj):

        url = f"http://127.0.0.1:8000/scratch/{obj.token}/"

        return format_html(
            """
            <button onclick="navigator.clipboard.writeText('{}');alert('Link Copied!');">
                📋 Copy
            </button>
            """,
            url
        )

    copy_link.short_description = "Copy Link"

    # ===========================
    # WHATSAPP
    # ===========================
    def whatsapp_link(self, obj):

        phone = "91" + obj.plumber.phone

        scratch_url = f"http://127.0.0.1:8000/scratch/{obj.token}/"

        message = f"""
🎉 Ashish Enterprises

Congratulations!

Your Scratch Card is Ready.

Click Below:

{scratch_url}

Scratch and Win 🎁
"""

        whatsapp = f"https://wa.me/{phone}?text={quote(message)}"

        return format_html(
            '<a href="{}" target="_blank">📲 WhatsApp</a>',
            whatsapp
        )

    whatsapp_link.short_description = "WhatsApp"

@admin.register(PurchaseHistory)
class PurchaseHistoryAdmin(admin.ModelAdmin):

    list_display = (
        "plumber",
        "product",
        "quantity",
        "rate_display",
        "total_display",
        "purchase_date",
        "note",
    )
    list_select_related = ("plumber", "product")
    list_per_page = 50
    search_fields = (
        "plumber__name",
        "product__name",
    )

    exclude = (
        "total",
    )

    list_filter = (
        "product",
        "purchase_date",
    )

    search_fields = (
        "plumber__name",
        "product__name",
        "note",
    )

    ordering = (
        "-purchase_date",
    )
    
    def save_model(self, request, obj, form, change):
        obj.total = obj.quantity * obj.rate
        super().save_model(request, obj, form, change)

    def rate_display(self, obj):
        return f"₹{obj.rate:,}"

    rate_display.short_description = "Rate"


    def total_display(self, obj):
        return f"₹{obj.total:,}"

    total_display.short_description = "Total"
    
@admin.register(FreeRewardHistory)
class FreeRewardHistoryAdmin(admin.ModelAdmin):

    list_display = (
        "plumber",
        "reward_product",
        "quantity",
        "given_date",
        "note",
    )

    list_select_related = ("plumber",)

    list_per_page = 50

    search_fields = (
        "plumber__name",
        "reward_product",
    )
    list_filter = (
        "reward_product",
        "given_date",
    )

    search_fields = (
        "plumber__name",
        "reward_product",
        "note",
    )

    ordering = (
        "-given_date",
    )