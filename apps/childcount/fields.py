
#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: henrycg

"""Useful form fields and widgets for
dealing with health IDs.
"""

from django.utils.translation import ugettext as _
from django.forms.fields import CharField
from django.forms import ModelForm
from django import forms
from django.forms import TextInput
from django.forms.util import ValidationError

from childcount.models.Patient import Patient

class HealthIdWidget(forms.TextInput):
    """Defines a widget for health IDs
    that looks like normal text input box but
    displays health IDs nicely.
    """

    def _format_value(self, value):
        if value is None:
            return ''
        
        if isinstance(value, (int, long)):
            return Patient.objects.get(pk=value).health_id.upper()
        return value.upper()

    def _has_changed(self, initial, data):
        return super(HealthIdWidget, self).has_changed(self._format_value(initial), data)

    def render(self, name, value, attrs=None):
        value = self._format_value(value)
        return super(HealthIdWidget, self).render(name, value, attrs)

class HealthIdField(forms.Field):
    """A form field for health IDs
    that does validation of an inputted
    health ID against the existing IDs
    in the database.
    """

    widget = HealthIdWidget

    def clean(self, value):
        super(HealthIdField, self).clean(value)

        value = super(HealthIdField, self).clean(value).upper()
        value = value.strip()

        if value == '': return None
        try:
            p = Patient.objects.get(health_id=value)
        except Patient.DoesNotExist:
            raise ValidationError(_("There is no patient with \
                health ID %(hid)s") % {'hid': value})
        return p

class PatientForm(ModelForm):
    """A Django form for editing :class:`childcount.models.Patient`
    objects.
    Uses the custom health ID input fields.
    """

    household = HealthIdField(required=True)
    mother = HealthIdField(required=False)

    class Meta:
        model = Patient
        exclude = ['health_id']

    def __init__(self, *args, **kwargs):
        super(PatientForm, self).__init__(*args, **kwargs)
        patients = Patient.objects.filter(location=self.instance.location)

