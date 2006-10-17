# Copyright © 2006 Jonás Melián. All rights reserved.
# Licensed under the New BSD license

from django.db import models


CONTINENT = (
    ('af', _('Africa')),
    ('am', _('America')),
    ('e',  _('Europe')),
    ('as', _('Asia')),
    ('o',  _('Oceania')),
)

REGION = (
    ('af.e',  _('Eastern Africa')),
    ('af.m',  _('Middle Africa')),
    ('af.n',  _('Northern Africa')),
    ('af.s',  _('Southern Africa')),
    ('af.w',  _('Western Africa')),
    ('am.ca', _('Caribbean')),
    ('am.c',  _('Central America')),
    ('am.s',  _('South America')),
    ('am.n',  _('Northern America')),
    ('as.c',  _('Central Asia')),
    ('as.e',  _('Eastern Asia')),
    ('as.s',  _('Southern Asia')),
    ('as.se', _('South-Eastern Asia')),
    ('as.w',  _('Western Asia')),
    ('e.e',   _('Eastern Europe')),
    ('e.n',   _('Northern Europe')),
    ('e.s',   _('Southern Europe')),
    ('e.w',   _('Western Europe')),
    ('o.a',   _('Australia and New Zealand')),
    ('o.me',  _('Melanesia')),
    ('o.mi',  _('Micronesia')),
    ('o.p',   _('Polynesia')),
)

AREA = (
    ('a', _('Another')),
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
    ('i', _('Island')),
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

POSITION = (
    ('l', _('Left')),
    ('c', _('Center')),
    ('r', _('Right')),
)


class Language(models.Model):
    """Languages more common.

'synonym' field is used for some languages that are called with
another name too.
    """
    name = models.CharField(_('language name'), maxlength=24,
        unique=True)
    iso3_code = models.CharField(_('alpha-3 ISO code'), maxlength=3,
        primary_key=True)
    iso2_code = models.CharField(_('alpha-2 ISO code'), maxlength=2,
        unique=True)
    synonym = models.CharField(_('language synonym'), maxlength=24)
    display = models.BooleanField (_('display'), default=False,
        help_text=_('Designates whether the language is shown.'))

    class Meta:
        verbose_name = _('language')
        verbose_name_plural = _('languages')
        ordering = ['name']
    class Admin:
        list_display = ('name', 'iso3_code', 'iso2_code', 'synonym',
                        'display')
        list_filter = ('display',)
        search_fields = ('name', 'synonym', 'iso3_code', 'iso2_code')

    def __str__(self):
        return self.iso3_code


class Country(models.Model):
    """Country or territory.

iso2_code and iso3_code are ISO 3166-1 codes.
    """
    name = models.CharField(_('country name'), maxlength=56,
        unique=True)
    iso3_code = models.CharField(_('alpha-3 ISO code'), maxlength=3,
        primary_key=True)
    iso2_code = models.CharField(_('alpha-2 ISO code'), maxlength=2,
        unique=True)
    region = models.CharField(_('geographical region'), maxlength=5,
        choices=REGION)
    territory_of = models.CharField(_('territory of'), maxlength=3)
    adm_area = models.CharField(_('administrative area'), maxlength=2,
        choices=AREA)
    display = models.BooleanField(_('display'), default=True,
        help_text=_('Designates whether the country is shown.'))

    class Meta:
        verbose_name = _('country')
        verbose_name_plural = _('countries')
        ordering = ['name']
    class Admin:
        """
        fields = (
            (_('Sorry! Not allowed to add or modify items in this model.'), {
                'fields': ('iso3_code',)
            }),
        )
        """
        list_display = ('name', 'iso3_code', 'iso2_code', 'territory_of',
                        'adm_area', 'display')
        list_filter = ('region', 'territory_of', 'display')
        search_fields = ('name', 'iso3_code', 'iso2_code')

    def __str__(self):
        return self.iso3_code

    def _get_name(self):
        return "%s (%s)" % (self.name, self.iso3_code)
    country_id = property(_get_name)


class CountryLanguage(models.Model):
    """Countries with its languages.
    """
    country = models.ForeignKey(Country, edit_inline=models.TABULAR,
        core=True)
    language = models.ForeignKey(Language)
    regional_lang = models.BooleanField(_('regional'), default=False,
        help_text=_('Designates whether is a regional language.'))
    identifier = models.CharField(_('identifier'), maxlength=5,
        primary_key=True)

    class Meta:
        verbose_name = _('country & language')
        verbose_name_plural = _('countries & languages')
        ordering = ['country']
    class Admin:
        list_display = ('country', 'language', 'regional_lang')
        list_filter = ('regional_lang',)
        search_fields = ('country', 'language')

    def __str__(self):
        return "%s - %s" % (self.country, self.language)


class Area(models.Model):
    """Top-level area division in the country, such as
state, district, province, island, region, etc.

In some countries is necessary for the mail address.
In others it is omitted, and in others it is either optional,
or needed in some cases but omitted in others.
    """
    country = models.ForeignKey(Country, edit_inline=models.TABULAR,
        core=True)
    name_id = models.CharField(_('name identifier'), maxlength=6,
        primary_key=True)
    name = models.CharField(_('area name'), maxlength=40)
    alt_name = models.CharField(_('area alternate name'), maxlength=32)
    abbrev = models.CharField(_('postal abbreviation'), maxlength=3)
    reg_area = models.CharField(_('regional administrative area'), maxlength=1,
        choices=AREA)

    class Meta:
        verbose_name = _('area')
        verbose_name_plural = _('areas')
        ordering = ['country']
        unique_together = (('country', 'name'),)
    class Admin:
        list_display = ('country', 'name', 'alt_name', 'abbrev', 'reg_area')
        search_fields = ('name')

    def __str__(self):
        if self.abbrev:
            return "%s (%s)" % (self.abbrev, self.name)
        else:
            return self.name


class TimeZone(models.Model):
    """The time zones for each country or territory.
    """
    country = models.ForeignKey(Country, edit_inline=models.TABULAR,
        core=True)
    zone = models.CharField(_('time zone'), maxlength=32,
        unique=True)

    class Meta:
        verbose_name = _('time zone')
        verbose_name_plural = _('time zones')
        ordering = ['country']
    class Admin:
        list_display = ('country', 'zone')
        search_fields = ('country')

    def __str__(self):
        return self.zone


class Phone(models.Model):
    """Information related to phones as country code, lengths, and prefixes.
    """
    country = models.ForeignKey(Country, edit_inline=models.TABULAR,
        core=True)
    code = models.PositiveSmallIntegerField(_('country code'), null=True)
    ln_area = models.CharField(_('length of area code'), maxlength=10)
    ln_sn = models.CharField(_('length of subscriber number (SN)'),
        maxlength=8)
    ln_area_sn = models.CharField(_('length of area code and SN'),
        maxlength=8)
    nat_prefix = models.CharField(_('national prefix'), maxlength=2)
    int_prefix = models.CharField(_('international prefix'), maxlength=4)

    class Meta:
        verbose_name = _('phone')
        verbose_name_plural = _('phones')
        ordering = ['country']
    class Admin:
        list_display = ('country', 'code', 'ln_area', 'ln_sn', 'ln_area_sn',
                        'nat_prefix', 'int_prefix')
        search_fields = ('country', 'code')

    def __str__(self):
        if self.code:
            return "%s" % self.code


"""
class AddressFormat(models.Model):
    '''Address formats for the correct mail delivery.
    '''
    country = models.ForeignKey(Country, edit_inline=models.TABULAR, core=True)
    name = models.CharField(_('name of person'), maxlength=8)
    address = models.CharField(_('street address'), maxlength=8)
    locality = models.CharField(_('locality line'), maxlength=16)
    postalcode = models.CharField(_('postal code'), maxlength=64)
    aligment = models.CharField(_('alignment of lines'), maxlength=1,
        choices=POSITION)
    position = models.CharField(_('position on the envelope'), maxlength=1,
        choices=POSITION)

    class Meta:
        verbose_name = _('address format')
        verbose_name_plural = _('address formats')
        ordering = ['country']
    class Admin:
        list_display = ('country', 'name', 'address', 'locality',
                        'postalcode', 'aligment', 'position')
        search_fields = ('country')

    def __str__(self):
        return "%s" % (self.locality)
"""
