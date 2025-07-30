from django.db.models import Q

from goods.models import Products


def q_search(query):
    if query.isdigit() and len(query) <= 5:
        return Products.objects.filter(pk=int(query))

    keywords = [word for word in query.split() if len(word) > 2]
    print(keywords)

    q_objects = Q()

    for word in keywords:
        q_objects |= Q(description__icontains=word)
        q_objects |= Q(name__icontains=word)

    return Products.objects.filter(q_objects)