from django.db import models


class Config(models.Model):
    storeName = models.CharField("Store Name",maxlength=100)
    
    
    def __str__(self):
        return self.storeName
        
    class Admin:
        pass