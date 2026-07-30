from django.urls import path
from . import views

urlpatterns = [

    path("", views.login_view, name="login"),

    path("dashboard/", views.dashboard, name="dashboard"),

    path("search/", views.search_card, name="search"),

    path(
        "scratch/<uuid:token>/",
        views.scratch_card,
        name="scratch_card",
    ),
    path("logout/", views.logout_view, name="logout"),
    path("plumbers/", views.plumbers, name="plumbers"),

    path("plumbers/add/", views.add_plumber, name="add_plumber"),
    path("plumbers/<int:plumber_id>/progress/",views.product_progress,name="product_progress"),
    path("plumbers/<int:id>/edit/", views.edit_plumber, name="edit_plumber"),
    path("plumbers/<int:id>/delete/", views.delete_plumber, name="delete_plumber"),

    path("products/", views.products, name="products"),
    path("products/add/", views.add_product, name="add_product"),
    path("products/<int:id>/edit/", views.edit_product, name="edit_product"),
    path("products/<int:id>/delete/", views.delete_product, name="delete_product"),

    path("products/", views.products, name="products"),
    path("purchase-history/", views.purchase_history, name="purchase_history"),
    path("purchase-history/<int:plumber_id>/",views.plumber_purchase_history,name="plumber_purchase_history",),
    path("purchase-history/add/", views.add_purchase, name="add_purchase"),
    path("purchase-history/<int:id>/edit/", views.edit_purchase, name="edit_purchase"),
    path("purchase-history/<int:id>/delete/", views.delete_purchase, name="delete_purchase"),

    path("reward-rules/",views.reward_rules,name="reward_rules",),
    path("reward-rules/add/",views.add_reward_rule,name="add_reward_rule",),
    path("reward-rules/<int:id>/edit/",views.edit_reward_rule,name="edit_reward_rule",),
    path("reward-rules/<int:id>/delete/",views.delete_reward_rule,name="delete_reward_rule",),
    path("reward-history/",views.reward_history,name="reward_history",),
    
    path("reward-history/<int:id>/delete/",views.delete_reward_history,name="delete_reward_history",),

    path("scratch-cards/", views.scratch_cards, name="scratch_cards"),
    path("scratch-cards/add/", views.add_scratch_card, name="add_scratch_card"),
    path("scratch-cards/<int:id>/delete/", views.delete_scratch_card, name="delete_scratch_card"),

    path("plumbers/<int:plumber_id>/give-reward/<int:rule_id>/",views.give_reward,name="give_reward",),
]