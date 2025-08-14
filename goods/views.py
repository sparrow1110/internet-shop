from django.http import Http404
from django.views.generic import DetailView, TemplateView
from goods.models import Categories, Products
from goods.utils import q_search


class CatalogView(TemplateView):
    template_name = "goods/catalog.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "ModaHouse - Каталог"
        slug_url = self.kwargs.get("category_slug")
        if slug_url:
            if slug_url != "all":
                category = Categories.objects.get(slug=self.kwargs["category_slug"])
                context['category'] = category.name
            else:
                context['category'] = "Все товары"
        return context


class ProductView(DetailView):
    template_name = "goods/product.html"
    slug_url_kwarg = "product_slug"
    context_object_name = "product"

    def get_object(self, queryset=None):
        product = Products.objects.get(slug=self.kwargs[self.slug_url_kwarg])
        return product

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.object.name
        return context
