from django.views.generic import TemplateView


class IndexView(TemplateView):
    template_name = "main/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "ModaHouse - Главная"
        context['content'] = "Магазин мебели ModaHouse"
        return context


class AboutView(TemplateView):
    template_name = "main/about.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "ModaHouse - О нас"
        context['content'] = "О нас"
        context['text_on_page'] = "Мы создаём мебель, которая превращает ваш дом в уютное и стильное пространство, " \
                                  "где каждая деталь продумана для комфорта и вдохновения."
        return context
