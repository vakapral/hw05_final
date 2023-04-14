from django import template

register = template.Library()


@register.filter
def addclass(field, css):
    return field.as_widget(attrs={'class': css})


@register.filter
def uglify(field):
    line = ''
    for k, v in enumerate(field):
        if k % 2 == 0:
            v = v.lower()
        else:
            v = v.upper()
        line = line + v
    return line
