#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: dgelvin


class CCForm(object):
    """An abstract class to hold the logic
    for an SMS form.
    """

    #KEYWORDS = {}
    MULTIPLE_PATIENTS = True
    
    PREFIX = '+'
    """The character prefix that should precede the
    form keyword.
    We use "+" everywhere to keep things standardized.
    """

    def __init__(self, message, date, chw, params, health_id):
        """
        :param message: SMS message being processed by this form
        :type message: :class:`rapidsms.Message`
        :param date: Encounter date of this form
        :type date: :class:`datetime.datetime`
        :param chw: CHW who submitted this form
        :type chw: :class:`childcount.models.CHW`
        :param params: Parameters passed to this form (as in :func:`sys.argv`)
        :type params: list
        :param health_id: Health ID for the encounter's patient
        :type health_id: str 

        """

        self.message = message
        self.date = date
        self.chw = chw
        self.params = params
        self.health_id = health_id
        self.encounter = None
        self.form_group = None
        self.response = ''

    def pre_process(self):
        """Processing to be done by this form *before*
        the patient's health ID is validated.

        This method used primarily for patient registration --
        when the health ID is not valid until the registration
        has completed. See
        :file:`apps/childcount/forms/PatientRegistrationForm.py` for
        an example.
        """

        pass

    def process(self, patient):
        """Processing to be done by this form once the
        encounter patient has been identified.
        Most forms implement their validation
        and DB logic here.
        """
        pass

    def post_process(self, forms_list):
        """Processing to be done *after* all :meth:`.process` has
        been called on all submitted forms.

        :param forms_list: List of successfully processed forms
        :type forms_list: list of instantiated 
                          :class:`childcount.forms.CCForm` objects

        """
        pass



