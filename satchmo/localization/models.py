from django.db import models

SUBDIVISION_CHOICES = (
    ('CO', _('County')),
    ('PR', _('Province')),
    ('ST', _('State')),
)


class AddressFormat(models.Model):
    """
    Format to indicate the order of lines in mail address.

        Whatever mail address is compound of the following lines although
        some countries use a different order:

            Person's name
            Department (if any)
            Institution or company (if any)
            Street address (or Post Office Box)
            City line
            Postal code
            Country name

        For domestic mail (mail within country), is not necessary the country name.
    """
    LINE_CHOICES = (
        (1, _('line 1')),
        (2, _('line 2')),
        (3, _('line 3')),
        (4, _('line 4')),
        (5, _('line 5')),
        (6, _('line 6')),
        (7, _('line 7')),
        (8, _('line 8')),
    )

    description = models.CharField(_('description'), maxlength=24)
    name = models.PositiveSmallIntegerField(_('name'), maxlength=1,
        choices=LINE_CHOICES)
    department = models.PositiveSmallIntegerField(_('department'),
        maxlength=1, choices=LINE_CHOICES)
    company = models.PositiveSmallIntegerField(_('institution or company'),
        maxlength=1, choices=LINE_CHOICES)
    street1 = models.PositiveSmallIntegerField(_('street 1'), maxlength=1,
        choices=LINE_CHOICES)
    street2 = models.PositiveSmallIntegerField(_('street 2'), maxlength=1,
        choices=LINE_CHOICES)    
    city = models.PositiveSmallIntegerField(_('city'), maxlength=1,
        choices=LINE_CHOICES)
    postal_code = models.PositiveSmallIntegerField(_('postalcode'), maxlength=1,
        choices=LINE_CHOICES)
    country_ln = models.PositiveSmallIntegerField(_('country'), maxlength=1,
        choices=LINE_CHOICES)

    class Meta:
        verbose_name = _('address format')
        verbose_name_plural = _('address formats')
    class Admin:
        #fields = (
        #    (_('Sorry! Not allowed to add or modify items in this model.'), {
        #        'fields': ('description',)
        #    }),
        #)
        pass
        
    def __str__(self):
        return self.description 


class Country(models.Model):
    """
    Country model

    'need_subdiv' indicates if is necessary the subdivision for the mail address.
    'main_subdiv' is the name used for primary subdivision in the country,
    as state is in U.S.
    
    """
    alpha3_code = models.CharField(_('3 letter ISO code'), maxlength=3,
        primary_key=True)
    alpha2_code = models.CharField(_('2 letter ISO code'), maxlength=2,
        unique=True)
    name = models.CharField(_('official country name in english'),
        maxlength=52, unique=True, core=True)
    is_subdivision = models.BooleanField(_('subdivision'), default=False,
        help_text=_('Designates whether the country needs the primary \
subdivision (i.e. state, province or county.'))
    main_subdiv = models.CharField(_('type of primay subdivision'),
        maxlength=2, choices=SUBDIVISION_CHOICES)
    address_format = models.ForeignKey(AddressFormat)
#, related_name='format')
#default=1)

    int_dialcode = models.PositiveSmallIntegerField(
        _('international dialing code'), maxlength=3)

    class Meta:
        verbose_name = _('country')
        verbose_name_plural = _('countries')
        ordering = ['alpha3_code']
    class Admin:
        #fields = (
        #    (_('Sorry! Not allowed to add or modify items in this model.'), {
        #        'fields': ('alpha2_code',)
        #    }),
        #)
        list_display = ('name', 'alpha3_code', 'alpha2_code', 'int_dialcode',
                        'is_subdivision')
        list_filter = ('is_subdivision',)
        search_fields = ('name', 'alpha3_code')

    def __str__(self):
        return "%s - %s" % (self.alpha3_code, self.name)


class PrimarySubdivision(models.Model):
    """
    The major subdivision of the country, known as the state, province,
    county, etc, depending on the country.

    In some countries this subdivision is necessary for the mail address.
    In others it is omitted, and in others it is either optional,
    or needed in some cases but omitted in others.
    """
    country = models.ForeignKey(Country)
    name = models.CharField(_('subdivision name'), maxlength=50)
    code = models.CharField(_('code'), maxlength=4)

    class Meta:
        verbose_name = _('primary subdivision')
        verbose_name_plural = _('primary subdivisions')
        ordering = ['country']
        unique_together = (('country', 'code'),)
    
    class Admin:
        #fields = (
        #    (_('Sorry! Not allowed to add or modify items in this model.'), {
        #        'fields': ('code',)
        #    }),
        #)
        list_display = ('code', 'name', 'country')
        search_fields = ('name')

    def __str__(self):
        return "%s (%s)" % (self.code, self.name)