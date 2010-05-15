#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

'''ChildCount Models

Case - Patient/Child model

CaseNote - case notes model
'''

import re

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User, Group

from rapidsms.message import Message
from reporters.models import Reporter, Role
from locations.models import Location

from childcount.models import CHW
from childcount.models import Patient
from childcount.models import Encounter
from childcount.models import CodedItem
from childcount.models.reports import NutritionReport
from childcount.models.reports import FeverReport
from childcount.models.reports import DangerSignsReport
from childcount.utils import clean_names
from childcount.forms import PatientRegistrationForm
from childcount.exceptions import BadValue, ParseError


class Case(models.Model):

    '''Holds the patient details, properties and methods related to it'''

    class Meta:
        app_label = 'migration'

    STATUS_ACTIVE = 1
    STATUS_INACTIVE = 0
    STATUS_DEAD = -1

    STATUS_CHOICES = (
        (STATUS_ACTIVE, 'Alive'),
        (STATUS_INACTIVE, 'Relocated'),
        (STATUS_DEAD, 'Dead'))

    GENDER_CHOICES = (
        ('M', _('Male')),
        ('F', _('Female')))

    ref_id = models.IntegerField(_('Case ID #'), null=True, db_index=True)
    first_name = models.CharField(max_length=255, db_index=True)
    last_name = models.CharField(max_length=255, db_index=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, \
                              null=True, blank=True)
    dob = models.DateField(_('Date of Birth'), null=True, blank=True)
    estimated_dob = models.NullBooleanField(null=True, blank=True)
    guardian = models.CharField(max_length=255, null=True, blank=True)
    guardian_id = models.CharField(max_length=255, null=True, blank=True)
    mobile = models.CharField(max_length=16, null=True, blank=True)
    reporter = models.ForeignKey(Reporter, db_index=True)
    location = models.ForeignKey(Location, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.IntegerField(choices=STATUS_CHOICES, \
                                      default=STATUS_ACTIVE)

    def __unicode__(self):
        return "#%d" % self.ref_id


class Observation(models.Model):

    '''Stores observations in a key/values format

    name - the full name/description of the observation
    letter - the short code alphabet of the observation
    '''

    uid = models.CharField(max_length=15)
    name = models.CharField(max_length=255)
    letter = models.CharField(max_length=2, unique=True)

    class Meta:
        app_label = 'migration'
        ordering = ('name',)

    def __unicode__(self):
        return self.name


class ReportMalaria(models.Model):

    '''records reported malaria rdt tests'''

    class Meta:
        get_latest_by = 'entered_at'
        ordering = ('-entered_at',)
        app_label = 'migration'
        verbose_name = 'Malaria Report'
        verbose_name_plural = 'Malaria Reports'

    case = models.ForeignKey(Case, db_index=True)
    reporter = models.ForeignKey(Reporter, db_index=True)
    entered_at = models.DateTimeField(db_index=True)
    bednet = models.BooleanField(db_index=True)
    result = models.BooleanField(db_index=True)
    observed = models.ManyToManyField(Observation, blank=True)


class ReportMalnutrition(models.Model):

    '''record malnutrition measurements'''

    MODERATE_STATUS = 1
    SEVERE_STATUS = 2
    SEVERE_COMP_STATUS = 3
    HEALTHY_STATUS = 4

    STATUS_CHOICES = (
        (MODERATE_STATUS, _('MAM')),
        (SEVERE_STATUS, _('SAM')),
        (SEVERE_COMP_STATUS, _('SAM+')),
        (HEALTHY_STATUS, _("Healthy")))

    case = models.ForeignKey(Case, db_index=True)
    reporter = models.ForeignKey(Reporter, db_index=True)
    entered_at = models.DateTimeField(db_index=True)
    muac = models.IntegerField(_("MUAC (mm)"), null=True, blank=True)
    height = models.IntegerField(_("Height (cm)"), null=True, blank=True)
    weight = models.FloatField(_("Weight (kg)"), null=True, blank=True)
    observed = models.ManyToManyField(Observation, blank=True)
    status = models.IntegerField(choices=STATUS_CHOICES, \
                            db_index=True, blank=True, null=True)

    class Meta:
        app_label = 'migration'
        verbose_name = "Malnutrition Report"
        verbose_name_plural = "Malnutrition Reports"
        get_latest_by = 'entered_at'
        ordering = ('-entered_at',)

    def __unicode__(self):
        return u'%s: %s: %s' % (self.id, self.case, self.muac)


class MigrationLog(models.Model):
    class Meta:
        app_label = 'migration'

    message = models.CharField(max_length=255, db_index=True)
    case = models.ForeignKey(Case, db_index=True)
    success = models.BooleanField(default=False)
    type = models.CharField(max_length=255, db_index=True)


def migrate_chw(reporter, autoalias=True):
    '''Give reporter object the CHW object property'''
    reporter_language = 'en'
    location = reporter.location
    if CHW.objects.filter(reporter_ptr=reporter).count():
        return CHW.objects.get(reporter_ptr=reporter)
    chw = CHW(reporter_ptr=reporter)
    chw.save_base(raw=True)
    flat_name = reporter.last_name + ' ' + reporter.first_name
    surname, firstnames, alias = clean_names(flat_name, surname_first=True)
    orig_alias = alias[:20]
    alias = orig_alias.lower()

    if alias != chw.alias and not re.match(r'%s\d' % alias, chw.alias):
        n = 1
        while User.objects.filter(username__iexact=alias).count():
            alias = "%s%d" % (orig_alias.lower(), n)
            n += 1
        n = 1
        while Reporter.objects.filter(alias__iexact=alias).count():
            alias = "%s%d" % (orig_alias.lower(), n)
            n += 1
        if not autoalias:
            chw.alias = reporter.alias
        else:
            chw.alias = alias

    chw.first_name = firstnames
    chw.last_name = surname
    chw.language = reporter_language

    chw.location = location

    chw.save()
    try:
        chw_group = Group.objects.get(name__iexact='CHW')
    except Group.DoesNotExist:
        #TODO what if there is no chw group?
        pass
    else:
        try:
            chw.groups.add(chw_group)
        except:
            pass
    return chw


def migrate_chws():
    chwrole = Role.objects.get(code='chw')
    reporters = Reporter.objects.filter(role=chwrole)
    chws = []
    for reporter in reporters:
        chw = migrate_chw(reporter)
        chws.append(chw)
    return chws


def migrate_patients():
    default_parent()
    cases = Case.objects.all()
    print cases.count()

    for case in cases:
        response = migrate_case(case)
        print response


def migrate_case(case):
    '''migrate a case to a patient

    case - is a Case object
    '''
    print case
    reporter = case.reporter
    message = Message(reporter.connection())
    message.reporter = reporter
    try:
        chw = CHW.objects.get(reporter_ptr=reporter)
    except CHW.DoesNotExist:
        chw = migrate_chw(reporter)
    params = ['new']
    params.append(case.location.code)
    params.append(case.first_name)
    params.append(case.last_name)
    params.append(case.gender.lower())
    params.append(case.dob.strftime("%d%m%Y"))
    params.append("XXXXX")
    params.append("XXXXX")

    form = PatientRegistrationForm(message, case.created_at, chw, params, \
                                    u'%s' % case.ref_id)
    form.pre_process()
    response = form.response
    success = response.startswith('You successfuly registered')
    ml = MigrationLog(message=response, case=case, success=success, \
                        type='reg')
    ml.save()
    return response


def default_parent():
    '''create the default parent that will be used by all cases initially'''
    reporter = Reporter.objects.get(alias__iexact=u'help')
    message = Message(reporter.connection())
    message.reporter = reporter
    try:
        chw = CHW.objects.get(reporter_ptr=reporter)
    except CHW.DoesNotExist:
        chw = migrate_chw(reporter, autoalias=False)
    params = ['new']
    params.append(reporter.location.code)
    params.append(u'Default')
    params.append(u'Parent')
    params.append(u'F'.lower())
    params.append(u'20011978')
    params.append(u'p')

    frm = PatientRegistrationForm(message, datetime.now(), chw, params, 'XXXXX')
    try:
        frm.pre_process()
    except ParseError, e:
        print e.message
        exit()
    except BadValue, e:
        print e.message
        exit()

    print frm.response


def get_encounter(encounter_date, type, chw, patient):
    '''create and return an encounter object'''
    enc = Encounter(encounter_date=encounter_date, type=type, chw=chw, \
                    patient=patient)
    enc.save()
    return enc


def migrate_muacs():
    for muac in ReportMalnutrition.objects.all():
        if muac.muac > 2000:
            continue
        print migrate_muac(muac)


def migrate_muac(muac):
    '''migrate nutrition reports
    muac - a ReportMalnutrition report
    '''
    print muac
    try:
        chw = CHW.objects.get(reporter_ptr=muac.reporter)
    except CHW.DoesNotExist:
        chw = migrate_chw(reporter, autoalias=False)
    patient = Patient.objects.get(health_id=muac.case.ref_id)
    oedema = NutritionReport.OEDEMA_NO
    if 'e' in muac.observed.values():
        oedema = NutritionReport.OEDEMA_YES
    encounter = get_encounter(muac.entered_at, Encounter.TYPE_PATIENT, chw, \
                                patient)
    if muac.muac > 500:
        muac.muac = muac.muac/10
    nr = NutritionReport(encounter=encounter, oedema=oedema, muac=muac.muac)
    nr.save()

    '''migrate observations'''
    danger_signs = dict([(danger_sign.code.lower(), danger_sign) \
                             for danger_sign in \
                             CodedItem.objects.filter(\
                                type=CodedItem.TYPE_DANGER_SIGN)])
    valid = []
    unknown = []
    for complication in muac.observed.all():
        code = complication.letter
        if complication.letter.lower() == 'uf':
            #Not feedeng
            code = u'nf'
        if complication.letter.lower() == 'cg':
            #Cough
            code = u'cc'
        if complication.letter.lower() == 'f':
            #Fever
            code = u'fv'
        if complication.letter.lower() == 'v':
            #vomiting
            code = u'vm'
        if complication.letter.lower() == 'e':
            #Oedema
            code = u'od'
        if complication.letter.lower() == 'b':
            #Difficulty breathing
            code = u'bd'
        if complication.letter.lower() == 'a':
            #Not feeding
            code = u'nf'
        obj = danger_signs.get(code, None)
        if obj is not None:
            valid.append(obj)
        else:
            unknown.append(code)
    if unknown:
        print "Unknown Danger Signs: %s" % ','.join(unknown).upper()
    else:
        dsr = DangerSignsReport(encounter=encounter)
        dsr.save()
        for obj in valid:
            dsr.danger_signs.add(obj)
        dsr.save()

    return nr


def migrate_mrdts():
    for mrdt in ReportMalaria.objects.all():
        print migrate_mrdt(mrdt)


def migrate_mrdt(mrdt):
    '''Migrate malaria reports
    mrdt - a ReportMalaria object
    '''
    print mrdt
    try:
        chw = CHW.objects.get(reporter_ptr=mrdt.reporter)
    except CHW.DoesNotExist:
        chw = migrate_chw(reporter, autoalias=False)
    patient = Patient.objects.get(health_id=mrdt.case.ref_id)

    encounter = get_encounter(mrdt.entered_at, Encounter.TYPE_PATIENT, chw, \
                                patient)
    rdt_result = FeverReport.RDT_NEGATIVE
    if mrdt.result:
        rdt_result = FeverReport.RDT_POSITIVE
    fr = FeverReport(encounter=encounter, rdt_result=rdt_result)
    fr.save()
    
    '''migrate observations'''
    danger_signs = dict([(danger_sign.code.lower(), danger_sign) \
                             for danger_sign in \
                             CodedItem.objects.filter(\
                                type=CodedItem.TYPE_DANGER_SIGN)])
    valid = []
    unknown = []
    for complication in mrdt.observed.all():
        code = complication.letter
        if complication.letter.lower() == 'uf':
            #Not feedeng
            code = u'nf'
        if complication.letter.lower() == 'cg':
            #Cough
            code = u'cc'
        if complication.letter.lower() == 'f':
            #Fever
            code = u'fv'
        if complication.letter.lower() == 'v':
            #vomiting
            code = u'vm'
        if complication.letter.lower() == 'e':
            #Oedema
            code = u'od'
        if complication.letter.lower() == 'b':
            #Difficulty breathing
            code = u'bd'
        if complication.letter.lower() == 'a':
            #Not feeding
            code = u'nf'
        obj = danger_signs.get(code, None)
        if obj is not None:
            valid.append(obj)
        else:
            unknown.append(code)
    if unknown:
        print "Unknown Danger Signs: %s" % ','.join(unknown).upper()
    else:
        dsr = DangerSignsReport(encounter=encounter)
        dsr.save()
        for obj in valid:
            dsr.danger_signs.add(obj)
        dsr.save()

    return fr


def reveal_case(case, what):
    print u'%s: %s %s %s %s' % (what, case.ref_id, case.first_name, \
                                case.last_name, case.reporter)


def dupes():
    '''Check for duplacate cases'''
    cases = Case.objects.all()
    dupes = []
    for case in cases:
        #those with same ref_id
        d = Case.objects.filter(ref_id__iexact=case.ref_id)
        if d.count() > 1:
            if case not in dupes:
                dupes.extend(d)
                reveal_case(case, 'REF')
        #those with same name, dob, CHW
        d = Case.objects.filter(first_name__iexact=case.first_name, \
                                last_name__exact=case.last_name, \
                                dob__exact=case.dob, \
                                reporter=case.reporter)
        if d.count() > 1:
            if case not in dupes:
                dupes.extend(d)
                reveal_case(case, 'NAME')
        #those with same name, dob
        d = Case.objects.filter(first_name__iexact=case.first_name, \
                                last_name__exact=case.last_name, \
                                dob__exact=case.dob)
        if d.count() > 1:
            if case not in dupes:
                dupes.extend(d)
                reveal_case(case, 'NAME NO Reporter')
    return dupes