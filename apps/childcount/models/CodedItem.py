#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin, rgaudin

from django.db import models
from django.utils.translation import ugettext_lazy as _


class CodedItem(models.Model):

    TYPE_DANGER_SIGN = 'DS'
    TYPE_FAMILY_PLANNING = 'FP'
    TYPE_MEDICINE = 'M'
    TYPE_COUNSELING = 'C'

    danger_sign = {
        'as': (_('as'), _(u"Accident / trauma")),
        'bd': (_('bd'), _(u"Difficulty breathing")),
        'bl': (_('bl'), _(u"Abnormal bleeding")),
        'bm': (_('bm'), _(u"Baby stopped moving")),
        'bs': (_('bs'), _(u"Blood in stool")),
        'bv': (_('bv'), _(u"Blurred vision")),
        'cc': (_('cc'), _(u"Cough")),
        'cl': (_('cl'), _(u"Cold to touch")),
        'cm': (_('cm'), _(u"Coma")),
        'cn': (_('cn'), _(u"No bowel movements")),
        'cv': (_('cv'), _(u"Convulsions")),
        'cw': (_('cw'), _(u"Cough > 3 weeks")),
        'dh': (_('dh'), _(u"Dehydration")),
        'fp': (_('fp'), _(u"Fever in first trimester")),
        'fv': (_('fv'), _(u"Fever")),
        'ir': (_('ir'), _(u"Irritable / inconsolable")),
        'nb': (_('nb'), _(u"Night blindness")),
        'nf': (_('nf'), _(u"Not feeding / sucking well")),
        'nr': (_('nr'), _(u"Not responding well")),
        'nu': (_('nu'), _(u"Little or no urine")),
        'od': (_('od'), _(u"Oedema")),
        'pa': (_('pa'), _(u"Abdominal / pelvic pain")),
        'ph': (_('ph'), _(u"Severe headache")),
        'pu': (_('pu'), _(u"Painful urination")),
        'sf': (_('sf'), _(u"Skin infection")),
        'sp': (_('sp'), _(u"Sores, itching, pus on body")),
        'sw': (_('sw'), _(u"Swelling of face or hands")),
        'uf': (_('uf'), _(u"Umbilicus infection")),
        'vb': (_('vb'), _(u"Abnormal vaginal bleeding")),
        'vd': (_('vd'), _(u"Abnormal vaginal discharge")),
        'vm': (_('vm'), _(u"Vomiting")),
        'vp': (_('vp'), _(u"Vaginal pain or sores")),
        'wl': (_('wl'), _(u"Weight loss")),
        'z': (_('z'), _(u"Other")),
    }

    family_planning = {
        'c': (_('c'), _(u"Condoms")),
        'i': (_('i'), _(u"Injectable")),
        'n': (_('n'), _(u"Norplant")),
        'p': (_('p'), _(u"Oral contraception")),
    }

    medecine = {
        'act': (_('act'), _(u"Anti-malarial")),
        'r': (_('r'), _(u"ORS")),
        'z': (_('z'), _(u"Zinc")),
    }

    counseling = {
        'bp': (_('bp'), _(u"Birth plan")),
        'ec': (_('ec'), _(u"Environmental cleanliness")),
        'fp': (_('fp'), _(u"Family planning")),
        'nut': (_('nut'), _(u"Nutrition")),
        'ed': (_('ed'), _(u"General education")),
        'ph': (_('ph'), _(u"Public health")),
        'im': (_('im'), _(u"Immunisations")),
    }

    ci_matrix = {
        TYPE_DANGER_SIGN: danger_sign,
        TYPE_FAMILY_PLANNING: family_planning,
        TYPE_MEDICINE: medecine,
        TYPE_COUNSELING: counseling,
    }

    class Meta:
        app_label = 'childcount'
        db_table = 'cc_codeditem'
        verbose_name = _(u"Coded Item")
        verbose_name_plural = _(u"Coded Items")
        ordering = ('type', 'code')
        unique_together = ('type', 'code')

    TYPE_CHOICES = (
        (TYPE_DANGER_SIGN, _(u"Danger sign")),
        (TYPE_FAMILY_PLANNING, _(u"Family planning")),
        (TYPE_MEDICINE, _(u"Medicine")),
        (TYPE_COUNSELING, _(u"Counseling topic")))

    code = models.CharField(_(u"Code"), max_length=10)
    type = models.CharField(_(u"Type"), choices=TYPE_CHOICES, max_length=2)

    @property
    def description(self):
        return self.ci_matrix[self.type][self.code][1].format()

    @property
    def local_code(self):
        return self.ci_matrix[self.type][self.code][0].format()

    def __unicode__(self):
        return u"%s: %s" % (self.local_code, self.description)

    @classmethod
    def by_local_code(cls, type_, local_code):
        for key, value in cls.ci_matrix[type_].iteritems():
            if local_code == value[0]:
                return CodedItem.objects.get(code=key)
        raise KeyError(u"No matching Coded Item.")
