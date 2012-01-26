#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
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
    list_display = ('__unicode__', 'location', 'chw', 'status')
    search_fields = ['health_id', 'first_name', 'last_name']
    list_filter = ['status', 'dob', 'chw']
admin.site.register(Patient, PatientAdmin)


class HealthIdAdmin(VersionAdmin):
    search_fields = ['health_id']
admin.site.register(HealthId, HealthIdAdmin)

class EncounterAdmin(VersionAdmin):
    list_filter = ['sync_omrs', 'type']
    search_fields = ['patient__health_id']
admin.site.register(Encounter, EncounterAdmin)

#Reports


class CCReportAdmin(VersionAdmin):
    search_fields = ['encounter__patient__health_id']
admin.site.register(CCReport, CCReportAdmin)
admin.site.register(BirthReport, VersionAdmin)
admin.site.register(DeathReport, VersionAdmin)
admin.site.register(StillbirthMiscarriageReport, VersionAdmin)
admin.site.register(FollowUpReport, VersionAdmin)
admin.site.register(PregnancyReport, VersionAdmin)
admin.site.register(NeonatalReport, VersionAdmin)
admin.site.register(UnderOneReport, VersionAdmin)


class NutritionReportAdmin(VersionAdmin):
    list_filter = ['status', ]
    search_fields = ['encounter__patient__chw__username',]
admin.site.register(NutritionReport, NutritionReportAdmin)
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


class BednetIssuedReportAdmin(VersionAdmin):
    list_display = ('patient', 'bednet_received', 'chw', 'identity',
                    'encounter')
    list_filter = ('bednet_received', )
    search_fields = ['encounter__patient__health_id',
                    'encounter__chw__location__name',
                    'encounter__chw__first__name',
                    'encounter__chw__last__name']
admin.site.register(BednetIssuedReport, BednetIssuedReportAdmin)
admin.site.register(DrinkingWaterReport, VersionAdmin)
#PMTCT
admin.site.register(AntenatalVisitReport, VersionAdmin)


class AppointmentReportAdmin(VersionAdmin):
    list_filter = ('status', )
    search_fields = ['encounter__patient__health_id',]
admin.site.register(AppointmentReport, AppointmentReportAdmin)
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


class PolioCampaignReportAdmin(VersionAdmin):
    list_filter = ('phase', 'chw')
    list_display = ('patient', 'chw', 'created_on')
    search_fields = ['patient__health_id', 'chw__clinic__code']
admin.site.register(PolioCampaignReport, PolioCampaignReportAdmin)

admin.site.register(DistributionPoints)
