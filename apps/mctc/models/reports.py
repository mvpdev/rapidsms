from django.db import models
from django.db.models import ObjectDoesNotExist
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from mctc.models.general import Case
from mctc.models.logs import MessageLog
from measles.models import ReportMeasles
from diarrhea.models import ReportDiarrhea
from diagnosis.models import ReportDiagnosis

from reporters.models import Reporter, Role
from locations.models import Location

from datetime import datetime, date, timedelta

class Report:
    def get_alert_recipients(self):
        """ Each report will send an alert, how it will choose when to send an alert
        is up to the model, however. """
        # this is the reporter, the provider or the CHW depending what you call it
        provider = self.provider
        facility = provider.clinic
        assert facility, "This provider does not have a clinic."

        recipients = []

        # find all the people assigned to alerts from this facility
        for user in facility.following_clinics.all():
            # only send if they want
            if user.alerts:
                if user not in recipients:
                    recipients.append(user)
        
        
        # find all the users monitoring this user
        for user in provider.following_users.all():
            if user.alerts:
                if user not in recipients:
                    recipients.append(user)

        return recipients

class Observation(models.Model):
    uid = models.CharField(max_length=15)
    name = models.CharField(max_length=255)
    letter = models.CharField(max_length=2, unique=True)

    class Meta:
        app_label = "mctc"
        ordering = ("name",)

    def __unicode__(self):
        return self.name

from mrdt.models import ReportMalaria
from muac.models import ReportMalnutrition
        
class ReportCHWStatus(Report, models.Model):
    class Meta:
        verbose_name = "CHW Perfomance Report"
        app_label = "mctc"
    @classmethod
    def get_providers_by_clinic(cls, duration_start, duration_end, muac_duration_start, clinic_id=None):
        
    
        ps      = []
        fields  = []
        counter = 0
        clinic_cases = 0
        clinic_mrdt = 0
        clinic_muac = 0
        clinic_sent = 0
        clinic_processed = 0
        clinic_refused = 0
        
        if clinic_id is not None:
            chwrole = Role.objects.get(code="chw")
            providers = Reporter.objects.filter(location=clinic_id, role=chwrole)
            for provider in providers:
                p = {}
                counter = counter + 1
                p['counter'] = "%d"%counter
                p['provider'] = provider
                p['num_cases'] = Case.count_by_provider(provider)
                p['num_cases_inactive'] = Case.count_by_provider(provider, Case.STATUS_INACTIVE)
                p['num_cases_dead'] = Case.count_by_provider(provider,Case.STATUS_DEAD)
                p['num_new_cases'] = Case.count_for_last_30_days(provider)
                p_muac = ReportMalaria.count_by_provider(provider, duration_end, duration_start)
                p['num_malaria_reports'] = p_muac
                clinic_mrdt = clinic_mrdt + p_muac 
                num_cases = p['num_cases']
                clinic_cases = clinic_cases + num_cases
                num_muac = ReportMalnutrition.count_by_provider(provider, duration_end, muac_duration_start)                
                clinic_muac = clinic_muac + num_muac
                if num_cases == 0:
                    muac_percentage = 0
                else:
                    muac_percentage  = round(float(float(num_muac)/float(num_cases))*100, 0)
                p['num_muac_reports'] = "%d %d%% (%s/%s)"%(num_muac, muac_percentage, num_muac, num_cases)
                sms_sent = MessageLog.count_by_provider(provider, duration_end, duration_start)
                clinic_sent = clinic_sent + sms_sent
                p['sms_sent'] = sms_sent
                sms_processed = MessageLog.count_processed_by_provider(provider, duration_end, duration_start)
                clinic_processed = clinic_processed + sms_processed
                p['sms_processed'] = sms_processed
                sms_refused = MessageLog.count_refused_by_provider(provider, duration_end, duration_start)
                clinic_refused = clinic_refused + sms_refused
                p['sms_refused'] = sms_refused
                if p['sms_sent'] != 0:
                    p['sms_rate'] = int(float(float(p['sms_processed'])/float(p['sms_sent'])*100))
                else:
                    p['sms_rate'] = 0
                #p['sms_rate'] = "%s%%"%p['sms_rate']
                last_activity = MessageLog.days_since_last_activity(provider)
                if last_activity == "" or ((duration_end - duration_start).days < last_activity):
                    p['days_since_last_activity'] = "No Activity"
                else:
                    p['days_since_last_activity'] = "%s days ago"%last_activity
                                    
                ps.append(p)
            
            #ps = sorted(ps)
            # Summary    
            p = {}
            p['counter'] = ""
            p['provider'] = "Summary"
            p['num_cases'] = clinic_cases
            p['num_malaria_reports'] = clinic_mrdt
            num_cases = clinic_cases
            num_muac = clinic_muac
            if num_cases == 0:
                muac_percentage = 0
            else:
                muac_percentage  = round(float(float(num_muac)/float(num_cases))*100, 0)
            p['num_muac_reports'] = "%d %% (%s/%s)"%(muac_percentage, num_muac, num_cases)
            p['sms_sent'] = clinic_sent
            p['sms_processed'] = clinic_processed
            p['sms_refused'] = clinic_refused
            if p['sms_sent'] != 0:
                p['sms_rate'] = int(float(float(p['sms_processed'])/float(p['sms_sent'])*100))
            else:
                p['sms_rate'] = 0
            #p['sms_rate'] = "%s%%"%p['sms_rate']
            p['days_since_last_activity'] = "" 
                                
            ps.append(p)
                    # caseid +|Y lastname firstname | sex | dob/age | guardian | provider  | date
            fields.append({"name": '#', "column": None, "bit": "{{ object.counter }}" })
            fields.append({"name": 'PROVIDER', "column": None, "bit": "{{ object.provider }}" })
            fields.append({"name": 'TOTAL CASES', "column": None, "bit": "{{ object.num_cases}}" })
            fields.append({"name": '# NEW CASES', "column": None, "bit": "{{ object.num_new_cases}}" })
            fields.append({"name": '# INACTIVE', "column": None, "bit": "{{ object.num_cases_inactive}}" })
            fields.append({"name": '# DEAD', "column": None, "bit": "{{ object.num_cases_dead}}" })
            fields.append({"name": 'MRDT', "column": None, "bit": "{{ object.num_malaria_reports }}" })
            fields.append({"name": 'MUAC', "column": None, "bit": "{{ object.num_muac_reports }}" })
            fields.append({"name": 'SMS RATE', "column": None, "bit": "{{ object.sms_rate }}% ({{ object.sms_processed }}/{{ object.sms_sent }})" })
            fields.append({"name": 'LAST ACTVITY', "column": None, "bit": "{{ object.days_since_last_activity }}" })
            return ps, fields 
        
    @classmethod
    def measles_summary(cls, duration_start, duration_end, muac_duration_start, clinic=None):            
        ps      = []
        fields  = []
        counter = 0
        eligible_cases=0
        vaccinated_cases = 0
        clinic_cases = 0
        if clinic is not None:
            # providers = Provider.list_by_clinic(clinic_id)
            chwrole = Role.objects.get(code="chw")
            reporters = Reporter.objects.filter(location=clinic, role=chwrole)
            # for provider in providers:
            for reporter in reporters:
                p = {}
                counter = counter + 1
                p['counter'] = "%d"%counter
                p['reporter'] = reporter
                p['num_cases'] = Case.count_by_provider(reporter)
                cases = Case.list_e_4_measles(reporter)
                p['eligible_cases'] = cases.count()                
                eligible_cases += p['eligible_cases'] 
                clinic_cases = clinic_cases + p['num_cases']
                #slow count
                slowcount = 0
                for case in cases:
                    if ReportMeasles.is_vaccinated(case):
                        slowcount += 1 
                mcases = ReportMeasles.get_vaccinated(reporter)
                #p['vaccinated_cases'] = mcases.count()                
                p['vaccinated_cases'] = slowcount
                p['not_vaccinated_cases'] = p['eligible_cases'] - p['vaccinated_cases']
                vaccinated_cases += p['vaccinated_cases']
                p['sms_sent'] = int(round(float(float(p['vaccinated_cases'])/float(p['eligible_cases']))*100, 0)) 
                                    
                ps.append(p)
            
            #ps = sorted(ps)
            # Summary    
            p = {}
            p['counter'] = ""
            p['reporter'] = "Summary"
            p['num_cases'] = clinic_cases
            p['eligible_cases'] = eligible_cases
            p['vaccinated_cases'] = vaccinated_cases     
            p['not_vaccinated_cases'] = eligible_cases - vaccinated_cases  
            sms_sent = int(round(float(float(vaccinated_cases)/float(eligible_cases))*100, 0))
            p['sms_sent'] = sms_sent
            ps.append(p)
                    # caseid +|Y lastname firstname | sex | dob/age | guardian | provider  | date
            fields.append({"name": '#', "column": None, "bit": "{{ object.counter }}" })
            fields.append({"name": 'CHW', "column": None, "bit": "{{ object.reporter }}" })
            fields.append({"name": 'TOTAL CASES', "column": None, "bit": "{{ object.num_cases}}" })
            fields.append({"name": '# ELIGIBLE CASES', "column": None, "bit": "{{ object.eligible_cases}}" })
            fields.append({"name": '# VACCINATED', "column": None, "bit": "{{ object.vaccinated_cases }}" })
            fields.append({"name": '# NOT VACCINATED', "column": None, "bit": "{{ object.not_vaccinated_cases }}" })
            fields.append({"name": '%', "column": None, "bit": "{{ object.sms_sent }}%" })
            return ps, fields
        
    @classmethod
    def measles_mini_summary(cls):            
        ps      = []
        fields  = []
        tcounter = 0
        teligible_cases=0
        tvaccinated_cases = 0
        tclinic_cases = 0
        clinics = Location.objects.filter(type__name="Clinic")
        for clinic in clinics:
            chwrole = Role.objects.get(code="chw")
            reporters = Reporter.objects.filter(location=clinic, role=chwrole)
            p = {}
            eligible_cases=0
            vaccinated_cases = 0
            clinic_cases = 0
            counter = 0
            p['clinic'] = clinic
            p['num_cases'] = 0
            p['eligible_cases'] = 0
            p['vaccinated_cases'] = 0
            for reporter in reporters:                
                counter = counter + 1
                #p['counter'] = "%d"%counter                
                cases = Case.list_e_4_measles(reporter)                 
                eligible_cases += cases.count() 
                clinic_cases = clinic_cases + Case.count_by_provider(reporter)
                mcases = ReportMeasles.get_vaccinated(reporter)
                #slow count
                slowcount = 0
                for case in cases:
                    if ReportMeasles.is_vaccinated(case):
                        slowcount += 1     
                #vaccinated_cases += mcases.count() 
                vaccinated_cases += slowcount
            
            # Summary    
            p = {}
            p['clinic'] = clinic
            p['counter'] = ""
            p['num_cases'] = clinic_cases
            p['eligible_cases'] = eligible_cases
            p['vaccinated_cases'] = vaccinated_cases
            ps.append(p)
            
            tcounter += counter
            teligible_cases += eligible_cases
            tvaccinated_cases += vaccinated_cases
            tclinic_cases +=clinic_cases
                    # caseid +|Y lastname firstname | sex | dob/age | guardian | provider  | date
        p = {}
        p['clinic'] = "Total:"
        p['counter'] = ""
        p['num_cases'] = tclinic_cases
        p['eligible_cases'] = teligible_cases
        p['vaccinated_cases'] = tvaccinated_cases
        ps.append(p)
        return ps       
        
class ReportAllPatients(Report, models.Model):
    class Meta:
        verbose_name = "CHW Perfomance Report"
        app_label = "mctc"
    @classmethod
    def by_provider(cls, reporter=None):    
        qs      = []
        fields  = []
        counter = 0
        if reporter is not None:
            cases   = Case.objects.order_by("last_name").filter(reporter=reporter, status=Case.STATUS_ACTIVE)
            
            for case in cases:
                q   = {}
                q['case']   = case
                counter = counter + 1
                q['counter'] = "%d"%counter
                try:
                    muacc   = ReportMalnutrition.objects.filter(case=case).latest()
                    #q['malnut'] = u"%(diag)s on %(date)s" % {'diag': muacc.diagnosis_msg(), 'date': muacc.entered_at.strftime("%Y-%m-%d")}
                    q['malnut_muac'] = "%s (%smm)"%(muacc.get_status_display(), muacc.muac)
                    q['malnut_symptoms'] = muacc.symptoms_keys()
                    q['malnut_days_since_last_update'] = muacc.days_since_last_activity()
                except ObjectDoesNotExist:
                    q['malnut_muac'] = ""
                    q['malnut_symptoms'] = ""
                    q['malnut_days_since_last_update'] = ""
                try:
                    orsc   = ReportDiarrhea.objects.filter(case=case).latest()
                    q['diarrhea'] = u"%(diag)s on %(date)s" % {'diag': orsc.diagnosis_msg(), 'date': orsc.entered_at.strftime("%Y-%m-%d")}
                except ObjectDoesNotExist:
                    q['diarrhea'] = None
                    
                try:
                    twoweeksago = date.today() - timedelta(14)
                    mrdtc   = ReportMalaria.objects.filter(case=case, entered_at__gte=twoweeksago).latest()
                    mrdtcd  = mrdtc.get_dictionary()
                    #q['malaria'] = u"result:%(res)s bednet:%(bed)s obs:%(obs)s on %(date)s" % {'res': mrdtcd['result_text'], 'bed': mrdtcd['bednet_text'], 'obs': mrdtcd['observed'], 'date': mrdtc.entered_at.strftime("%Y-%m-%d")}
                    q['malaria_result'] = mrdtc.results_for_malaria_result()
                    q['malaria_bednet'] = mrdtc.results_for_malaria_bednet()
                except ObjectDoesNotExist:
                    q['malaria_result'] = ""
                    q['malaria_bednet'] = ""
                    
                num_of_malaria_cases = ReportMalaria.num_reports_by_case(case)                
                if num_of_malaria_cases is not None and num_of_malaria_cases > 1:
                     q['malaria_result'] = q['malaria_result'] + "(%sX)"%num_of_malaria_cases
                     last_mrdt = ReportMalaria.days_since_last_mrdt(case)
                     if last_mrdt is not "" and last_mrdt < 15:
                         q['malaria_result'] = q['malaria_result'] + " %s days ago"%last_mrdt
                    
                try:
                    dc      = ReportDiagnosis.objects.filter(case=case).latest('entered_at')
                    dcd     = dc.get_dictionary()
                    q['diagnosis'] = u"diag:%(diag)s labs:%(lab)s on %(date)s" % {'diag': dcd['diagnosis'], 'lab': dcd['labs_text'], 'date': dc.entered_at.strftime("%Y-%m-%d")}
                except ObjectDoesNotExist:
                    q['diagnosis'] = None
                
                qs.append(q)
            # caseid +|Y lastname firstname | sex | dob/age | guardian | provider  | date
            fields.append({"name": '#', "column": None, "bit": "{{ object.counter }}" })
            fields.append({"name": 'PID#', "column": None, "bit": "{{ object.case.ref_id }}" })
            fields.append({"name": 'NAME', "column": None, "bit": "{{ object.case.last_name }} {{ object.case.first_name }}" })
            fields.append({"name": 'SEX', "column": None, "bit": "{{ object.case.gender }}" })
            fields.append({"name": 'AGE', "column": None, "bit": "{{ object.case.age }}" })            
            fields.append({"name": 'MRDT', "column": None, "bit": "{{ object.malaria_result }}" })
            fields.append({"name": 'BEDNET', "column": None, "bit": "{{ object.malaria_bednet }}" })
            fields.append({"name": 'CMAM', "column": None, "bit": "{{ object.malnut_muac }} {{object.malnut_days_since_last_update}}" })
            fields.append({"name": 'SYMPTOMS', "column": None, "bit": "{{ object.malnut_symptoms}}" })
            #fields.append({"name": 'LAST UPDATE', "column": None, "bit": "{{ object.case.date_registered }}" })
            
            return qs, fields
    @classmethod
    def malnut_trend_by_provider(cls, provider_id=None):    
        qs      = []
        fields  = []
        counter = 0
        if provider_id is not None:
            cases   = Case.objects.order_by("last_name").filter(provider=provider_id)
        else:
            cases   = Case.objects.order_by("last_name")
        if cases:
            for case in cases:
                q   = {}
                q['case']   = case
                
                
                try:
                    muacc   = ReportMalnutrition.objects.filter(case=case).order_by("entered_at")
                    trend = ""
                    scase = False
                    for m in muacc:
                        mrpt = m.get_dictionary()
                        mrpt["entered_at"] = m.entered_at.strftime("%d.%m.%y")
                        if trend != "":
                            trend += ", "
                        trend += "%(diagnosis)s %(muac)s(%(entered_at)s)" % mrpt
                        if m.status in [1,2,3]:
                            scase = True
                    #q['malnut'] = u"%(diag)s on %(date)s" % {'diag': muacc.diagnosis_msg(), 'date': muacc.entered_at.strftime("%Y-%m-%d")}
                    q['trend'] = trend
                except ObjectDoesNotExist:
                    q['trend'] = ""
                if scase:
                    counter = counter + 1
                    q['counter'] = "%d"%counter
                    qs.append(q)
            # caseid +|Y lastname firstname | sex | dob/age | guardian | provider  | date
            fields.append({"name": '#', "column": None, "bit": "{{ object.counter }}" })
            fields.append({"name": 'PID#', "column": None, "bit": "{{ object.case.ref_id }}" })
            fields.append({"name": 'NAME', "column": None, "bit": "{{ object.case.short_name }}" })
            fields.append({"name": 'SEX', "column": None, "bit": "{{ object.case.gender }}" })
            fields.append({"name": 'AGE', "column": None, "bit": "{{ object.case.short_dob }} - {{ object.case.age }}" })            
            fields.append({"name": 'CMAM Trend', "column": None, "bit": "{{ object.trend }}" })
            fields.append({"name": 'CHW', "column": None, "bit": "{{ object.provider }} {{ object.provider.mobile }}" })
            fields.append({"name": 'Village', "column": None, "bit": "{{ object.case.zone }}" })
            
            return qs, fields

    @classmethod
    def measles_by_provider(cls, provider_id=None):    
        qs      = []
        fields  = []
        counter = 0
        if provider_id is not None:
            provider = Provider.objects.get(id=provider_id)
            cases   = Case.list_e_4_measles(provider)
            
            for case in cases:
                q   = {}
                q['case']   = case
                counter = counter + 1
                q['counter'] = "%d"%counter
                try:
                    muacc   = ReportMalnutrition.objects.filter(case=case).latest()
                    #q['malnut'] = u"%(diag)s on %(date)s" % {'diag': muacc.diagnosis_msg(), 'date': muacc.entered_at.strftime("%Y-%m-%d")}
                    q['malnut_muac'] = "%s (%smm)"%(muacc.get_status_display(), muacc.muac)
                    q['malnut_symptoms'] = muacc.symptoms()
                    q['malnut_days_since_last_update'] = muacc.days_since_last_activity()
                except ObjectDoesNotExist:
                    q['malnut_muac'] = ""
                    q['malnut_symptoms'] = ""
                    q['malnut_days_since_last_update'] = ""
                try:
                    orsc   = ReportDiarrhea.objects.filter(case=case).latest()
                    q['diarrhea'] = u"%(diag)s on %(date)s" % {'diag': orsc.diagnosis_msg(), 'date': orsc.entered_at.strftime("%Y-%m-%d")}
                except ObjectDoesNotExist:
                    q['diarrhea'] = None
                    
                try:
                    twoweeksago = date.today() - timedelta(14)
                    mrdtc   = ReportMalaria.objects.filter(case=case, entered_at__gte=twoweeksago).latest()
                    mrdtcd  = mrdtc.get_dictionary()
                    #q['malaria'] = u"result:%(res)s bednet:%(bed)s obs:%(obs)s on %(date)s" % {'res': mrdtcd['result_text'], 'bed': mrdtcd['bednet_text'], 'obs': mrdtcd['observed'], 'date': mrdtc.entered_at.strftime("%Y-%m-%d")}
                    q['malaria_result'] = mrdtc.results_for_malaria_result()
                    q['malaria_bednet'] = mrdtc.results_for_malaria_bednet()
                except ObjectDoesNotExist:
                    q['malaria_result'] = ""
                    q['malaria_bednet'] = ""
                    
                num_of_malaria_cases = ReportMalaria.num_reports_by_case(case)                
                if num_of_malaria_cases is not None and num_of_malaria_cases > 1:
                     q['malaria_result'] = q['malaria_result'] + "(%sX)"%num_of_malaria_cases
                     last_mrdt = ReportMalaria.days_since_last_mrdt(case)
                     if last_mrdt is not "" and last_mrdt < 15:
                         q['malaria_result'] = q['malaria_result'] + " %s days ago"%last_mrdt
                    
                try:
                    dc      = ReportDiagnosis.objects.filter(case=case).latest('entered_at')
                    dcd     = dc.get_dictionary()
                    q['diagnosis'] = u"diag:%(diag)s labs:%(lab)s on %(date)s" % {'diag': dcd['diagnosis'], 'lab': dcd['labs_text'], 'date': dc.entered_at.strftime("%Y-%m-%d")}
                except ObjectDoesNotExist:
                    q['diagnosis'] = None

                
                q['vaccinated'] = ReportMeasles.is_vaccinated(case)
                if q['vaccinated']:
                    q['sent'] = u"Yes"
                    q['vaccinated'] = u"Yes" 
                else:
                    q['vaccinated'] = u"No"
                    q['sent'] = u"No"
                    qs.append(q)

            # caseid +|Y lastname firstname | sex | dob/age | guardian | provider  | date
            fields.append({"name": '#', "column": None, "bit": "{{ object.case.zone }}" })
            fields.append({"name": 'PID#', "column": None, "bit": "{{ object.case.ref_id }}" })
            fields.append({"name": 'NAME', "column": None, "bit": "{{ object.case.last_name }} {{ object.case.first_name }}" })
            fields.append({"name": 'SEX', "column": None, "bit": "{{ object.case.gender }}" })
            fields.append({"name": 'AGE', "column": None, "bit": "{{ object.case.age }}" })            
            fields.append({"name": 'VACCINATED?', "column": None, "bit": "{{ object.vaccinated }}" })
            fields.append({"name": 'SENT?', "column": None, "bit": "{{ object.sent }}" })
            
            return qs, fields

    @classmethod
    def malaria_by_provider(cls, provider_id=None):    
        qs      = []
        fields  = []
        counter = 0
        if provider_id is None:
            #cases   = Case.objects.order_by("last_name").filter(provider=provider_id)
            malrpts = ReportMalaria.objects.order_by("case").order_by("result")
            
            for case in malrpts:
                q   = {}
                
                q['case']   = case.case
                q['reporter']   = case.reporter
                counter = counter + 1
                q['counter'] = "%d"%counter
                    
                try:
                    twoweeksago = date.today() - timedelta(14)
                    mrdtc   = ReportMalaria.objects.filter(case=case.case).latest()
                    mrdtcd  = mrdtc.get_dictionary()
                    #q['malaria'] = u"result:%(res)s bednet:%(bed)s obs:%(obs)s on %(date)s" % {'res': mrdtcd['result_text'], 'bed': mrdtcd['bednet_text'], 'obs': mrdtcd['observed'], 'date': mrdtc.entered_at.strftime("%Y-%m-%d")}
                    q['malaria_result'] = mrdtc.results_for_malaria_result()
                    q['malaria_bednet'] = mrdtc.results_for_malaria_bednet()
                except ObjectDoesNotExist:
                    q['malaria_result'] = ""
                    q['malaria_bednet'] = ""
                    
                num_of_malaria_cases = ReportMalaria.num_reports_by_case(case)                
                if num_of_malaria_cases is not None and num_of_malaria_cases > 1:
                     q['malaria_result'] = q['malaria_result'] + "(%sX)"%num_of_malaria_cases
                     last_mrdt = ReportMalaria.days_since_last_mrdt(case)
                     if last_mrdt is not "" and last_mrdt < 15:
                         q['malaria_result'] = q['malaria_result'] + " %s days ago"%last_mrdt
                                
                qs.append(q)
            # caseid +|Y lastname firstname | sex | dob/age | guardian | provider  | date
            fields.append({"name": '#', "column": None, "bit": "{{ object.counter }}" })
            fields.append({"name": 'PID#', "column": None, "bit": "{{ object.case.ref_id }}" })
            fields.append({"name": 'NAME', "column": None, "bit": "{{ object.case.short_name }}" })
            fields.append({"name": 'SEX', "column": None, "bit": "{{ object.case.gender }}" })
            fields.append({"name": 'AGE', "column": None, "bit": "{{ object.case.short_dob }} - {{ object.case.age }}" })            
            fields.append({"name": 'MRDT', "column": None, "bit": "{{ object.malaria_result }}" })
            fields.append({"name": 'BEDNET', "column": None, "bit": "{{ object.malaria_bednet }}" })
            fields.append({"name": 'LAST UPDATE', "column": None, "bit": "{{ object.case.date_registered }}" })
            fields.append({"name": 'CHW', "column": None, "bit": "{{ object.reporter}}" })
            fields.append({"name": 'Village', "column": None, "bit": "{{ object.case.zone }}" })
            
            return qs, fields
    
    @classmethod
    def malaria_at_risk(cls, duration_start, duration_end, clinic=None):    
        qs      = []
        fields  = []
        counter = 0
        if clinic is None:
            #cases   = Case.objects.order_by("last_name").filter(provider=provider_id)
            malrpts = ReportMalaria.objects.filter(result=True, entered_at__gte=duration_start,entered_at__lte=duration_end).values("case").distinct().order_by("case__location")
        else:
            malrpts = ReportMalaria.objects.filter(result=True, entered_at__gte=duration_start,entered_at__lte=duration_end, case__location=clinic).values("case").distinct().order_by("case__location")
        for case in malrpts:
            q   = {}
            case = ReportMalaria.objects.filter(case__id=case["case"]).latest()
            q['case']   = case.case
            q['date']   = case.entered_at.strftime("%d.%m.%y")
            q['mobile']   = case.provider_number()
            q['reporter']   = case.reporter
            q['result']   = case.results_for_malaria_result()
            q['bednet'] = case.results_for_malaria_bednet()            
            q['name'] =  u"%s %s"%(q['case'].last_name, q['case'].first_name)
            counter = counter + 1
            q['counter'] = "%d"%counter
                
            num_of_malaria_cases = ReportMalaria.num_reports_by_case(case.case)                
            q['num_of_malaria_cases'] = "%d"%num_of_malaria_cases
            q['symptoms'] = case.symptoms()
            qs.append(q)
        # caseid +|Y lastname firstname | sex | dob/age | guardian | provider  | date
        fields.append({"name": '#', "column": None, "bit": "{{ object.counter }}" })
        fields.append({"name": 'PID#', "column": None, "bit": "{{ object.case.ref_id }}" })
        fields.append({"name": 'NAME', "column": None, "bit": "{{ object.name }}" })
        fields.append({"name": 'SEX', "column": None, "bit": "{{ object.case.gender }}" })
        fields.append({"name": 'AGE', "column": None, "bit": "{{ object.case.age }}" })            
        fields.append({"name": 'MRDT', "column": None, "bit": "{{ object.result }}" })
        fields.append({"name": 'BEDNET', "column": None, "bit": "{{ object.bednet }}" })
        fields.append({"name": 'DATE', "column": None, "bit": "{{ object.date }}" })
        fields.append({"name": 'TIMES', "column": None, "bit": "{{ object.num_of_malaria_cases }}" })
        fields.append({"name": 'CHW', "column": None, "bit": "{{ object.reporter}}" })
        fields.append({"name": 'MOBILE', "column": None, "bit": "{{ object.mobile }}" })
        fields.append({"name": 'SYMPTOMS', "column": None, "bit": "{{ object.symptoms }}" })
        
        return qs, fields
    
    @classmethod
    def malnutrition_at_risk(cls, duration_start, duration_end, clinic=None):
        """
        Show at risk Cases for malnutrition reports
        """    
        qs      = []
        fields  = []
        counter = 0
        if clinic is None:
            #cases   = Case.objects.order_by("last_name").filter(provider=provider_id)
            malrpts = ReportMalnutrition.objects.filter(entered_at__gte=duration_start,entered_at__lte=duration_end).exclude(status=ReportMalnutrition.HEALTHY_STATUS).values("case").distinct().order_by("status")
        else:
            malrpts = ReportMalnutrition.objects.filter(entered_at__gte=duration_start,entered_at__lte=duration_end, case__location=clinic).exclude(status=ReportMalnutrition.HEALTHY_STATUS).values("case").distinct().order_by("status")
        for case in malrpts:
            q   = {}
            muac = ReportMalnutrition.objects.filter(case__id=case["case"]).latest()
            q['case']   = muac.case
            q['date']   = muac.entered_at.strftime("%d.%m.%y")
            q['mobile']   = muac.provider_number()
            q['reporter']   = muac.reporter
            
            q['malnut_muac'] = "%s (%smm)"%(muac.get_status_display(), muac.muac)
                        
            q['name'] =  u"%s %s"%(q['case'].last_name, q['case'].first_name)
            counter = counter + 1
            q['counter'] = "%d"%counter
                
            num_of_muac_cases = ReportMalnutrition.num_reports_by_case(muac.case)                
            q['num_of_muac_cases'] = "%d"%num_of_muac_cases
            q['symptoms'] = muac.symptoms_keys()
            qs.append(q)
        # caseid +|Y lastname firstname | sex | dob/age | guardian | provider  | date
        fields.append({"name": '#', "column": None, "bit": "{{ object.counter }}" })
        fields.append({"name": 'PID#', "column": None, "bit": "{{ object.case.ref_id }}" })
        fields.append({"name": 'NAME', "column": None, "bit": "{{ object.name }}" })
        fields.append({"name": 'SEX', "column": None, "bit": "{{ object.case.gender }}" })
        fields.append({"name": 'AGE', "column": None, "bit": "{{ object.case.age }}" })            
        fields.append({"name": 'MUAC', "column": None, "bit": "{{ object.malnut_muac }}" })
        fields.append({"name": 'DATE', "column": None, "bit": "{{ object.date }}" })
        fields.append({"name": '#', "column": None, "bit": "{{ object.num_of_muac_cases }}" })
        fields.append({"name": 'CHW', "column": None, "bit": "{{ object.reporter.last_name}}" })
        fields.append({"name": 'MOBILE', "column": None, "bit": "{{ object.mobile }}" })
        fields.append({"name": 'SYMPTOMS', "column": None, "bit": "{{ object.symptoms }}" })
        
        return qs, fields
    
    
    @classmethod
    def malnut_by_provider(cls):    
        qs      = []
        fields  = []
        counter = 0
        provider_id=None
        if provider_id is None:
            #cases   = Case.objects.order_by("last_name").filter(provider=provider_id)
            muacs = ReportMalnutrition.objects.order_by("provider").exclude(status=4).order_by("status")
            
            for muacc in muacs:
                q   = {}
                
                q['case']   = muacc.case
                q['reporter']   = muacc.reporter
                counter = counter + 1
                q['counter'] = "%d"%counter
                try:
                    #muacc   = ReportMalnutrition.objects.filter(case=case).latest()
                    q['malnut'] = u"%(diag)s on %(date)s" % {'diag': muacc.diagnosis_msg(), 'date': muacc.entered_at.strftime("%Y-%m-%d")}
                    q['malnut_muac'] = "%s (%smm)"%(muacc.get_status_display(), muacc.muac)
                    q['malnut_symptoms'] = muacc.symptoms()
                    q['malnut_days_since_last_update'] = "%s days ago"%muacc.days_since_last_activity()
                except ObjectDoesNotExist:
                    q['malnut_muac'] = ""
                    q['malnut_symptoms'] = ""
                    q['malnut_days_since_last_update'] = ""
                                
                qs.append(q)
            # caseid +|Y lastname firstname | sex | dob/age | guardian | provider  | date
            fields.append({"name": '#', "column": None, "bit": "{{ object.counter }}" })
            fields.append({"name": 'PID#', "column": None, "bit": "{{ object.case.ref_id }}" })
            fields.append({"name": 'NAME', "column": None, "bit": "{{ object.case.short_name }}" })
            fields.append({"name": 'SEX', "column": None, "bit": "{{ object.case.gender }}" })
            fields.append({"name": 'AGE', "column": None, "bit": "{{ object.case.short_dob }} - {{ object.case.age }}" })            
            fields.append({"name": 'CMAM', "column": None, "bit": "{{ object.malnut_muac }} {{object.malnut_days_since_last_update}}" })
            fields.append({"name": 'SYMPTOMS', "column": None, "bit": "{{ object.malnut_symptoms}}" })
            fields.append({"name": 'CHW', "column": None, "bit": "{{ object.reporter }}" })
            fields.append({"name": 'Village', "column": None, "bit": "{{ object.case.zone }}" })
            
            return qs, fields

    @classmethod
    def malnutrition_screening_info(cls,site=None):
        """
        Show information required for malnutrition screening forms. SNCC
        """    
        qs      = []
        fields  = []

        counter = 0
	
        if site is None:
            #cases   = Case.objects.order_by("last_name").filter(provider=provider_id)
            cases   = Case.objects.order_by("last_name","first_name").filter(status=Case.STATUS_ACTIVE).distinct()
        else:
            cases   = Case.objects.order_by("last_name","first_name").filter(location=site, status=Case.STATUS_ACTIVE).distinct()

        for case in cases:
            q   = {}
            q['case']   = case
            q['name'] =  u"%s %s"%(q['case'].last_name.upper(), q['case'].first_name)
            if case.dob == None:
               q['dob'] = ''
            else:
               q['dob'] = case.dob.strftime("%d.%m.%y")
            
            if case.guardian_id == None:
                case.guardian_id = ''

            if case.gender == None:
                case.gender = ''

            counter = counter + 1
            q['counter'] = "%d"%counter
            try:
                muacc   = ReportMalnutrition.objects.filter(case=case).latest()
                
                #q['malnut'] = u"%(diag)s on %(date)s" % {'diag': muacc.diagnosis_msg(), 'date': muacc.entered_at.strftime("%Y-%m-%d")}
                q['malnut_muac'] = "%s"%(muacc.muac)
                if muacc.weight > 0:
                    q['malnut_weight'] = "%s"%(muacc.weight)
                else:
                    q['malnut_weight'] = ""
                
                q['malnut_symptoms'] = muacc.symptoms_keys()
                q['malnut_days_since_last_update'] = muacc.days_since_last_activity()
                q['malnut_entered_at'] = muacc.entered_at.strftime("%d.%m.%Y")

            except ObjectDoesNotExist:
                q['malnut_muac'] = ""
                q['malnut_symptoms'] = ""
                q['malnut_days_since_last_update'] = ""

            qs.append(q)


        # caseid +|Y lastname firstname | sex | dob/age | guardian | provider  | date

        fields.append({"name": 'No', "column": None, "bit": "{{ object.counter }}" })
        fields.append({"name": 'Nom', "column": None, "bit": "{{ object.name }}" })
        fields.append({"name": 'Sexe', "column": None, "bit": "{{ object.case.gender }}" })
        fields.append({"name": 'DN', "column": None, "bit": "{{ object.dob }}" }) 
        fields.append({"name": 'Age', "column": None, "bit": "{{ object.case.age }}" })
        fields.append({"name": 'Nom de Mere', "column": None, "bit": "{{ object.case.guardian }}" })
        fields.append({"name": 'Carte ID', "column": None, "bit": "{{ object.case.guardian_id }}" })
#        fields.append({"name": 'Dernier Depistage', "column": None, "bit": "{{ object.malnut_entered_at }}" })
        fields.append({"name": 'SMS', "column": None, "bit": "PB" })          
        fields.append({"name": 'No Enfant', "column": None, "bit": "+{{ object.case.ref_id }}" })
        fields.append({"name": 'PB (mm)', "column": None, "bit": "{{ object.malnut_muac }}" })
#        fields.append({"name": 'SYMPTOMS', "column": None, "bit": "{{ object.symptoms }}" })
        fields.append({"name": 'Poids (kg)', "column": None, "bit": "{{ object.malnut_weight }}" })
        fields.append({"name": 'Oedemes', "column": None, "bit": "" })
        fields.append({"name": 'CONSULTER', "column": None, "bit": "[  ]" })
#        fields.append({"name": 'MOBILE', "column": None, "bit": "{{ object.mobile }}" })

        
        return qs, fields

    # Ajout Assane
    @classmethod
    def by_age(cls,age_mois,cases=None):    
        """
        Show information required for malnutrition screening forms. SNCC
        """    
        qs      = []
        fields  = []

        counter = 0
       
        #for case in cases:

	for case in cases:
	  if (age_mois==0):
		q   = {}
        	q['case']   = case
	        q['name'] =  u"%s %s"%(q['case'].last_name.upper(), q['case'].first_name)
        	counter = counter + 1
	        q['counter'] = "%d"%counter
        	try:
	            muacc   = ReportMalnutrition.objects.filter(case=case).latest()
                
                #q['malnut'] = u"%(diag)s on %(date)s" % {'diag': muacc.diagnosis_msg(), 'date': muacc.entered_at.strftime("%Y-%m-%d")}
        	    q['malnut_muac'] = "%smm"%(muacc.muac)
        	    q['malnut_weight'] = "%s kg"%(muacc.weight)
        	    q['malnut_symptoms'] = muacc.symptoms_keys()
        	    q['malnut_days_since_last_update'] = muacc.days_since_last_activity()
        	except ObjectDoesNotExist:
        	    q['malnut_muac'] = ""
        	    q['malnut_symptoms'] = ""
        	    q['malnut_days_since_last_update'] = ""

		qs.append(q)
 	  else:
                delta=datetime.now().date()
	        if case.dob is not None:
                  delta = datetime.now().date() - case.dob          
             	  age=int(delta.days/30.4375)
                if (age==age_mois):               

         	  q   = {}
        	  q['case']   = case
	          q['name'] =  u"%s %s"%(q['case'].last_name.upper(), q['case'].first_name)
        	  counter = counter + 1
	          q['counter'] = "%d"%counter
        	  try:
	            muacc   = ReportMalnutrition.objects.filter(case=case).latest()
                
                #q['malnut'] = u"%(diag)s on %(date)s" % {'diag': muacc.diagnosis_msg(), 'date': muacc.entered_at.strftime("%Y-%m-%d")}
        	    q['malnut_muac'] = "%smm"%(muacc.muac)
        	    q['malnut_weight'] = "%s kg"%(muacc.weight)
        	    q['malnut_symptoms'] = muacc.symptoms_keys()
        	    q['malnut_days_since_last_update'] = muacc.days_since_last_activity()
        	  except ObjectDoesNotExist:
        	    q['malnut_muac'] = ""
        	    q['malnut_symptoms'] = ""
        	    q['malnut_days_since_last_update'] = ""

                  qs.append(q)


        # caseid +|Y lastname firstname | sex | dob/age | guardian | provider  | date

        fields.append({"name": 'No', "column": None, "bit": "{{ object.counter }}" })
        fields.append({"name": 'Nom', "column": None, "bit": "{{ object.name }}" })
        fields.append({"name": 'Sexe', "column": None, "bit": "{{ object.case.gender }}" })
        fields.append({"name": 'DN', "column": None, "bit": "{{ object.case.dob }}" }) 
        fields.append({"name": 'Age', "column": None, "bit": "{{ object.case.age }}" })
        fields.append({"name": 'Nom de Mere', "column": None, "bit": "{{ object.case.guardian }}" })
        fields.append({"name": 'SMS', "column": None, "bit": "PB" })          
        fields.append({"name": 'No Enfant', "column": None, "bit": "+{{ object.case.ref_id }}" })
        fields.append({"name": 'PB', "column": None, "bit": "{{ object.malnut_muac }}" })
#        fields.append({"name": 'SYMPTOMS', "column": None, "bit": "{{ object.symptoms }}" })
        fields.append({"name": 'Poids', "column": None, "bit": "{{ object.malnut_weight }}" })
        fields.append({"name": 'Oedemes', "column": None, "bit": "" })
        fields.append({"name": 'Dernier Depistage', "column": None, "bit": "{{ object.case.updated_at }}" })
        fields.append({"name": 'CONSULTER', "column": None, "bit": "[  ]" })
#        fields.append({"name": 'MOBILE', "column": None, "bit": "{{ object.mobile }}" })

        
        return qs, fields

#Fin Ajout new
