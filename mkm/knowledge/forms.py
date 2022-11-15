from django import forms
from django.forms import ModelForm
from knowledge.models import *
from django.utils.translation import gettext_lazy as _


class AuthorForm(ModelForm):

    scopus_id = forms.IntegerField(required=False)
    ciencia_id = forms.CharField(required=False)
    orcid_id = forms.CharField(required=False)

    class Meta:
        model = Author
        fields = ["scopus_id", "ciencia_id", "orcid_id"]
        labels = {
            "scopus_id": _("Scopus ID"),
            "ciencia_id": _("Ciência ID"),
            "orcid_id": _("ORCID ID"),
        }
        # help_texts = {'scopus_id': _('This is a help text.')}
