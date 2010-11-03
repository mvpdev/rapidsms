#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.db import models
from django.db.models.signals import pre_save
from django.core.files.storage import default_storage
from xml.dom.minidom import parseString, Element

ODK_FORMS = "odk-forms/"

class Form(models.Model):
    name = models.CharField(max_length=30)
    id_string = models.CharField(max_length=50, unique=True, blank=True)
    xml = models.TextField()
    active = models.BooleanField()

    class Meta:
        unique_together = (("name", "active"),)

    def url(self):
        """Return 'odk-forms/formname.xml'."""
        return ODK_FORMS + self.name + ".xml"

    def __unicode__(self):
        return self.id_string

    def _set_id_from_xml(self):
        """Find the single child of h:head/model/instance and return
        the attribute 'id'."""
        dom = parseString(self.xml)
        element = dom.documentElement
        path = ["h:head", "model", "instance"]
        count = {}
        for name in path:
            count[name] = 0
            for child in element.childNodes:
                if isinstance(child, Element) and child.tagName==name:
                    count[name] += 1
                    element = child
            assert count[name]==1
        count["id"] = 0
        for child in element.childNodes:
            if isinstance(child, Element):
                count["id"] += 1
                element = child
        assert count["id"]==1
        self.id_string = element.getAttribute("id")

def _set_form_id(sender, **kwargs):
    kwargs["instance"]._set_id_from_xml()

# before a form is saved to the database set the form's id string by
# looking through it's xml.
pre_save.connect(_set_form_id, sender=Form)

    
ODK_IMAGES = "odk-images/"
ODK_DATE_FORMAT = "%Y-%m-%d_%H-%M-%S"

class Submission(models.Model):
    xml = models.TextField()
    saved = models.DateTimeField()
    posted = models.DateTimeField(auto_now_add=True)
    form = models.ForeignKey(Form, null=True, related_name="submissions")

    def __unicode__(self):
        return self.form.id_string

    def _link(self):
        dom = parseString(self.xml)
        element = dom.documentElement
        id_string = element.getAttribute("id")
        self.form = Form.objects.get(id_string=id_string)

def _link_submission(sender, **kwargs):
    kwargs["instance"]._link()

pre_save.connect(_link_submission, sender=Submission)

    
# http://docs.djangoproject.com/en/dev/ref/models/fields/#django.db.models.FileField.upload_to
def _upload_to(instance, filename):
    return "/".join([ODK_IMAGES + instance.submission.form.name,
                     instance.submission.saved.strftime(ODK_DATE_FORMAT),
                     filename])

class SubmissionImage(models.Model):
    submission = models.ForeignKey(Submission, related_name="images")
    image = models.FileField(upload_to=_upload_to, storage=default_storage)
