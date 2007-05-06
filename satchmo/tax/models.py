"""
Store tables used to calculate tax on a product
"""

from django.db import models
from satchmo.i18n.models import Area, Country
from satchmo.shop.utils.validators import MutuallyExclusiveWithField
from django.utils.translation import gettext_lazy as _
from django.core import validators

class TaxClass(models.Model):
    """
    Type of tax that can be applied to a product.  Tax
    might vary based on the type of product.  In the US, clothing could be 
    taxed at a different rate than food items.
    """
    title = models.CharField(_("Title"), maxlength=20, help_text=_("Displayed title of this tax"))
    description = models.CharField(_("Description"), maxlength=30,help_text=_('Description of products that would be taxed'))
    
    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = _("Tax Class")
        verbose_name_plural = _("Tax Classes")
    
    class Admin:
        pass
        

taxrate_zoneandcountry_zone_validator = MutuallyExclusiveWithField('taxCountry')
taxrate_zoneandcountry_country_validator = MutuallyExclusiveWithField('taxZone')

class TaxRate(models.Model):
    """
    Actual percentage tax based on area and product class
    """
    taxClass = models.ForeignKey(TaxClass)
    taxZone = models.ForeignKey(Area, blank=True, null=True, 
                                validator_list=[taxrate_zoneandcountry_zone_validator])
    taxCountry = models.ForeignKey(Country, blank=True, null=True,
                                   validator_list=[taxrate_zoneandcountry_country_validator])
    percentage = models.FloatField(_("Percentage"), max_digits=7, decimal_places=6, help_text=_("% tax for this area and type"))
    
    def _country(self):
        if self.taxZone:
            return self.taxZone.country.name
        else:
            return self.taxCountry.name
    country = property(_country)
    
    def _display_percentage(self):
        return "%#2.2f%%" % (100*self.percentage)
    display_percentage = property(_display_percentage) 
    
    def __str__(self):
        return ("%s - %s" % (self.taxClass,
                             self.taxZone and self.taxZone or self.taxCountry))
    
    def save(self):
        if self.taxZone and not self.taxCountry or \
            not self.taxZone and self.taxCountry:
            super(TaxRate, self).save()
        else:
            raise validators.ValidationError(_("You must choose a zone or a country"))
          
    class Admin:
        list_display = ("taxClass", "taxZone", "taxCountry", "display_percentage")

    class Meta:
        verbose_name = _("Tax Rate")
        verbose_name_plural = _("Tax Rates")