#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin


from django import forms
from django_tracking.models import State, TrackedItem
from findtb.models import SpecimenMustBeReplaced, AllTestsDone,\
                          MicroscopyResult, LpaResult, MgitResult,\
                          SpecimenInvalid, LjResult, SirezResult
from findtb.libs.utils import send_to_dtu, dtls_is_lab_tech_at, send_to_dtls
from sref_transit_forms import SrefForm

"""
Forms setting states for a testing results
"""


class MicroscopyForm(SrefForm):
    """
    Form shown when the specimen needs a microcopy.
    """

    result = forms.ChoiceField(choices=MicroscopyResult.RESULT_CHOICES)


    def save(self, *args, **kwargs):

        ti, created = TrackedItem.get_tracker_or_create(content_object=self.specimen)

        result = MicroscopyResult(result=self.cleaned_data['result'],
                                  specimen=self.specimen)

        ti.state = result
        ti.save()

        msg_start = u"Specimen %(id)s (%(tc)s)" % \
              {'id': self.specimen.patient.zero_id(),
               'tc': self.specimen.tc_number}

        msg_end = u"Microscopy smear results: "

        if result.is_positive():
            msg_end += u"POSITIVE (%(result)s). Expect LPA results within 7 " \
                   u"days." % {'result': result.result.upper()}
        else:
            msg_end += u"%(result)s. Expect MGIT culture results within 6" \
                       u" weeks." % \
                       {'result': result.result.upper()}

        send_to_dtu(self.specimen.location, u"%s %s" % (msg_start, msg_end))

        if not dtls_is_lab_tech_at(self.specimen.location):
            send_to_dtls(self.specimen.location, u"%s from %s %s" % \
                              (msg_start, self.specimen.location, msg_end))


class LpaForm(SrefForm):
    """
    Form shown when the specimen needs a LPA.
    """

    RIF_CHOICES = (
        ('resistant', u"RIF Resistant") ,
        ('Susceptible', u"RIF Susceptible"),
        ('invalid', u"Invalid"),
    )

    INH_CHOICES = (
        ('resistant', u"INH Resistant") ,
        ('Susceptible', u"INH Susceptible"),
        ('invalid', u"Invalid"),
    )

    rif = forms.ChoiceField(choices=RIF_CHOICES)
    inh = forms.ChoiceField(choices=INH_CHOICES)


    def save(self, *args, **kwargs):

        ti, created = TrackedItem.get_tracker_or_create(content_object=self.specimen)

        result = LpaResult(rif=self.cleaned_data['rif'],
                           inh=self.cleaned_data['inh'],
                           specimen=self.specimen)
        ti.state = result
        ti.save()

        msg = u"LPA results for specimen of %(patient)s with "\
              u"tracking tag %(tag)s: INH %(inh)s and RIF %(rif)s." % {
               'patient': self.specimen.patient,
               'tag': self.specimen.tracking_tag,
               'inh': self.cleaned_data['inh'].upper(),
               'rif': self.cleaned_data['rif'].upper()}

        if self.cleaned_data['rif'] == 'Susceptible':
            msg = "Start category 1 treatment - %s" % msg
            result = AllTestsDone(specimen=self.specimen)
            ti.state = result
            ti.save()
        else:
            msg = "Start category 2 treatment - %s" % msg

        send_to_dtu(self.specimen.location, msg)



class MgitForm(SrefForm):
    """
    Form shown when the specimen needs a MGIT.
    """

    RESULT_CHOICES = (
        ('positive', u"Positive"),
        ('negative', u"Negative"),
        ('invalid', u"Invalid"),
    )

    result = forms.ChoiceField(choices=RESULT_CHOICES)


    def save(self, *args, **kwargs):

        ti, created = TrackedItem.get_tracker_or_create(content_object=self.specimen)

        result = MgitResult(result=self.cleaned_data['result'],
                            specimen=self.specimen)
        ti.state = result
        ti.save()

        if self.cleaned_data['result'] == 'negative':
            result = SpecimenMustBeReplaced(specimen=self.specimen)
            ti.state = State(content_object=result, is_final=True)
            ti.save()

        msg = u"MGIT results for specimen of %(patient)s with "\
              u"tracking tag %(tag)s: %s(result)s." % {
               'patient': self.specimen.patient,
               'tag': self.specimen.tracking_tag,
               'result': self.cleaned_data['result'].upper()}


        send_to_dtu(self.specimen.location, msg)



class LjForm(SrefForm):
    """
    Form shown when the specimen needs a LJ.
    """

    RESULT_CHOICES = (
        ('positive', u"Positive"),
        ('negative', u"Negative"),
        ('invalid', u"Invalid"),
    )

    result = forms.ChoiceField(choices=RESULT_CHOICES)


    def save(self, *args, **kwargs):

        ti, created = TrackedItem.get_tracker_or_create(content_object=self.specimen)

        result = LjResult(result=self.cleaned_data['result'],
                                 specimen=self.specimen)
        ti.state = result
        ti.save()

        if self.cleaned_data['result'] != "positive":

            msg = u"LJ results for specimen of %(patient)s with "\
                  u"tracking tag %(tag)s: %(result)s. Please send a new specimen." % {
                    'patient': self.specimen.patient,
                    'tag': self.specimen.tracking_tag,
                    'result': self.cleaned_data['result'].upper()}

            result = SpecimenMustBeReplaced(specimen=self.specimen)
            ti.state = State(content_object=result, is_final=True)
            ti.save()

        else:
            msg = u"LJ results for specimen of %(patient)s with "\
                   u"tracking tag %(tag)s: %(result)s." % {
                     'patient': self.specimen.patient,
                     'tag': self.specimen.tracking_tag,
                     'result': self.cleaned_data['result'].upper()}

        send_to_dtu(self.specimen.location, msg)


class SirezForm(SrefForm):
    """
    Form shown when the specimen needs to be tested against SIREZ.
    """

    RIF_CHOICES = (
        ('resistant', u"RIF Resistant") ,
        ('Susceptible', u"RIF Susceptible"),
        ('invalid', u"Invalid"),
    )

    INH_CHOICES = (
        ('resistant', u"INH Resistant") ,
        ('Susceptible', u"INH Susceptible"),
        ('invalid', u"Invalid"),
    )

    STR_CHOICES = (
        ('resistant', u"STR Resistant") ,
        ('Susceptible', u"STR Susceptible"),
        ('invalid', u"Invalid"),
    )

    EMB_CHOICES = (
        ('resistant', u"EMB Resistant") ,
        ('Susceptible', u"EMB Susceptible"),
        ('invalid', u"Invalid"),
    )

    PZA_CHOICES = (
        ('resistant', u"PZA Resistant") ,
        ('Susceptible', u"PZA Susceptible"),
        ('invalid', u"Invalid"),
    )

    rif = forms.ChoiceField(choices=RIF_CHOICES)
    inh = forms.ChoiceField(choices=INH_CHOICES)
    str = forms.ChoiceField(choices=STR_CHOICES)
    emb = forms.ChoiceField(choices=EMB_CHOICES)
    pza = forms.ChoiceField(choices=PZA_CHOICES)


    def save(self, *args, **kwargs):

        ti, created = TrackedItem.get_tracker_or_create(content_object=self.specimen)

        result = SirezResult(rif=self.cleaned_data['rif'],
                             inh=self.cleaned_data['inh'],
                             str=self.cleaned_data['str'],
                             emb=self.cleaned_data['emb'],
                             pza=self.cleaned_data['pza'],
                                 specimen=self.specimen)
        ti.state = result
        ti.save()

        # if one test is invalid, request a new specimen, but do not
        # mark the test as invalid
        # count the number of resitances, the SMS response if different
        # according to the level of resistance
        resistances = []
        sent = False
        for test in ('rif', 'inh', 'str', 'emb', 'pza'):

            res = self.cleaned_data[test]

            if res == 'invalid' and not sent:

                msg = u"SIREZ results for specimen of %(patient)s with "\
                      u"tracking tag %(tag)s is invalid for %(test)s. "\
                      u"Please send a new specimen." % {
                        'patient': self.specimen.patient,
                        'tag': self.specimen.tracking_tag,
                        'test': test.upper()}

                send_to_dtu(self.specimen.location, msg)
                sent = True

                result = SpecimenMustBeReplaced(specimen=self.specimen)
                ti.state = State(content_object=result, is_final=True)
                ti.save()

            if res == 'resistant':
                resistances.append(test.upper())

        msg = u"SIREZ shows resistances for: %s. " % ", ".join(resistances)

        # check the difference with lpa
        lpa = ti.get_history().get(title='lpa').content_object
        diff = []

        if lpa.rif != self.cleaned_data['rif']:
            diff.append(u"RIF: %s" % lpa.rif.upper())

        if lpa.inh != self.cleaned_data['inh']:
            diff.append(u"INH: %s" % lpa.inh.upper())

        if diff:
            msg += u"LPA had different results: %s. " % " ".join(diff)

        if len(resistances) >= 2 or self.cleaned_data['rif'] == 'resistant':
            msg = u"Carry on with category 2 treatment and seek guidance "\
                  u"from ZTLS. %s" % msg
        else:
            msg = u"Carry on with category 1 treatment and seek guidance "\
                  u"from ZTLS. %s" % msg

        send_to_dtu(self.specimen.location, msg)

        result = AllTestsDone(specimen=self.specimen)
        ti.state = result
        ti.save()



class SireForm(SrefForm):
    """
    Form shown when the specimen needs to be tested against SIRE(Z).
    """

    PZA_CHOICES = (
        ('untested', u"PZA Untested"),
        ('resistant', u"PZA Resistant") ,
        ('Susceptible', u"PZA Susceptible"),
        ('invalid', u"Invalid"),
    )

    pza = forms.ChoiceField(choices=PZA_CHOICES)


