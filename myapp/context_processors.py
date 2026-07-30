from django.core.cache import cache
from django.db.models import Sum, F

from .models import FreeRewardHistory, ScratchCard


def sidebar_data(request):
    # Cache 60 seconds
    total_rewards_given = cache.get("sidebar_total_rewards")

    if total_rewards_given is None:

        # Product reward total
        product_total = (
            FreeRewardHistory.objects
            .annotate(amount=F("quantity") * F("unit_price"))
            .aggregate(total=Sum("amount"))["total"] or 0
        )

        # Sirf reward_text field lo (poora object nahi)
        cash_total = 0

        reward_list = (
            ScratchCard.objects
            .filter(
                reward_rule__prize_type="Cash",
                is_scratched=True
            )
            .values_list("reward_text", flat=True)
        )

        for reward in reward_list:
            try:
                cash_total += int(reward.replace("₹", "").strip())
            except (ValueError, AttributeError):
                pass

        total_rewards_given = product_total + cash_total

        cache.set(
            "sidebar_total_rewards",
            total_rewards_given,
            60
        )

    return {
        "total_rewards_given": total_rewards_given,
    }