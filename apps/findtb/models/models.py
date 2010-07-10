#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

import re
import datetime

from django.db import models, IntegrityError
from django.utils.translation import ugettext as _
from django.contrib.auth.models import Group, User
from django.db.models.signals import post_delete, pre_save
from django.contrib.contenttypes import generic

from django_tracking.models import TrackedItem, State

from locations.models import Location
from reporters.models import Reporter

# TODO : break this file in several smaller files

class SlidesBatchManager(models.Manager):


    def get_for_quarter(self, dtu, quarter=None, year=None):
        """
        Get the slides batch from a DTU for the EQA of the corresponding quarter
        of the given year or the current quarter and year if none is provided.
        """

        if bool(quarter) != bool(year):
            raise ValueError("You must define 'quarter' AND 'year' or none of them")

        if not quarter:
            quarter, year = SlidesBatch.get_quarter(datetime.date.today())

        begin, end = SlidesBatch.QUARTER_BOUNDARIES[quarter]
        begin = datetime.date(year, begin[1], begin[0])
        end = datetime.date(year, end[1], end[0])

        return self.filter(location=dtu, created_on__gte=begin, created_on__lte=end).get()


    def get_for_quarter_including_date(self, dtu, date=None):
        """
        Get the slides batch from a DTU for the EQA of the corresponding quarter
        of the given year that includes this date or the current date if
        none is provided.
        """

        date = date or datetime.date.today()
        return self.get_for_quarter(dtu, *SlidesBatch.get_quarter(date))



class Role(models.Model):
    """
    Link between a Django group, a location and a reporter
    """

    class Meta:
        app_label = 'findtb'

    group = models.ForeignKey(Group)
    reporter = models.ForeignKey(Reporter)
    location = models.ForeignKey(Location, blank=True, null=True)


    def __unicode__(self):
        return "%(reporter)s as %(group)s at %(location)s" % \
               {'reporter':self.reporter, 'group':self.group,
                'location':self.location}


    @classmethod
    def getSpecimenRelatedRoles(cls, specimen):
        """
            Return roles for a given specimen according to its location
        """

        roles = list(Role.objects.filter(location=specimen.location))
        try:
            roles.extend(Role.objects.filter(location=specimen.location.parent))
            roles.extend(Role.objects.filter(location=specimen.location.parent.parent))
        except AttributeError:
            pass

        return roles


    @classmethod
    def getSpecimenRelatedContacts(cls, specimen):
        """
            Return contacts for a given specimen according to its location
        """

        roles = cls.getSpecimenRelatedRoles(specimen)

        roles_dict = {}
        for role in roles:
            roles_dict.setdefault(role.group.name, []).append(role.reporter)

        return roles_dict


    @classmethod
    def getSlidesBatchRelatedRoles(cls, slides_batch):
        """
            Return roles for a given slides batch according to its location
        """

        roles = list(Role.objects.filter(location=slides_batch.location))
        try:
            roles.extend(Role.objects.filter(location=slides_batch.location.parent))
            roles.extend(Role.objects.filter(location=slides_batch.location.parent.parent))
        except AttributeError:
            pass

        return roles


    @classmethod
    def getSlidesBatchRelatedContacts(cls, slides_batch):
        """
            Return contacts for a given slides batch according to its location
        """

        roles = cls.getSlidesBatchRelatedRoles(slides_batch)

        roles_dict = {}
        for role in roles:
            roles_dict.setdefault(role.group.name, []).append(role.reporter)

        return roles_dict



def Role_delete_handler(sender, **kwargs):
    '''
    Called when a Role is deleted. It checks to see if that was that reporter's
    only Role in that group and, if so, removes the User from that Group
    '''
    class Meta:
        app_label = 'findtb'
    role = kwargs['instance']
    if not Role.objects.filter(reporter=role.reporter,
                               group=role.group).count():
        role.reporter.groups.remove(role.group)

post_delete.connect(Role_delete_handler, sender=Role)



def Role_presave_handler(sender, **kwargs):
    '''
    Called when a Role is saved. It adds the Role's reporter (User) to the
    same group. It also removes the User from the group if they don't have
    any more Roles in that group.
    '''
    class Meta:
        app_label = 'findtb'
    role = kwargs['instance']
    role.reporter.groups.add(role.group)
    if role.pk:
        orig_role = Role.objects.get(pk=role.pk)
        if orig_role.reporter != role.reporter:
            if Role.objects.filter(reporter=orig_role.reporter,
                                   group=orig_role.group).count() == 1:
                orig_role.reporter.groups.remove(orig_role.group)
        else:
            if orig_role.group != role.group:
                if Role.objects.filter(reporter=role.reporter,
                                       group=orig_role.group).count() == 1:
                    role.reporter.groups.remove(orig_role.group)

pre_save.connect(Role_presave_handler, sender=Role)



class Patient(models.Model):

    class Meta:
        app_label = 'findtb'
        unique_together = ("registration_number", "location")


    GENDER_MALE = 'M'
    GENDER_FEMALE = 'F'

    GENDER_CHOICES = (
        (GENDER_MALE, _(u"Male")),
        (GENDER_FEMALE, _(u"Female")))

    first_name = models.CharField(max_length=50, blank=True, default="")
    last_name = models.CharField(max_length=50, blank=True, default="")

    gender = models.CharField(_(u"Gender"), max_length=1,
                              choices=GENDER_CHOICES,
                              blank=True, null=True)

    created_on = models.DateTimeField(_(u"Created on"), auto_now_add=True)
    created_by = models.ForeignKey(Reporter)

    location = models.ForeignKey(Location)
    registration_number = models.CharField(max_length=25, db_index=True)
    dob = models.DateField(_(u"Date of birth"), blank=True, null=True)

    estimated_dob = models.NullBooleanField(_(u"Estimated date of birth"),
                                            default=True,
                                            help_text=_(u"True or false: the "\
                                                     "date of birth is only "\
                                                     "an approximation"))
    is_active = models.BooleanField(default=True)

    def zero_id(self):
        """
            Returns a zero-padded registration_number as a string
        """
        match = re.match('^(\d+)/(\d+)$',self.registration_number)

        if not re.match('^(\d+)/(\d+)$',self.registration_number):
            return self.registration_number

        return "%04d/%s" % (int(match.groups()[0]), match.groups()[1])


    def full_name(self):
        """
        Return last_name and/or first_name, or an empty string.
        """
        name = '%s %s' % (self.last_name, self.first_name)
        if name != " ":
            return name
        return ''


    def __unicode__(self):

        name = self.full_name()
        if name:
            return name

        return self.zero_id()


    def get_estimated_age(self):
        """
            Return age calculated from date or birth
        """
        return datetime.date.today().year - self.dob.year



class Specimen(models.Model):

    class Meta:
        app_label = 'findtb'
        permissions = (("send_specimen", "Can send specimen"),
                       ("receive_specimen", "Can send receive"))


    patient = models.ForeignKey(Patient)
    location = models.ForeignKey(Location)
    created_on = models.DateTimeField(_(u"Created on"), auto_now_add=True)
    created_by = models.ForeignKey(Reporter)
    tracking_tag = models.CharField(max_length=8, unique=True, db_index=True)
    tc_number = models.CharField(max_length=12, blank=True, null=True,
                                      db_index=True, unique=True)

    def __unicode__(self):

        if self.tc_number:
            return "Specimen of patient %(patient)s, TC#%(tc)s from %(dtu)s" % \
                             {'patient':self.patient, 'tc':self.tc_number,
                              'dtu': self.location}

        return "Specimen of patient %(patient)s, tracking tag %(tag)s from %(dtu)s" % \
                 {'patient':self.patient, 'tag':self.tracking_tag,
                  'dtu': self.location}


    def get_lab_techs(self):
        """
        Returns a query set of reporters that have the role lab tech at the
        DTU where the sample was registered.
        """
        return self.location.role_set \
                       .filter(group__name=FINDTBGroup.DTU_LAB_TECH_GROUP_NAME)

    def get_clinician(self):
        """
        Returns one reporter object that has the role clinician at the
        DTU where the sample was registered.  Returns None if there is not
        one.
        """
        try:
            return self.location.role_set \
                       .filter(group__name=FINDTBGroup.CLINICIAN_GROUP_NAME)[0]
        except IndexError:
            return None


    def get_dtls(self):
        return self.location.get_dtls()


    def get_ztls(self):
        return self.location.get_ztls()


    def should_shortcut_test_flow(self):
        """
            Test if the previous state was LPA with invalid result then
            a LJ with an invalid result.
        """
        try:
            prev_spec = self.patient.specimen_set.all().order_by('-created_on')[1]
        except IndexError, e:
            pass
        else:
            ti, c = TrackedItem.get_tracker_or_create(content_object=prev_spec)
            try:
                history = ti.get_history()
                lj = history.get(title="lj").content_object.result
                if lj != 'positive':
                    try:
                        lpa = history.get(title="lpa").content_object.rif
                        return lpa == 'invalid'
                    except State.DoesNotExist, e:
                        try:
                            mgit = history.get(title="mgit").content_object.result
                            return mgit != 'positive'
                        except State.DoesNotExist, e:
                            pass

            except State.DoesNotExist, e:
                pass

        return False
        
        
    @models.permalink
    def get_absolute_url(self):
        return ('findtb-sref-tracking', (),  {'id':self.id})
        


class FINDTBGroup(Group):

    class Meta:
        app_label = 'findtb'
        proxy = True


    CLINICIAN_GROUP_NAME = 'clinician'
    DTU_LAB_TECH_GROUP_NAME = 'dtu lab tech'
    DISTRICT_TB_SUPERVISOR_GROUP_NAME = 'district tb supervisor'
    ZONAL_TB_SUPERVISOR_GROUP_NAME = 'zonal tb supervisor'
    DTU_FOCAL_PERSON_GROUP_NAME = 'dtu focal person'
    FIRST_CONTROL_FOCAL_PERSON_GROUP_NAME = 'first control focal person'
    SECOND_CONTROL_FOCAL_PERSON_GROUP_NAME = 'second control focal person'


    def isClinician(self):
        return self.name == self.CLINICIAN_GROUP_NAME


    def isLabTech(self):
        return self.name == self.DTU_LAB_TECH


    def isDTLS(self):
        return self.name == self.DISTRICT_TB_SUPERVISOR


    def isZTLS(self):
        return self.name == self.ZONAL_TB_SUPERVISOR


    def isDtuFocalPerson(self):
        return self.name == self.DTU_FOCAL_PERSON_GROUP_NAME



class FINDTBLocation(Location):

    class Meta:
        app_label = 'findtb'
        proxy = True


    def get_zone(self):
        for location in self.ancestors(include_self=True):
            if location.type.name == 'zone':
                return location


    def get_district(self):
        for location in self.ancestors(include_self=True):
            if location.type.name == 'district':
                return location


    def get_dtls(self):

        district = self.get_district()
        dtls_group_name = FINDTBGroup.DISTRICT_TB_SUPERVISOR_GROUP_NAME
        dtls_group = Group.objects.get(name=dtls_group_name)

        try:
            return district.role_set.get(group=dtls_group)
        except Role.DoesNotExist:
            return None


    def get_ztls(self):

        zone = self.get_zone()
        ztls_group_name = FINDTBGroup.ZONAL_TB_SUPERVISOR_GROUP_NAME
        ztls_group = Group.objects.get(name=ztls_group_name)

        try:
            return zone.role_set.get(group=ztls_group)
        except Location.DoesNotExist:
            return None


    def get_lab_techs(self):
        lab_tech_group_name = FINDTBGroup.DTU_LAB_TECH_GROUP_NAME
        lab_group = Group.objects.get(name=lab_tech_group_name)
        return self.role_set.filter(group=lab_group)



class Configuration(models.Model):

    class Meta:
        app_label = 'findtb'

    '''Store Key/value config options'''

    description = models.CharField(_('Description'), max_length=255,
                                   db_index=True)
    key = models.CharField(_('Key'), max_length=50, db_index=True)
    value = models.CharField(_('Value'), max_length=255,
                             db_index=True, blank=True)

    def __unicode__(self):
        return u"%s: %s" % (self.key, self.value)


    def get_dictionary(self):
        return {'key': self.key, 'value': self.value,
                'description': self.description}


    @classmethod
    def has_key(cls, key):
        return cls.objects.filter(key=key).count() != 0


    @classmethod
    def get(cls, key):
        '''get config value of specified key'''
        cfg = cls.objects.get(key__iexact=key)
        return cfg.value



class SlidesBatch(models.Model):
    """
        Group of slides, hold slides origin and date.
    """

    MONTH_QUARTERS = { 1: 1, 2: 1, 3: 1, 4: 2, 5: 2, 6: 2,
                      7: 3, 8: 3, 9: 3,10: 4, 11: 4, 12: 4 }

    QUARTER_BOUNDARIES = { 1: ((1, 1), (31, 3)), 2: ((1, 4), (30, 6)),
                           3: ((1, 7), (30, 9)), 4: ((1, 10), (31, 12))}

    class Meta:
        app_label = 'findtb'

    location = models.ForeignKey(Location)
    created_on = models.DateField(_(u"Created on"), default=datetime.date.today)
    created_by = models.ForeignKey(Reporter, blank=True, null=True)
    comment = models.CharField(max_length=100, blank=True)
    results = models.CharField(max_length=100, blank=True)
    objects = SlidesBatchManager()


    def save(self, *args, **kwargs):

        if not self.pk:
            try:
                SlidesBatch.objects.get_for_quarter_including_date(self.location,
                                                                    self.created_on)
            except SlidesBatch.DoesNotExist:
                pass
            else:
                raise IntegrityError(u"A Slides Batch already exists for this "\
                                      u"DTU and this quarter")
                                      
        super(SlidesBatch, self).save(*args, **kwargs)


    @classmethod
    def get_quarter(cls, date=None):
        """
        Return the quarter the given date is in. A quarter is a tuple with a number
        between 1 and 4 and a year.
        """
        date = date or datetime.date.today()
        return (cls.MONTH_QUARTERS[date.month], date.year)


    @property
    def quarter(self):
        return SlidesBatch.get_quarter(self.created_on)


    def __unicode__(self):

        q, y = self.get_quarter(self.created_on)
        return u"Batch of %(slides)s slides from %(location)s for EQA of "\
                "Q%(quarter)s %(year)s" % {'slides': self.slide_set.all().count(),
                                           'location': self.location,
                                           'quarter': q,
                                           'year': y}
                                           
    @models.permalink
    def get_absolute_url(self):
        q, y = self.get_quarter(self.created_on)
        return ('findtb-eqa-tracking', (),
                {'id':self.location.id, 'quarter':q, 'year':y})



class Slide(models.Model):
    """
    A slide of sputum to be tested for EQA. Hold an id and the tests results
    for the DTU, the first controller and the second controller.
    """

    RESULTS_CHOICES = (('negative', "Negative"),
                       ('1', "1+"),
                       ('2', "2+"),
                       ('3', "3+")) +\
                        tuple(('%s_afb' % x, "%s AFB" % x) for x in range(1, 20))

    class Meta:
        app_label = 'findtb'


    batch = models.ForeignKey(SlidesBatch)
    number = models.CharField(max_length=20, blank=True, null=True,
                              db_index=True, unique=True)

    dtu_results = models.CharField(max_length=10, blank=True,
                                   choices=RESULTS_CHOICES)

    first_ctrl_results = models.CharField(max_length=10, blank=True,
                                          choices=RESULTS_CHOICES)

    second_ctrl_results = models.CharField(max_length=10, blank=True,
                                           choices=RESULTS_CHOICES)

    cancelled = models.BooleanField(default=False)

    def save(self, *args, **kwargs):

        # django doesn't provide contrainst "unique if not blank"
        if not self.number: 
            self.number = None

        super(Slide, self).save(*args, **kwargs)


    def __unicode__(self):

        q, y = self.batch.get_quarter(self.batch.created_on)
        return u"Slides %(number)s from %(location)s for EQA of "\
                "Q%(quarter)s %(year)s" % {'number': self.number or '',
                                           'location': self.batch.location,
                                           'quarter': q,
                                           'year': y}

class Notice(models.Model):
    """
    A message sent as part of the stock management / notice system
    """

    class Meta:
        app_label = 'findtb'

    location = models.ForeignKey(Location, blank=True, null=True)
    reporter = models.ForeignKey(Reporter, blank=True, null=True)
    recieved_on = models.DateTimeField(auto_now_add=True)
    text = models.CharField(max_length=450, blank=True, null=True)
    response = models.CharField(max_length=450, blank=True, null=True)
    responded_on = models.DateTimeField(blank=True, null=True)
    responded_by = models.ForeignKey(User, related_name='notice_response', \
                                     blank=True, null=True)

    def __unicode__(self):
        return u"%(loc)s - %(text)s" % \
               {'loc': self.location, 'text':self.text}
