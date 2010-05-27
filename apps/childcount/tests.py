import os

from rapidsms.tests.scripted import TestScript
from django.core.management.commands.loaddata import Command

import reporters.app as reporter_app
import locations.app as locations_app

from locations.models import *
from childcount.models import CHW

from app import App
from childcount.forms import *
from childcount.commands import *


class TestApp (TestScript):
    apps = (reporter_app.App, locations_app.App, App,)
    App.forms = [PatientRegistrationForm, BirthForm, MobileForm, DeathForm, StillbirthMiscarriageForm, FollowUpForm, PregnancyForm, NeonatalForm, UnderOneForm, NutritionForm, FeverForm, ReferralForm, DangerSignsForm, MedicineGivenForm, HouseholdVisitForm, FamilyPlanningForm, BedNetForm]
    App.commands = [WhoCommand, RegistrationCommand]
    fixtures = ['uganda_locations', 'uganda_locations_type']

    def setUp(self):
        super(TestApp, self).setUp()

        
    def _register(self):
        #load location fixtures
        self.assertEquals(Location.objects.all().count(), 0)
        ldc = Command()
        filename = os.path.abspath(os.path.join(os.path.dirname(__file__),"fixtures/ruhiira_LocationType"))
        ldc.handle('location', filename)
        filename = os.path.abspath(os.path.join(os.path.dirname(__file__),"fixtures/ruhiira_Locations"))
        ldc.handle('location', filename)
        #print Location.objects.all()
        self.assertEquals(Location.objects.all().count(), 98)

        #load codes fixtures
        filename = os.path.abspath(os.path.join(os.path.dirname(__file__), \
                                    "fixtures/CodedItems"))
        ldc.handle('childcount', filename)

        self.runScript("""
            123 > chw bir lname fname
            123 < Success. You are now registered at Birare with alias @flname.
            123 > who
            123 < You are registered as Fname Lname from Birare with alias @flname.
        """)

    def test_registration_fails(self):
        self.runScript("""
            123 > who
            123 < 123 is not a registered number.
            123 > chw bidxcvxxx lname fname
            123 < Location bidxcvxxx does not exist
        """)
    '''
    def testCHWRegistration(self):
        self._register()
    '''

    def testYouMustBeRegistered(self):
        self.runScript("""
            123 > d345 +new bir mary unding f 19730512 p +mob 0720395121
            123 < You must register before you can send any reports.
        """)

    def testPatientRegistration(self):
        self._register()
        self.runScript("""
        123 > d345 +new bir mary unding f 19730512 p +mob 0720395121
        123 < Error while processing +NEW: Could not understand age or date_of_birth of 19730512 - Please correct and send all information again.
        123 > d345 +new bir mary unding f 12051973 p +mob 0720395121
        123 < +NEW, +MOB successfuly processed: [You successfuly registered D345 Mary Unding F/36y] [Mobile phone number: 0720395121]
        123 > d346 +new bir baby mary m 23022009 d345 d345
        123 < +NEW successfuly processed: [You successfuly registered D346 Baby Mary M/12m]
        """)

        #test forms
        #+V - visit
        self.runScript("""
            123 > +d346 +v y 1
            123 < Error: Could not understand your message. Your message must start with a single health ID, followed by a space then a + then the form keyword you are sending.
            123 > d346 +v y 1
            123 < +V successfuly processed: [Household member available, 1 children under 5 seen]
            123 > d346 +v y 1 ed nut
            123 < +V successfuly processed: [Household member available, 1 children under 5 seen, counseling / advice topics covered: General education, Nutrition]
        """)

        #+FP - family planning
        self.runScript("""
            123 > d346 +fp 1 1 cd
            123 < +FP failed: Unkown family planning code(s): CD No family planning recorded. You must send that form again.
            123 > d346 +fp 1 1
            123 < +FP failed: You must specify 1 family planning code(s). One for each of the 1 women using modern family planning. You must send that form again.
            123 > d346 +fp 1 1 c
            123 < +FP successfuly processed: [1 women, 1 using family planning: Condoms (1)]
            123 > d346 +bn 1
            123 < +BN failed: Not enough info, expected: number of bednets and number of sleeping sites You must send that form again.
            123 > d346 +bn 1 1
            123 < +BN successfuly processed: [1 bednets, 1 sleeping sites]
        """)

        #Individual forms
        self.runScript("""
            123 > d346 +U y n
            123 < +U successfuly processed: [Condition improved, Patient did not visit health facility]
            123 > d346 +S F
            123 < +S failed: Unkown danger sign code(s): F No danger signs recorded. You must send that form again.
            123 > d346 +S CV
            123 < +S successfuly processed: [Danger signs: Convulsions]
            123 > d346 +P 3 1 n
            123 < +P failed: Only female patients can be pregnant
            123 > d345 +P 3 1 n
            123 < +P failed: Weeks since last ANC visit must be a number You must send that form again.
            123 > d345 +P 3 1 0
            123 < +P successfuly processed: [3 months pregnant with 1 ANC visits, last ANC visit less than one week ago]
            123 > d346 +n 2
            123 < +N failed: Neonatal reports are only for children less than 28 days old
            123 > d346 +t n y
            123 < +T successfuly processed: [Not exclusive breast feeding, Up-to-date on immunisations]
            123 > d346 +m 134 n
            123 < +M successfuly processed: [MUAC of 134mm, No signs of oedema]
            123 > d346 +m 134 y
            123 < +M successfuly processed: [MUAC of 134mm, Oedema present]
            123 > d346 +m 134 y 10kg
            123 < +M successfuly processed: [MUAC of 134mm, Oedema present, Weight 10.0kg]
        """)

