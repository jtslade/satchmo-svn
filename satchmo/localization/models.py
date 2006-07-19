from django.db import models


SUBDIVISION_CHOICES = (
    ('ar', _('Autonomous region')),
    ('co', _('County')),
    ('fd', _('Federal district')),
    ('mu', _('Municipality')),
    ('pr', _('Province')),
    ('sm', _('Special municipality')),
    ('st', _('State')),
    ('ty', _('Territory')),
)

ZONE_CHOICES = (
    (1, _('North America')),
    (2, _('Africa')),
    (34, _('Europe')),
    (5, _('Mexico, Central and South America, West Indies')),
    (6, _('South Pacific and Oceania')),
    (7, _('Russia and its vicinity')),
    (8, _('East Asia')),
    (9, _('West, South and Central Asia, Middle East')),
)


class Country(models.Model):
    """Country model.

'main_subdiv' is the name used for primary subdivision in the country,
as state in U.S.
    """
    alpha2_code = models.CharField(_('2 letter ISO code'), maxlength=5,
        primary_key=True)
    name = models.CharField(_('official english name'), maxlength=52,
        unique=True)
    zone = models.PositiveSmallIntegerField(_('geographic zone'), maxlength=1,
        choices=ZONE_CHOICES)
    main_subdiv = models.CharField(_('primary subdivision'), maxlength=2,
        choices=SUBDIVISION_CHOICES)
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
        list_display = ('name', 'alpha2_code', 'zone', 'main_subdiv',
                        'display')
        list_filter = ('zone', 'display',)
        search_fields = ('name', 'alpha2_code')

    def __str__(self):
        return "%s (%s)" % (self.name, self.alpha2_code)


class PrimarySubdivision(models.Model):
    """The major subdivision of the country, known as the state, province,
county, etc, depending on the country.

In some countries this subdivision is necessary for the mail address.
In others it is omitted, and in others it is either optional,
or needed in some cases but omitted in others.
    """
    country = models.ForeignKey(Country)
    id_name = models.CharField(_('name identifier'), maxlength=8,
        primary_key=True)
    name = models.CharField(_('name'), maxlength=50)
    iso_code = models.CharField(_('ISO 3166-2 code'), maxlength=3)
    main_subdiv = models.CharField(_('primary subdivision'), maxlength=2,
        choices=SUBDIVISION_CHOICES)

    class Meta:
        verbose_name = _('primary subdivision')
        verbose_name_plural = _('primary subdivisions')
        ordering = ['country', 'name']
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
        search_fields = ('name', 'iso_code')

    def __str__(self):
        return "%s (%s)" % (self.iso_code, self.name)
