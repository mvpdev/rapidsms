from django import forms
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User, Group
from django.forms.util import ErrorList

from childcount.forms.base import BaseForm, BaseModelForm
from childcount.models.general import  Case
from reporters.models import Reporter, ReporterGroup

from urllib import quote


class MessageForm(BaseForm):
    message = forms.CharField(
        label=_("Message text"),
        required=True,
# oh if only this worked properly
#        widget = forms.Textarea(attrs={"class":"span-6", "style":
#            "height; 2em"})
    )

    groups = forms.MultipleChoiceField(
        label=_("Groups"),
        required=False,
        widget=forms.CheckboxSelectMultiple())

    users = forms.MultipleChoiceField(
        label=_("Users"),
        required=False,
        widget=forms.CheckboxSelectMultiple())

    def clean(self):
        data = self.cleaned_data
        if data.get("message"):
            # the http messaging pushes message through a URL
            # which means that you can only do ASCII so we'll check
            # its valid here
            try:
                quote(data.get("message"))
            except KeyError:
                msg = _("You can only specify ASCII characters "\
                        "in the message.")
                self._errors["message"] = ErrorList([msg, ])
        if not data.get("groups") and not data.get("users"):
            msg = _("You must specify either one or more groups or users.")
            self._errors["groups"] = ErrorList([msg, ])

        return super(MessageForm, self).clean()

    def __init__(self, *args, **kw):
        super(MessageForm, self).__init__(*args, **kw)

        groups = [(str(g.id), g.title) for g in ReporterGroup.objects.all()]
        users = []
        for p in Reporter.objects.all().order_by('last_name'):
            if p.first_name and p.last_name:
                users.append([str(p.id), "%s %s" % (p.first_name, \
                                                    p.last_name)])
            else:
                users.append([str(p.id), "%s (name not entered)"\
                               % p.connection().identity])

        self.fields["groups"].choices = groups
        self.fields["users"].choices = users


class CaseForm(BaseModelForm):

    class Meta:
        model = Case
        exclude = ('created_at', 'updated_at')


class Enfant(BaseModelForm):

    class Meta:
        model = Case
        exclude = ('created_at', 'updated_at', 'ref_id', \
                   'estimated_dob', 'guardian_id')
