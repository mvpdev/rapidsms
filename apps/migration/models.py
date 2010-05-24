#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

'''ChildCount Models

Case - Patient/Child model

CaseNote - case notes model
'''

import re
from datetime import datetime

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User, Group
from django.core.urlresolvers import reverse

from rapidsms.message import Message

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

from rapidsms.webui.managers import *
from patterns.models import Pattern
from locations.models import *


# TODO: remove this. it's a slightly weird version
#       of ReporterGroup, which can't be nested. i'm
#       not sure how it happened in the first place.

class Role(models.Model):
    """Basic representation of a role that someone can have.  For example,
       'supervisor' or 'data entry clerk'"""
    name = models.CharField(max_length=160)
    code = models.CharField(max_length=20, blank=True, null=True,\
        help_text="Abbreviation")
    patterns = models.ManyToManyField(Pattern, null=True, blank=True)

    def match(self, token):
        return self.regex and re.match(self.regex, token, re.IGNORECASE)

    @property
    def regex(self):
        # convenience accessor for joining patterns
        return Pattern.join(self.patterns)

    def __unicode__(self):
        return self.name


class ReporterGroup(models.Model):
    title       = models.CharField(max_length=30, unique=True)
    parent      = models.ForeignKey("self", related_name="mchildren", null=True, blank=True)
    description = models.TextField(blank=True)
    objects     = RecursiveManager()


    class Meta:
        verbose_name = "Group"


    def __unicode__(self):
        return self.title


    # TODO: rename to something that indicates
    #       that it's a counter, not a queryset
    def members(self):
        return self.reporters.all().count()


class Reporter(models.Model):
    """This model represents a KNOWN person, that can be identified via
       their alias and/or connection(s). Unlike the RapidSMS Person class,
       it should not be used to represent unknown reporters, since that
       could lead to multiple objects for the same "person". Usually, this
       model should be created through the WebUI, in advance of the reporter
       using the system - but there are always exceptions to these rules..."""
    alias      = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name  = models.CharField(max_length=30, blank=True)
    groups     = models.ManyToManyField(ReporterGroup, related_name="mreporters", blank=True)

    # here are some fields that don't belong here
    location   = models.ForeignKey(Location, related_name="mreporters", null=True, blank=True)
    role       = models.ForeignKey(Role, related_name="mreporters", null=True, blank=True)

    def __unicode__(self):
        return self.connection().identity


    # the language that this reporter prefers to
    # receive their messages in, as a w3c language tag
    #
    # the spec:   http://www.w3.org/International/articles/language-tags/Overview.en.php
    # reference:  http://www.iana.org/assignments/language-subtag-registry
    #
    # to summarize:
    #   english  = en
    #   amharic  = am
    #   chichewa = ny
    #   klingon  = tlh
    #
    language = models.CharField(max_length=10, blank=True)

    # although it's impossible to enforce, if a user registers
    # themself (via the app.py backend), this flag should be set
    # indicate that they probably shouldn't be trusted
    registered_self = models.BooleanField()


    class Meta:
        ordering = ["last_name", "first_name"]

        # define a permission for this app to use the @permission_required
        # decorator in reporter's views
        # in the admin's auth section, we have a group called 'manager' whose
        # users have this permission -- and are able to see this section
        permissions = (
            ("can_view", "Can view"),
        )


    def full_name(self):
        return ("%s %s" % (
            self.first_name,
            self.last_name)).strip()

    def __unicode__(self):
        return self.full_name()

    def __repr__(self):
        return "%s (%s)" % (
            self.full_name(),
            self.alias)

    def __json__(self):
        return {
            "pk":         self.pk,
            "alias":      self.alias,
            "first_name": self.first_name,
            "last_name":  self.last_name,
            "str":        unicode(self) }


    @classmethod
    def exists(klass, reporter, connection):
        """Checks if a reporter has already been entered into the system"""
        try:
            # look for a connection and reporter object matching what
            # was passed in, and if they are already linked then this
            # reporter already exists
            existing_conn = PersistantConnection.objects.get\
                (backend=connection.backend, identity=connection.identity)
            # this currently checks first and last name, location and role.
            # we may want to make this more lax
            filters = {"first_name" : reporter.first_name,
                       "last_name" : reporter.last_name,
                       "location" : reporter.location,
                       "role" : reporter.role }
            existing_reps = Reporter.objects.filter(**filters)
            for existing_rep in existing_reps:
                if existing_rep == existing_conn.reporter:
                    return True
            return False
        except PersistantConnection.DoesNotExist:
            # if we couldn't find a connection then they
            # don't exist
            return False

    @classmethod
    def parse_name(klass, flat_name):
        """Given a single string, this function returns a three-string
           tuple containing a suggested alias, first name, and last name,
           via some quite crude pattern matching."""

        patterns = [
            # try a few common name formats.
            # this is crappy but sufficient
            r"([a-z]+)",                       # Adam
            r"([a-z]+)\s+([a-z]+)",            # Evan Wheeler
            r"([a-z]+)\s+[a-z]+\.?\s+([a-z]+)",# Mark E. Johnston, Lee Harvey Oswald
            r"([a-z]+)\s+([a-z]+\-[a-z]+)"     # Erica Kochi-Fabian
        ]

        def unique(str):
            """Checks an alias for uniqueness; if it is already taken, alter it
               (by append incrementing digits) until an available alias is found."""

            n = 1
            alias = str.lower()

            # keep on looping until an alias becomes available.
            # --
            # WARNING: this isn't going to work at high volumes, since the alias
            # that we return might be taken before we have time to do anything
            # with it! This should logic should probably be moved to the
            # initializer, to make the find/grab alias loop atomic
            while klass.objects.filter(alias__iexact=alias).count():
                alias = "%s%d" % (str.lower(), n)
                n += 1

            return alias

        # try each pattern, returning as
        # soon as we find something that fits
        for pat in patterns:
            m = re.match("^%s$" % pat, flat_name, re.IGNORECASE)
            if m is not None:
                g = m.groups()

                # return single names as-is
                # they might already be aliases
                if len(g) == 1:
                    alias = unique(g[0].lower())
                    return (alias, g[0], "")

                else:
                    # return only the letters from
                    # the first and last names
                    alias = unique(g[0][0] + re.sub(r"[^a-zA-Z]", "", g[1]))
                    return (alias.lower(), g[0], g[1])

        # we have no idea what is going on,
        # so just return the whole thing
        alias = unique(re.sub(r"[^a-zA-Z]", "", flat_name))
        return (alias.lower(), flat_name, "")


    def connection(self):
        """Returns the connection object last used by this Reporter.
           The field is (probably) updated by app.py when receiving
           a message, so depends on _incoming_ messages only."""

        # TODO: add a "preferred" flag to connection, which then
        # overrides the last_seen connection as the default, here
        try:
            return self.connections.latest("last_seen")

        # if no connections exist for this reporter (how
        # did that happen?!), then just return None...
        except PersistantConnection.DoesNotExist:
            return None


    def last_seen(self):
        """Returns the Python datetime that this Reporter was last seen,
           on any Connection. Before displaying in the WebUI, the output
           should be run through the XXX  filter, to make it prettier."""

        # comprehend a list of datetimes that this
        # reporter was last seen on each connection,
        # excluding those that have never seen them
        timedates = [
            c.last_seen
            for c in self.connections.all()
            if c.last_seen is not None]

        # return the latest, or none, if they've
        # has never been seen on ANY connection
        return max(timedates) if timedates else None


class PersistantBackend(models.Model):
    """This class exists to provide a primary key for each
       named RapidSMS backend, which can be linked from the
       other modules. We can't use a char field with OPTIONS
       (in models which wish to link to a backend), since the
       available backends (and their orders) may change after
       deployment; hence, something persistant is needed."""
    slug  = models.CharField(max_length=30, unique=True)
    title = models.CharField(max_length=30)


    class Meta:
        verbose_name = "Backend"


    def __unicode__(self):
        return self.slug


    @classmethod
    def from_message(klass, msg):
        """"Fetch a PersistantBackend object from the data buried in a rapidsms.message.Message
            object. In time, this should be moved to the message object itself, since persistance
            should be fairly ubiquitous; but right now, that would couple the framework to this
            individual app. So you can use this for now."""
        be_slug = msg.connection.backend.slug
        return klass.objects.get(slug=be_slug)



class PersistantConnection(models.Model):
    """This class is a persistant version of the RapidSMS Connection
       class, to keep track of the various channels of communication
       that Reporters use to interact with RapidSMS (as a backend +
       identity pair, like rapidsms.connection.Connection). When a
       Reporter is seen communicating via a new backend, or is expected
       to do so in future, a PersistantConnection should be created,
       so they can be recognized by their backend + identity pair."""
    backend   = models.ForeignKey(PersistantBackend, related_name="connections")
    identity  = models.CharField(max_length=30)
    reporter  = models.ForeignKey(Reporter, related_name="mconnections", blank=True, null=True)
    last_seen = models.DateTimeField(blank=True, null=True)


    class Meta:
        verbose_name = "Connection"
        unique_together = ("backend", "identity")


    def __unicode__(self):
        return "%s:%s" % (
            self.backend,
            self.identity)

    def __json__(self):
        return {
            "pk": self.pk,
            "identity": self.identity,
            "reporter": self.reporter,
            "str": unicode(self) }


    @classmethod
    def from_message(klass, msg):
        obj, created = klass.objects.get_or_create(
            backend  = PersistantBackend.from_message(msg),
            identity = msg.connection.identity)

        if created:
            obj.save()

        # just return the object. it doesn't matter
        # if it was created or fetched. TODO: maybe
        # a parameter to return the tuple
        return obj


    def seen(self):
        """"Updates the last_seen field of this object to _now_, and saves.
            Unless the linked Reporter has an explict preferred connection
            (see PersistantConnection.prefer), calling this method will set
            it as the implicit default connection for the Reporter. """
        self.last_seen = datetime.now()
        return self.save()


    def prefer(self):
        """Removes the _preferred_ flag from all other PersistantConnection objects
           linked to the same Reporter, and sets the _preferred_ flag on this object."""
        for pc in PersistantConnection.objects.filter(reporter=self.reporter):
            pc.preferred = True if pc == self else False
            pc.save()

    def add_reporter_url(self):
        """Returns the URL to the "add-reporter" view, prepopulated with this
           PersistantConnection object. This shouldn't be here, since it couples
           the Model and view layers, but the folks in #django don't have any
           better suggestions."""
        return "%s?connection=%s" % (reverse("add-reporter"), self.pk)


class MigrateCHW(models.Model):
    class Meta:
        app_label = 'migration'
        verbose_name = _(u"MigrateCHW")
        verbose_name_plural = _(u"MigrateCHWs")
        ordering = ('oldid',)

    oldid = models.IntegerField(_("OldId"))
    newid = models.ForeignKey(CHW)

    def __unicode__(self):
        return u"%s: %s" % (self.oldid, self.newid)


class MigrateIDs(models.Model):

    '''Hold the old ids and the new health ids'''
    
    class Meta:
        app_label = 'migration'
        verbose_name = _(u"Migrate ID")
        verbose_name_plural = _(u"Migrate IDs")
        ordering = ('oldid',)

    oldid = models.IntegerField(_("OldId"), null=True)
    health_id = models.CharField(_(u"Health ID"), max_length=6, db_index=True, \
                                unique=True, help_text=_(u"Unique Health ID"))

    def __unicode__(self):
        return u"%s: %s" % (self.health_id, self.oldid)



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
    #default_parent()
    cases = Case.objects.all()
    print cases.count()

    for case in cases:
        if len(Patient.objects.filter(health_id=case.ref_id)) == 0:
            response = migrate_case(case)
            print response


def migrate_case(case):
    '''migrate a case to a patient

    case - is a Case object
    '''
    print case
    reporter = MigrateCHW.objects.get(oldid=case.reporter.id).newid
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

    health_id =  get_health_id(case.ref_id)
    form = PatientRegistrationForm(message, case.created_at, chw, params, \
                                   health_id)
    try:
        form.pre_process()
        response = form.response
    except Exception, e:
        response = e.message
    success = response.startswith('You successfuly registered')
    ml = MigrationLog(message=response, case=case, success=success, \
                        type='reg')
    ml.save()
    return response


def default_parent():
    '''create the default parent that will be used by all cases initially'''
    r = Reporter.objects.get(alias__iexact=u'help')
    reporter = MigrateCHW.objects.get(oldid=r.id).newid
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


def do_migration():
    '''run the entire migration'''
    #migrate chws
    migrate_chws()
    #create default parent
    default_parent()
    #migrate under fives
    migrate_patients()
    #migrate muac
    migrate_muacs()
    #migrate mrdt
    migrate_mrdts()


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


def migrate_reporter_backends():
    from reporters.models import PersistantBackend, PersistantConnection
    pygsm = PersistantBackend.objects.get(slug=u'pygsm')
    for pc in PersistantConnection.objects.all():
        pc.backend = pygsm
        pc.save()


def migrate_ids():
    '''place the health ids in MigrateIDs for migration'''
    with open('Sauri_Ids_1-20000.txt', 'r') as f:
        for health_id in f:
            try:
                mids = MigrateIDs(health_id=health_id)
                mids.save()
            except:
                pass

    return MigrateIDs.objects.all().count()


def get_health_id(ref_id):
    mid = MigrateIDs.objects.filter(oldid=None)[0]
    mid.oldid = int(ref_id)
    mid.save()
    return mid.health_id

