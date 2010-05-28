#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: rgaudin

from django.contrib import admin
from reversion.admin import VersionAdmin
from reversion.models import Version, Revision

from childcount.models import *
from childcount.models.reports import *
admin.site.register(Configuration)


class CHWAdmin(admin.ModelAdmin):
    list_filter = ('location', )
admin.site.register(CHW, CHWAdmin)
admin.site.register(Encounter, VersionAdmin)
admin.site.register(FormGroup)
admin.site.register(Clinic)
admin.site.register(Patient, VersionAdmin)


class HealthIdAdmin(VersionAdmin):
    search_fields = ['health_id']
admin.site.register(HealthId, HealthIdAdmin)

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
admin.site.register(BedNetReport, VersionAdmin)
admin.site.register(SickMembersReport, VersionAdmin)
admin.site.register(DangerSignsReport, VersionAdmin)
admin.site.register(MedicineGivenReport, VersionAdmin)


class CodedItemAdmin(admin.ModelAdmin):
    list_filter = ('type', )

admin.site.register(CodedItem, CodedItemAdmin)
admin.site.register(CodedItemTranslation)

admin.site.register(Case)
admin.site.register(Referral)
admin.site.register(Version)
admin.site.register(Revision)
admin.site.register(Vaccine)
