from django.shortcuts import render,redirect,get_object_or_404
from django.http import JsonResponse
from django.db.models import Sum,Q,IntegerField,F
from .models import (
    Plumber,
    Product,
    PurchaseHistory,
    RewardRule,
    FreeRewardHistory,
    ScratchCard,
)
from django.template.loader import render_to_string
from django.contrib.auth import authenticate, login,logout
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
import random
from django.contrib import messages
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.db.models.functions import Cast
from datetime import date
from django.core.cache import cache

def login_view(request):

    if request.user.is_authenticated:
        return redirect("/dashboard/")

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user:
            login(request, user)
            request.session.set_expiry(1000)
            request.session.modified = True
            return redirect("/dashboard/")

        return render(request, "login.html", {
            "error": "Invalid Username or Password"
        })

    return render(request, "login.html")

@login_required(login_url="/")
def dashboard(request):

    recent_purchases = PurchaseHistory.objects.select_related(
        "plumber"
    ).order_by("-purchase_date")[:5]

    top_plumbers = (
        PurchaseHistory.objects
        .values("plumber__name")
        .annotate(
            total=Coalesce(Sum("total"), 0)
        )
        .order_by("-total")[:5]
    )

    total_product_reward = (
        FreeRewardHistory.objects
        .annotate(
            amount=F("quantity") * F("unit_price")
        )
        .aggregate(
            total=Sum("amount")
        )["total"] or 0
    )

    cash_rewards = 0

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
            cash_rewards += int(
                reward.replace("₹", "").strip()
            )
        except (ValueError, AttributeError):
            pass

    context = {

        "plumbers": Plumber.objects.count(),

        "products": Product.objects.count(),

        "purchases": PurchaseHistory.objects.count(),

        "rules": RewardRule.objects.count(),

        "rewards": FreeRewardHistory.objects.count(),

        "scratch_cards": ScratchCard.objects.count(),

        "cash_rewards": cash_rewards,
        "total_reward_amount": total_product_reward + cash_rewards,

        "recent_purchases": recent_purchases,

        "top_plumbers": top_plumbers,

        "today": timezone.now(),

        "current": "dashboard",


    }

    return render(
        request,
        "dashboard.html",
        context
    )

def home(request):
    return render(request, "index.html")


def search_card(request):

    card = None
    show_reward = False

    if request.method == "POST":

        # Scratch Button
        if "scratch" in request.POST:

            card = get_object_or_404(
                ScratchCard.objects.select_related(
                    "plumber",
                    "reward_rule"
                ),
                id=request.POST["card_id"]
            )

            if not card.is_scratched:
                card.is_scratched = True
                card.save(update_fields=["is_scratched"])
                cache.delete("sidebar_total_rewards")

            show_reward = True

        # Search Button
        else:

            phone = request.POST.get("phone", "").strip()

            card = (
                ScratchCard.objects
                .select_related("plumber", "reward_rule")
                .filter(
                    plumber__phone=phone,
                    is_scratched=False
                )
                .first()
            )

    return render(request, "search.html", {
        "card": card,
        "show_reward": show_reward
    })

def logout_view(request):
    logout(request)
    return redirect("/")

def scratch_card(request, token):

    card = ScratchCard.objects.select_related(
        "plumber",
        "reward_rule"
    ).filter(
        token=token
    ).first()

    if not card:
        return render(request, "notfound.html")

    if card.is_scratched:
        return render(request, "used.html")

    # JavaScript se request aayegi jab scratch complete ho jayega
    if request.method == "POST":

        card.is_scratched = True
        card.save(update_fields=["is_scratched"])

        cache.delete("sidebar_total_rewards")

        return JsonResponse({
            "status": "success"
        })

    return render(request, "scratch.html", {
        "card": card
    })
@login_required(login_url="/")
def plumbers(request):

    search = request.GET.get("search", "")

    plumbers = Plumber.objects.only(
        "id",
        "name",
        "phone",
        "address"
    )

    if search:
        plumbers = plumbers.filter(name__icontains=search)

    # AJAX Request
    if request.headers.get("x-requested-with") == "XMLHttpRequest":

        html = render_to_string(
            "partials/plumber_table.html",
            {
                "plumbers": plumbers
            },
            request=request
        )

        return JsonResponse({
            "html": html
        })

    return render(
        request,
        "plumbers.html",
        {
            "plumbers": plumbers,
            "search": search,
            "current": "plumbers",
        }
    )

@login_required(login_url="/")
def add_plumber(request):

    if request.method == "POST":

        name = request.POST.get("name")
        phone = request.POST.get("phone")
        address = request.POST.get("address")

        Plumber.objects.create(
            name=name,
            phone=phone,
            address=address
        )

        return redirect("plumbers")

    return render(request, "add_plumber.html")


@login_required(login_url="/")
def edit_plumber(request, id):

    plumber = get_object_or_404(
        Plumber,
        id=id
    )

    if request.method == "POST":

        plumber.name = request.POST.get("name")
        plumber.phone = request.POST.get("phone")
        plumber.address = request.POST.get("address")

        plumber.save()

        return redirect("plumbers")

    return render(
        request,
        "add_plumber.html",
        {
            "plumber": plumber
        }
    )


@login_required(login_url="/")
def delete_plumber(request, id):

    plumber = get_object_or_404(
        Plumber,
        id=id
    )

    plumber.delete()

    return redirect("plumbers")

@login_required(login_url="/")
def products(request):

    search = request.GET.get("search", "")

    products = Product.objects.only(
        "id",
        "name"
    )

    if search:
        products = products.filter(name__icontains=search)

    if request.headers.get("x-requested-with") == "XMLHttpRequest":

        html = render_to_string(
            "partials/product_table.html",
            {
                "products": products
            },
            request=request
        )

        return JsonResponse({
            "html": html
        })

    return render(
        request,
        "products.html",
        {
            "products": products,
            "search": search,
            "current": "products",
        }
    )

@login_required(login_url="/")
def add_product(request):

    if request.method == "POST":

        Product.objects.create(
            name=request.POST.get("name")
        )

        return redirect("products")

    return render(
        request,
        "add_product.html"
    )


@login_required(login_url="/")
def edit_product(request, id):

    product = get_object_or_404(
        Product,
        id=id
    )

    if request.method == "POST":

        product.name = request.POST.get("name")

        product.save()

        return redirect("products")

    return render(
        request,
        "add_product.html",
        {
            "product": product
        }
    )


@login_required(login_url="/")
def delete_product(request, id):

    product = get_object_or_404(
        Product,
        id=id
    )

    product.delete()

    return redirect("products")

@login_required(login_url="/")
def product_progress(request, plumber_id):

    plumber = get_object_or_404(Plumber, id=plumber_id)

    rules = RewardRule.objects.filter(
        prize_type="Product"
    ).only(
        "id",
        "purchase_product",
        "reward_product",
        "buy_quantity"
    )

    purchase_totals = {
        row["product__name"]: row["total"]
        for row in (
            PurchaseHistory.objects
            .filter(plumber=plumber)
            .values("product__name")
            .annotate(total=Sum("quantity"))
        )
    }

    reward_totals = {
        row["reward_product"]: row["total"]
        for row in (
            FreeRewardHistory.objects
            .filter(plumber=plumber)
            .values("reward_product")
            .annotate(total=Sum("quantity"))
        )
    }

    progress = []

    for rule in rules:

        purchased = purchase_totals.get(rule.purchase_product, 0) or 0
        free_given = reward_totals.get(rule.reward_product, 0) or 0

        current = purchased - (free_given * rule.buy_quantity)

        if current < 0:
            current = 0

        percent = min(
            (current / rule.buy_quantity) * 100,
            100
        )

        progress.append({
            "rule_id": rule.id,
            "purchase_product": rule.purchase_product,
            "reward_product": rule.reward_product,
            "buy_quantity": rule.buy_quantity,
            "purchased": current,
            "free_given": free_given,
            "percent": percent,
            "eligible": current >= rule.buy_quantity,
        })

    return render(
        request,
        "product_progress.html",
        {
            "plumber": plumber,
            "progress": progress,
        },
    )

@login_required(login_url="/")
def purchase_history(request):

    search = request.GET.get("search", "")

    plumbers = Plumber.objects.all().order_by("name")

    if search:
        plumbers = plumbers.filter(
            name__icontains=search
        )

    if request.headers.get("x-requested-with") == "XMLHttpRequest":

        html = render_to_string(
            "partials/purchase_table.html",
            {
                "plumbers": plumbers
            },
            request=request
        )

        return JsonResponse({
            "html": html
        })

    return render(
        request,
        "purchase_history.html",
        {
            "plumbers": plumbers,
            "search": search,
            "current": "purchase_history",
        }
    )

@login_required(login_url="/")
def plumber_purchase_history(request, plumber_id):

    plumber = get_object_or_404(
        Plumber,
        id=plumber_id
    )

    purchases = (
        PurchaseHistory.objects
        .filter(plumber=plumber)
        .select_related("product")
        .order_by("-purchase_date")
    )

    return render(
        request,
        "plumber_purchase_history.html",
        {
            "plumber": plumber,
            "purchases": purchases,
            "current": "purchase_history",
        }
    )

@login_required(login_url="/")
def add_purchase(request):

    if request.method == "POST":

        plumber = get_object_or_404(
            Plumber,
            id=request.POST.get("plumber")
        )

        product = get_object_or_404(
            Product,
            id=request.POST.get("product")
        )

        quantity = int(request.POST.get("quantity"))
        rate = int(request.POST.get("rate"))

        PurchaseHistory.objects.create(

            plumber=plumber,

            product=product,

            quantity=quantity,

            rate=rate,

            total=quantity * rate,

            purchase_date=request.POST.get("purchase_date"),

            note=request.POST.get("note")

        )

        return redirect("purchase_history")

    return render(
        request,
        "add_purchase.html",
        {
            "plumbers": Plumber.objects.all(),
            "products": Product.objects.all(),
        }
    )


@login_required(login_url="/")
def edit_purchase(request, id):

    purchase = get_object_or_404(
        PurchaseHistory,
        id=id
    )

    if request.method == "POST":

        purchase.plumber = get_object_or_404(
            Plumber,
            id=request.POST.get("plumber")
        )

        purchase.product = get_object_or_404(
            Product,
            id=request.POST.get("product")
        )

        purchase.quantity = int(request.POST.get("quantity"))
        purchase.rate = int(request.POST.get("rate"))

        purchase.total = purchase.quantity * purchase.rate

        purchase.purchase_date = request.POST.get("purchase_date")

        purchase.note = request.POST.get("note")

        purchase.save()

        return redirect("purchase_history")

    return render(
        request,
        "add_purchase.html",
        {
            "purchase": purchase,
            "plumbers": Plumber.objects.all(),
            "products": Product.objects.all(),
        }
    )


@login_required(login_url="/")
def delete_purchase(request, id):

    purchase = get_object_or_404(
        PurchaseHistory,
        id=id
    )

    purchase.delete()

    return redirect("purchase_history")

@login_required(login_url="/")
def reward_rules(request):

    search = request.GET.get("search", "")

    rules = RewardRule.objects.only(
        "id",
        "purchase_product",
        "reward_product",
        "prize_type",
        "buy_quantity",
        "min_purchase",
        "max_purchase",
        "min_reward",
        "max_reward",
    )

    if search:

        rules = rules.filter(
            purchase_product__name__icontains=search
        )

    if request.headers.get("x-requested-with") == "XMLHttpRequest":

        html = render_to_string(
            "partials/reward_rule_table.html",
            {
                "rules": rules
            },
            request=request
        )

        return JsonResponse({
            "html": html
        })

    return render(
        request,
        "reward_rules.html",
        {
            "rules": rules,
            "search": search,
            "current": "reward_rules",
        }
    )


@login_required(login_url="/")
def add_reward_rule(request):

    if request.method == "POST":

        prize_type = request.POST.get("prize_type")

        if prize_type == "Cash":

            purchase_product = request.POST.get("cash_purchase_product")

        else:

            product = get_object_or_404(
                Product,
                id=request.POST.get("purchase_product")
            )

            purchase_product = product.name

        RewardRule.objects.create(

            min_purchase=request.POST.get("min_purchase"),

            max_purchase=request.POST.get("max_purchase"),

            prize_type=prize_type,

            purchase_product=purchase_product,

            buy_quantity=request.POST.get("buy_quantity") or 0,

            reward_product=request.POST.get("reward_product"),

            min_reward=request.POST.get("min_reward") or None,

            max_reward=request.POST.get("max_reward") or None,

        )

        return redirect("reward_rules")

    return render(
        request,
        "add_reward_rule.html",
        {
            "products": Product.objects.all(),
        }
    )


@login_required(login_url="/")
def edit_reward_rule(request, id):

    rule = get_object_or_404(
        RewardRule,
        id=id
    )

    if request.method == "POST":

        prize_type = request.POST.get("prize_type")

        rule.min_purchase = request.POST.get("min_purchase")

        rule.max_purchase = request.POST.get("max_purchase")

        rule.prize_type = prize_type

        if prize_type == "Cash":

            rule.purchase_product = request.POST.get(
                "cash_purchase_product"
            )

            rule.buy_quantity = 0

            rule.reward_product = ""

            rule.min_reward = request.POST.get("min_reward") or None

            rule.max_reward = request.POST.get("max_reward") or None

        else:

            product = get_object_or_404(
                Product,
                id=request.POST.get("purchase_product")
            )

            rule.purchase_product = product.name

            rule.buy_quantity = request.POST.get("buy_quantity")

            rule.reward_product = request.POST.get("reward_product")

            rule.min_reward = None

            rule.max_reward = None

        rule.save()

        return redirect("reward_rules")

    return render(
        request,
        "add_reward_rule.html",
        {
            "rule": rule,
            "products": Product.objects.all(),
        }
    )


@login_required(login_url="/")
def delete_reward_rule(request, id):

    rule = get_object_or_404(
        RewardRule,
        id=id
    )

    rule.delete()

    return redirect("reward_rules")

@login_required(login_url="/")
def reward_history(request):

    search = request.GET.get("search", "")

    rewards = FreeRewardHistory.objects.select_related(
        "plumber"
    ).all().order_by("-given_date")

    if search:

        rewards = rewards.filter(

            Q(plumber__name__icontains=search) |
            Q(reward_product__icontains=search) |
            Q(note__icontains=search)

        )

    if request.headers.get("x-requested-with") == "XMLHttpRequest":

        html = render_to_string(
            "partials/reward_history_table.html",
            {
                "rewards": rewards
            },
            request=request
        )

        return JsonResponse({
            "html": html
        })

    return render(
        request,
        "reward_history.html",
        {
            "rewards": rewards,
            "search": search,
            "current": "reward_history",
        }
    )

@login_required(login_url="/")
def delete_reward_history(request, id):

    reward = get_object_or_404(
        FreeRewardHistory,
        id=id
    )

    reward.delete()

    return redirect("reward_history")

@login_required(login_url="/")
def scratch_cards(request):

    search = request.GET.get("search", "")

    cards = ScratchCard.objects.select_related(
        "plumber"
    ).order_by("-created_at")

    if search:

        cards = cards.filter(

            Q(plumber__name__icontains=search) |
            Q(reward_text__icontains=search) |
            Q(note__icontains=search)

        )

    if request.headers.get("x-requested-with") == "XMLHttpRequest":

        html = render_to_string(

            "partials/scratch_card_table.html",

            {
                "cards": cards
            },

            request=request

        )

        return JsonResponse({

            "html": html

        })

    return render(

        request,

        "scratch_cards.html",

        {

            "cards": cards,
            "search": search,
            "current": "scratch_cards",

        }

    )


@login_required(login_url="/")
def add_scratch_card(request):

    plumbers = Plumber.objects.only(
        "id",
        "name"
    ).order_by("name")

    if request.method == "POST":

        plumber = get_object_or_404(
            Plumber,
            id=request.POST.get("plumber")
        )

        purchase_amount = int(
            request.POST.get("purchase_amount")
        )
        reward_type = request.POST.get("reward_type")

        note = request.POST.get("note")

        rule = RewardRule.objects.filter(
            prize_type=reward_type,
            min_purchase__lte=purchase_amount,
            max_purchase__gte=purchase_amount
        ).first()

        if not rule:

            messages.error(
                request,
                "No Reward Rule Found For This Purchase Amount."
            )

            return redirect("add_scratch_card")

        if rule.prize_type == "Cash":

            reward_text = f"₹{random.randint(rule.min_reward, rule.max_reward)}"

        else:

            reward_text = rule.reward_product

        ScratchCard.objects.create(

            plumber=plumber,

            purchase_amount=purchase_amount,
            reward_type=reward_type,

            note=note,

            reward_rule=rule,

            reward_text=reward_text

        )

        messages.success(
            request,
            "Scratch Card Created Successfully."
        )

        return redirect("scratch_cards")

    return render(

        request,

        "add_scratch_card.html",

        {

            "plumbers": plumbers,

            "current": "scratch_cards",

        }

    )


@login_required(login_url="/")
def delete_scratch_card(request, id):

    card = get_object_or_404(
        ScratchCard,
        id=id
    )

    card.delete()

    return redirect("scratch_cards")

@login_required(login_url="/")
def give_reward(request, plumber_id, rule_id):

    plumber = get_object_or_404(
        Plumber,
        id=plumber_id
    )

    rule = get_object_or_404(
        RewardRule,
        id=rule_id
    )

    purchase_data = PurchaseHistory.objects.filter(
        plumber_id=plumber.id,
        product__name=rule.purchase_product
    ).aggregate(total=Coalesce(Sum("quantity"), 0))

    reward_data = FreeRewardHistory.objects.filter(
        plumber_id=plumber.id,
        reward_product=rule.reward_product
    ).aggregate(total=Coalesce(Sum("quantity"), 0))

    purchased = purchase_data["total"]
    free_given = reward_data["total"]
    current = purchased - (free_given * rule.buy_quantity)

    if current < rule.buy_quantity:

        messages.error(
            request,
            "Reward not eligible."
        )

        return redirect(
            "product_progress",
            plumber_id=plumber.id
        )

    purchase = (
        PurchaseHistory.objects
        .filter(
            plumber_id=plumber.id,
            product__name=rule.purchase_product
        )
        .only("rate")
        .order_by("-purchase_date")
        .first()
    )

    price = purchase.rate if purchase else 0

    FreeRewardHistory.objects.create(
        plumber=plumber,
        reward_product=rule.reward_product,
        quantity=1,
        unit_price=price,
        note="Reward Given",
        given_date=date.today(),
    )
    cache.delete("sidebar_total_rewards")

    messages.success(
        request,
        "Reward Given Successfully."
    )

    return redirect(
        "product_progress",
        plumber_id=plumber.id
    )