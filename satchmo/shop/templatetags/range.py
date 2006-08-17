from django import template

register = template.Library()

def template_range(value):
    '''Return a range 1..value'''
    #return range(1,1+value)
    return range(value)
    
register.filter('template_range',range)