from django.core.cache import cache

from category.models import Category


def categories(request):
    cats = cache.get("categories")
    if not cats:
        cats = [
            cat
            for cat in sorted(
                Category.objects.all(),
                key=lambda c: float(c.ordering_weight)
                if c.ordering_weight
                else float(c.id),
            )
        ]
        cache.set("categories", cats, 300)

    return {"categories": cats}
