from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from models.general import Case 
from models.logs import MessageLog, EventLog, SystemErrorLog
from models.reports import Observation
from django.utils.translation import ugettext_lazy as _

class CaseAdmin(admin.ModelAdmin):
    list_display = ("ref_id", "first_name", "last_name", "gender", "dob", "estimated_dob", "location","created_at","reporter", "provider_mobile", "age","eligible_for_measles")
    search_fields = ['ref_id', 'first_name', 'last_name']
    list_filter = ("dob",'status')
    ordering = ('-dob',)
    
admin.site.register(Case, CaseAdmin)

class MessageLogAdmin(admin.ModelAdmin):
    list_display = ("sent_by_name", "mobile", "text", "created_at", "was_handled")
    list_filter = ("was_handled","created_at")
    search_fields = [ 'mobile','text', ]
    
admin.site.register(MessageLog, MessageLogAdmin)

class EventLogAdmin(admin.ModelAdmin):
    list_display = ("__unicode__",)
    list_filter = ("created_at", "message", "content_type")
    
admin.site.register(EventLog, EventLogAdmin)

class SystemErrorLogAdmin(admin.ModelAdmin):
    list_display = ("__unicode__",)
    list_filter = ("message", "created_at")
    
admin.site.register(SystemErrorLog, SystemErrorLogAdmin)


admin.site.register(Observation)
