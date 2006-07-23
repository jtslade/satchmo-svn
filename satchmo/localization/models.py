from django.db import models


SUBDIVISION = (
    ('ar', _('Autonomous region')),
    ('co', _('County')),
    ('fd', _('Federal district')),
    ('mu', _('Municipality')),
    ('pr', _('Province')),
    ('sm', _('Special municipality')),
    ('st', _('State')),
    ('ty', _('Territory')),
)

REGION = (
    ('a',   _('Africa')),
    ('an',  _('America, Nort')),
    ('as',  _('America, Central and South')),
    ('ac',  _('America, Caribbean')),
    ('asc', _('Asia, Central')),
    ('ase', _('Asia, Eastern and Southeastern')),
    ('asw', _('Asia, Southern and Western')),
    ('ee',  _('Europe, Eastern')),
    ('ew',  _('Europe, Western')),
    ('o',   _('Oceania')),
    ('oa',  _('Ocean, Atlantic')),
    ('oi',  _('Ocean, Indian')),
    ('os',  _('Oceans, Pacific, Southern and Artic')),
)


class Country(models.Model):
    """Country or territory.

'main_subdiv' is the name used for primary subdivision in the country,
as state in U.S.
    """
    alpha2_code = models.CharField(_('2 letter ISO code'), maxlength=2,
        primary_key=True)
    alpha3_code = models.CharField(_('3 letter ISO code'), maxlength=3)
    name = models.CharField(_('official english name'), maxlength=52,
        unique=True)
    region = models.CharField(_('geographical region'), maxlength=3,
        choices=REGION)
    from_country = models.CharField(_('from'), maxlength=3)
    main_subdiv = models.CharField(_('primary subdivision'), maxlength=2,
        choices=SUBDIVISION)
    display = models.BooleanField (_('display'), default=True,
        help_text=_('Designates whether the country is shown.'))

#    address_format = models.ForeignKey(AddressFormat)
#, related_name='format')
#default=1)

#    alpha3_code = models.CharField(_('3 letter ISO code'), maxlength=3,
#        unique=True)
#    is_subdivision = models.BooleanField(_('subdivision'), default=False,
#        help_text=_('Designates whether the country needs the primary \
#subdivision for the mail delivery.'))
#'need_subdiv' indicates if is necessary the subdivision for the mail address.

    class Meta:
        verbose_name = _('country')
        verbose_name_plural = _('countries')
        ordering = ['name']
    class Admin:
        """
        fields = (
            (_('Sorry! Not allowed to add or modify items in this model.'), {
                'fields': ('alpha2_code',)
            }),
        )
        """
        list_display = ('name', 'alpha2_code', 'alpha3_code', 'from_country',
                        'display')
        list_filter = ('region', 'from_country', 'display')
        search_fields = ('name', 'alpha2_code', 'alpha3_code')

    def __str__(self):
        if self.alpha3_code:
            return self.alpha3_code
        else:
            return self.alpha2_code

    def _get_name(self):
        if self.alpha3_code:
            return "%s (%s)" % (self.name, self.alpha3_code)
        else:
            return "%s (%s)" % (self.name, self.alpha2_code)
    country_id = property(_get_name)


class PrimarySubdivision(models.Model):
    """The major subdivision of the country, known as the state, province,
county, etc, depending on the country.

In some countries this subdivision is necessary for the mail address.
In others it is omitted, and in others it is either optional,
or needed in some cases but omitted in others.
    """
    country = models.ForeignKey(Country)
    id_name = models.CharField(_('name identifier'), maxlength=5,
        primary_key=True)
    name = models.CharField(_('name'), maxlength=50)
    iso_code = models.CharField(_('ISO 3166-2 code'), maxlength=3)
    main_subdiv = models.CharField(_('primary subdivision'), maxlength=2,
        choices=SUBDIVISION)

    class Meta:
        verbose_name = _('primary subdivision')
        verbose_name_plural = _('primary subdivisions')
        ordering = ['country']
        unique_together = (('country', 'name'),)
    class Admin:
        """
        fields = (
            (_('Sorry! Not allowed to add or modify items in this model.'), {
                'fields': ('code',)
            }),
        )
        """
        list_display = ('country', 'name', 'iso_code')
        search_fields = ('name')

    def __str__(self):
        return "%s (%s)" % (self.iso_code, self.name)


class TimeZone(models.Model):
    """The time zones for each country or territory.
    """
    country = models.ForeignKey(Country)
    zone = models.CharField(_('time zone'), maxlength=32, unique=True)

    class Meta:
        verbose_name = _('time zone')
        verbose_name_plural = _('time zones')
        ordering = ['country']
    class Admin:
        list_display = ('country', 'zone')
        search_fields = ('country')

    def __str__(self):
        return "%s" % (self.zone)

