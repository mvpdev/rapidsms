from datetime import datetime

from childcount.forms import CCForm
from childcount.models import Encounter
from childcount.models.reports import NutritionReport


class MigrationForm(CCForm):
    KEYWORDS = {
        'en': ['migrate'],
    }
    ENCOUNTER_TYPE = Encounter.TYPE_PATIENT

    def process(self, patient):
        if self.params[1].lower() == "patient":
            #pick estimated_dob status created_at
            if len(self.params[2:]) >= 3:
                if self.params[2].isdigit():
                    patient.estimated_dob = bool(int(self.params[2]))
                patient.status = int(self.params[3])
                created_on = self.params[4].upper().replace('T', ' ')
                created_on = datetime.strptime(created_on,"%Y-%m-%d %H:%M:%S")
                patient.created_on = created_on
                patient.save()
        if self.params[1].lower() == "muac":
            #pick status created_at
            if len(self.params[2:]) >= 2:
                created_on = self.params[3].upper().replace('T', ' ')
                created_on = datetime.strptime(created_on,"%Y-%m-%d %H:%M:%S")
                status = int(self.params[2])
                nr = NutritionReport.objects.filter(encounter=self.encounter)[0];
                nr.status = status
                nr.save()
                dir(self.encounter)
                self.encounter.encounter_date = created_on
                self.encounter.save()
