#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: rgaudin

from datetime import date, datetime

from django.utils.translation import ugettext as _
from django.template import Context, Template


XFORM_DATE_FMT = "%Y-%m-%d"
XFORM_DATETIME_FMT = "%Y-%m-%dT%H:%M:%SZ"


class UnexpectedValueError(ValueError):
    pass


class OpenMRSTransmissionError(Exception):
    pass


class OpenMRSFormInterface(object):

    ''' Holds all OpenMRS Forms logic

    includes lots of value-checking logic
    as OMRS XForm module does no error handling '''

    # TYPES (cf. http://omrs/openmrs/admin/concepts/conceptDatatype.list)
    # NM: Numeric
    # CWE: Coded (concepts)
    # ST: Free Text
    # ZZ: Not Associated with DataType ; Rule (nodes ?)
    # RP: Document
    # DT: Date
    # TM: Time
    # TS: DateTime
    # BIT: Boolean
    # SN: Structured Numeric

    # Store reference to avoid free text
    T_NM = 'NM'
    T_CWE = 'CWE'
    T_ST = 'ST'
    T_ZZ = 'ZZ'
    T_RP = 'RP'
    T_DT = 'DT'
    T_TM = 'TM'
    T_TS = 'TS'
    T_BIT = 'BIT'
    T_SN = 'SN'
    T_BOOL = bool

    fields = {}
    values = {}

    # Patient Identification
    #patient_id = None
    patient___medical_record_number = None
    patient___identifier_type = 3
    patient___birthdate = None
    patient___birthdate_estimated = None
    patient___family_name = None
    patient___given_name = None
    patient___middle_name = None
    patient___sex = None

    # Encounter Informations
    encounter___encounter_datetime = None
    encounter___location_id = None
    encounter___provider_id = None

    # Template
    template_name = 'defaultForm.xml'

    def __init__(self, create, mri, location, provider, \
                     encounter_datetime=datetime.now(), dob=None, \
                     dob_estimate=False, family_name=None, given_name=None, \
                     middle_name=None, sex=None):

        # can't check much of those
        if not isinstance(location, int):
            raise UnexpectedValueError(_(u"Location requires int"))
        self.encounter___location_id = location
        if not isinstance(provider, int):
            raise UnexpectedValueError(_(u"Provider requires int"))
        self.encounter___provider_id = provider

        if not isinstance(encounter_datetime, datetime):
            raise UnexpectedValueError(_(u"Encounter datetime invalid"))
        self.encounter___encounter_datetime = \
                                    encounter_datetime.strftime(XFORM_DATETIME_FMT)

        # load template
        self.load_template()

        # Not creating a Patient ; skipping details
        if not create:
            self.patient___medical_record_number = mri
            return

        # checking required fields for new patient creation
        if None in (dob, family_name, given_name, sex):
            raise UnexpectedValueError(_(u"Missing required patient field"))

        if not isinstance(dob, (date, datetime)):
            raise UnexpectedValueError(_(u"Date of Birth requires date"))
        dob = dob.strftime(XFORM_DATE_FMT)

        if not isinstance(dob_estimate, bool):
            raise UnexpectedValueError(_(u"DOB estimate requires bool"))

        if not sex.upper() in ('M', 'F'):
            raise UnexpectedValueError(_(u"Sex is wrong"))
        else:
            sex = sex.upper()

        #assign new patient details
        self.patient___medical_record_number = mri
        self.patient___birthdate = dob
        self.patient___birthdate_estimated = dob_estimate
        self.patient___family_name = family_name
        self.patient___given_name = given_name
        self.patient___middle_name = middle_name
        self.patient___sex = sex

    def load_template(self):
        fp = open('apps/mgvmrs/templates/%(template)s' \
                % {'template': self.template_name})
        self.template = Template(fp.read())
        fp.close()

    def assign(self, field, value):
        ''' assign the value of a field '''
        if not field in self.fields:
            return None

        # retrive field definition
        ff_type, ff_values = self.fields[field]

        # Numeric Values
        if ff_type == self.T_NM:
            try:
                ff_value = value.strip()
            except AttributeError:
                ff_value = value
            try:
                tmp = float(ff_value)
            except ValueError:
                raise UnexpectedValueError(_(u"Expecting Numeric value"))

            self.values[field] = ff_value

        # Concept Values
        if ff_type == self.T_CWE:
            ff_value = value.strip()
            if not ff_value in ff_values:
                raise UnexpectedValueError(_(u"Unknown OpenMRS Concept"))
            self.values[field] = ff_value

        # ST: Free Text
        if ff_type == self.T_ST:
            ff_value = value.strip()
            self.values[field] = ff_value

        # ZZ: N/A list of concepts
        if ff_type == self.T_ZZ:
            ff_value = value
            try:
                tmp = ff_value.__iter__()
            except AttributeError:
                ff_value = [ff_value, ]

            ff_value_clean = []
            for val in ff_value:
                val = val.strip()
                if not val in ff_values:
                    raise UnexpectedValueError(_(u"Unknown OpenMRS Concept"))
                ff_value_clean.append(val)
            self.values[field] = ff_value_clean


        # RP: Document
        if ff_type == self.T_RP:
            pass

        # DT: Date
        if ff_type == self.T_DT:
            pass

        # TM: Time
        if ff_type == self.T_TM:
            pass

        # TS: DateTime
        if ff_type == self.T_TS:
            pass

        # BIT: Boolean
        if ff_type == self.T_BIT:
            ff_value = value.strip()
            try:
                tmp = bool(ff_value)
            except ValueError:
                raise UnexpectedValueError(_(u"Expecting Boolean value"))

            self.values[field] = ff_value

        # SN: Structured Numeric
        if ff_type == self.T_SN:
            pass

        # BOOL: python boolean
        if ff_type == self.T_BOOL:
            try:
                ff_value = bool(value)
            except ValueError:
                raise UnexpectedValueError(_(u"Expecting Boolean value"))
            self.values[field] = ff_value

    def retrieve(self, field):
        ''' get the value of one field '''
        return self.values[field]

    def template_dict(self):
        ''' dictionary of values for use in template '''

        form = {}
        for field in (
            'patient___medical_record_number',
            'patient___identifier_type',
            'patient___birthdate',
            'patient___birthdate_estimated',
            'patient___family_name',
            'patient___given_name',
            'patient___middle_name',
            'patient___sex',
            'encounter___encounter_datetime',
            'encounter___location_id',
            'encounter___provider_id',
        ):
            value = eval("self." + field)
            form[field] = value

        tpl_dict = self.values
        tpl_dict.update(form)

        return tpl_dict

    def render(self):
        ''' returns the XML formatted XForm data to submit to OMRS '''
        rendered = self.template.render(Context(self.template_dict()))
        return rendered
