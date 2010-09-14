#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: rgaudin

from django.contrib import admin
from reversion.admin import VersionAdmin
from reversion.models import Version, Revision

from childcount.models import *

admin.site.register(Configuration)
admin.site.register(CHW)
admin.site.register(FormGroup)
admin.site.register(Clinic)


class PatientAdmin(VersionAdmin):
    list_display = ('__unicode__', 'location', 'chw')
    search_fields = ['health_id', 'first_name', 'last_name']
admin.site.register(Patient, PatientAdmin)


class HealthIdAdmin(VersionAdmin):
    search_fields = ['health_id']
admin.site.register(HealthId, HealthIdAdmin)

class EncounterAdmin(VersionAdmin):
    list_filter = ['sync_omrs', 'type']
admin.site.register(Encounter, EncounterAdmin)

#Reports
admin.site.register(CCReport, VersionAdmin)
admin.site.register(BirthReport, VersionAdmin)
admin.site.register(DeathReport, VersionAdmin)
admin.site.register(StillbirthMiscarriageReport, VersionAdmin)
admin.site.register(FollowUpReport, VersionAdmin)
admin.site.register(PregnancyReport, VersionAdmin)
admin.site.register(NeonatalReport, VersionAdmin)
admin.site.register(UnderOneReport, VersionAdmin)
admin.site.register(NutritionReport, VersionAdmin)
admin.site.register(FeverReport, VersionAdmin)
admin.site.register(ReferralReport, VersionAdmin)
admin.site.register(HouseholdVisitReport, VersionAdmin)
admin.site.register(FamilyPlanningReport, VersionAdmin)
admin.site.register(FamilyPlanningUsage, VersionAdmin)
admin.site.register(BCPillReport, VersionAdmin)
admin.site.register(BedNetReport, VersionAdmin)
admin.site.register(SickMembersReport, VersionAdmin)
admin.site.register(DangerSignsReport, VersionAdmin)
admin.site.register(MedicineGivenReport, VersionAdmin)
#Bednet Sanitation
admin.site.register(BednetUtilization, VersionAdmin)
admin.site.register(SanitationReport, VersionAdmin)
admin.site.register(BednetIssuedReport, VersionAdmin)
admin.site.register(DrinkingWaterReport, VersionAdmin)
#PMTCT
admin.site.register(AntenatalVisitReport, VersionAdmin)
admin.site.register(AppointmentReport, VersionAdmin)
admin.site.register(PregnancyRegistrationReport, VersionAdmin)
admin.site.register(HIVTestReport, VersionAdmin)
#Immunization
admin.site.register(ImmunizationSchedule, VersionAdmin)
admin.site.register(ImmunizationNotification, VersionAdmin)


class CodedItemAdmin(admin.ModelAdmin):
    list_filter = ('type', )
    list_display = ('code', 'local_code', 'description', 'type',)
admin.site.register(CodedItem, CodedItemAdmin)

admin.site.register(Case)
admin.site.register(Referral)
admin.site.register(Version)
admin.site.register(Revision)
admin.site.register(Vaccine)
admin.site.register(DeadPerson)
