from django.db import models


class ModelBase(models.Model):

    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        abstract = True


class BaseEmpresa(ModelBase):
    empresas = models.ForeignKey("empresas.Empresa", on_delete=models.CASCADE)

    class Meta:
        abstract = True
