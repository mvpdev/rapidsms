from django.db import models
from django.utils.translation import ugettext as _

from logger.models import OutgoingMessage
from reporters.models import Reporter

from djcelery.models import TaskMeta

class SmsAlertModel(models.Model):

    '''Log every sms alert planned to be sent'''

    class Meta:

        verbose_name = _(u"SMS Alert")
        verbose_name_plural = _(u"SMS Alerts")

    name = models.CharField(_(u"Alert Type"), max_length=255, 
                             blank=True, null=True)
    task_meta = models.ForeignKey(TaskMeta, null=True, blank=True)
    reporter = models.ForeignKey(Reporter)
    outgoing_message = models.ForeignKey(OutgoingMessage,  
                                        null=True, blank=True)
    cancelled = models.BooleanField(_("Cancelled"), default=False)

    
    
