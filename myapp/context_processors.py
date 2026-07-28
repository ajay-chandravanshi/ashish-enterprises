from .models import FreeRewardHistory, ScratchCard
from django.db.models import Sum, F

def sidebar_data(request):

    product_total = (
        FreeRewardHistory.objects
        .annotate(
            amount=F("quantity") * F("unit_price")
        )
        .aggregate(
            total=Sum("amount")
        )["total"] or 0
    )

    cash_total = 0

    cards = ScratchCard.objects.filter(
        reward_rule__prize_type="Cash",
        is_scratched=True
    )

    for card in cards:

        try:

            cash_total += int(
                card.reward_text.replace("₹", "").strip()
            )

        except:

            pass

    total_rewards_given = product_total + cash_total

    return {

        "total_rewards_given": total_rewards_given,

    }