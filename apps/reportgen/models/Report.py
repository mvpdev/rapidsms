#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.db.models.signals import pre_save
from django.db import models, IntegrityError
from django.utils.translation import ugettext as _

'''
Report primarily exists to point to the
file where the Report definition is stored.
Classname tells reportgen the name of the
file in the reportgen/definitions folder
where the report definition exists.

We put the report title here so that we can
easily sort the list of reports by title.

'''

class Report(models.Model):
    class Meta:
        app_label = 'reportgen'
        db_table = 'reportgen_report'
        verbose_name = _(u"Report")
        verbose_name_plural = _(u"Reports")
        ordering = ('title', )

    title = models.CharField(_(u"Title"), max_length=60, blank=False, \
                                null=False, db_index=True, unique=True, \
                                help_text=_(u"Human-readable title for report"))

    classname = models.CharField(_(u"Class name"), max_length=60, blank=False, \
                                null=False, db_index=True, unique=True, \
                                help_text=_(u"Name of module in which the report " \
                                            "is defined."))

    def __unicode__(self):
        return self.title

    def get_definition(self):
        m = __import__(\
                ''.join(['reportgen.definitions.', self.classname]),
                globals(), locals(), ['ReportDefinition'], -1)
        t = m.ReportDefinition()
        t.check_sanity()
        return m.ReportDefinition


    def get_filename(self, variant, rformat, key=None):
        if variant is None: variant = ''

        if key is None:     keystr = ''
        else:               keystr = "_%d" % key

        return ''.join([\
            self.get_definition().filename, \
            variant, \
            keystr, '.', rformat])

    @property
    def formats(self):
        return self.get_definition().formats

    @property
    def variants(self):
        var = self.get_definition().variants
        if len(var) > 0: return var
        else:
            var = [("--","", {})]

def validate_report(sender, **kwargs):
    report = kwargs['instance']
    try:
        report.get_definition()
    except ImportError:
        raise IntegrityError(_("Could not import report definition "\
                                "named \"%s\".") % report.classname)

# Tell Django to run the custom validation logic
# on the Report before saving it
pre_save.connect(validate_report, \
    dispatch_uid='validate_report',
    weak=False,
    sender=Report)

