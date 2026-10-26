from django import template

register = template.Library()


@register.filter
def field_for(form, suffix):
    name = "size_%s" % suffix
    return form[name]
