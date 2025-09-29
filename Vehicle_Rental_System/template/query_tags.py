from django import template

register = template.Library()

@register.simple_tag
def query_transform(request, **kwargs):
    """
    Alters the current request's query parameters with the provided kwargs.
    """
    updated = request.GET.copy()
    for k, v in kwargs.items():
        updated[k] = v
    return updated.urlencode()