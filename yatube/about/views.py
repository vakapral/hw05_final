from django.views.generic.base import TemplateView


# Create your views here.
class AboutAuthorView(TemplateView):
    template_name = 'about/author/'


class AboutTechView(TemplateView):
    template_name = 'about/tech/'