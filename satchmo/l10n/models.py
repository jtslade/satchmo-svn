# -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext_lazy as _

CONTINENTS = (
    ('AF', _('Africa')),
    ('NA', _('North America')),
    ('EU',  _('Europe')),
    ('AS', _('Asia')),
    ('OC',  _('Oceania')),
    ('SA', _('South America')),
    ('AN', _('Antarctica'))
)

AREAS = (
    ('a', _('Another')),
    ('i', _('Island')),
    ('ar', _('Arrondissement')),
    ('at', _('Atoll')),
    ('ai', _('Autonomous island')),
    ('ca', _('Canton')),
    ('cm', _('Commune')),
    ('co', _('County')),
    ('dp', _('Department')),
    ('de', _('Dependency')),
    ('dt', _('District')),
    ('dv', _('Division')),
    ('em', _('Emirate')),
    ('gv', _('Governorate')),
    ('ic', _('Island council')),
    ('ig', _('Island group')),
    ('ir', _('Island region')),
    ('kd', _('Kingdom')),
    ('mu', _('Municipality')),
    ('pa', _('Parish')),
    ('pf', _('Prefecture')),
    ('pr', _('Province')),
    ('rg', _('Region')),
    ('rp', _('Republic')),
    ('sh', _('Sheading')),
    ('st', _('State')),
    ('sd', _('Subdivision')),
    ('sj', _('Subject')),
    ('ty', _('Territory')),
)



class Country(models.Model):
    """
    International Organization for Standardization (ISO) 3166-1 Country list
    
     * ``iso`` = ISO 3166-1 alpha-2
     * ``name`` = Official country names used by the ISO 3166/MA in capital letters
     * ``printable_name`` = Printable country names for in-text use
     * ``iso3`` = ISO 3166-1 alpha-3
     * ``numcode`` = ISO 3166-1 numeric
    
    Note::
        This model is fixed to the database table 'country' to be more general.
        Change ``db_table`` if this cause conflicts with your database layout.
        Or comment out the line for default django behaviour.
    
    """
    iso2_code = models.CharField(_('ISO alpha-2'), max_length=2, unique=True)
    name = models.CharField(_('Official name (CAPS)'), max_length=128)
    printable_name = models.CharField(_('Country name'), max_length=128)
    iso3_code = models.CharField(_('ISO alpha-3'), max_length=3, unique=True)
    numcode = models.PositiveSmallIntegerField(_('ISO numeric'), null=True)
    active = models.BooleanField(_('Country is active'), default=True)
    continent = models.CharField(_('Continent'), choices=CONTINENTS, max_length=2)
    admin_area = models.CharField(_('Administrative Area'), choices=AREAS, max_length=2, null=True)
    
    class Meta:
        verbose_name = _('Country')
        verbose_name_plural = _('Countries')
        ordering = ('name',)
        
    class Admin:
        list_display = ('printable_name', 'iso2_code',)
        list_filter = ('continent', 'active')
        search_fields = ('name', 'iso2_code', 'iso3_code')
        
        
    def __unicode__(self):
        return self.printable_name


class AdminArea(models.Model):
    """
    Administrative Area for a country.  For the US, this would be the states
    """
    country = models.ForeignKey(Country, edit_inline=models.TABULAR)
    name = models.CharField(_('Admin Area name'), max_length=50, core=True)
    abbrev = models.CharField(_('Postal Abbreviation'), max_length=3, null=False)

    class Meta:
        verbose_name = _('Administrative Area')
        verbose_name_plural = _('Administrative Areas')
        ordering = ('name',)

    def __unicode__(self):
        return self.name
