# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        pass


    def backwards(self, orm):
        pass


    models = {
        'alerts.smsalertmodel': {
            'Meta': {'object_name': 'SmsAlertModel'},
            'cancelled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'outgoing_message': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['logger_ng.LoggedMessage']", 'null': 'True', 'blank': 'True'}),
            'reporter': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['reporters.Reporter']"}),
            'task_meta': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['djcelery.TaskMeta']", 'null': 'True', 'blank': 'True'})
        },
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'childcount.antenatalvisitreport': {
            'Meta': {'object_name': 'AntenatalVisitReport', 'db_table': "'cc_iavrpt'", '_ormbases': ['childcount.CCReport']},
            'ccreport_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['childcount.CCReport']", 'unique': 'True', 'primary_key': 'True'}),
            'expected_on': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'sms_alert': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['alerts.SmsAlertModel']", 'null': 'True', 'blank': 'True'})
        },
        'childcount.appointmentreport': {
            'Meta': {'object_name': 'AppointmentReport', 'db_table': "'cc_appointment'", '_ormbases': ['childcount.CCReport']},
            'appointment_date': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'ccreport_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['childcount.CCReport']", 'unique': 'True', 'primary_key': 'True'}),
            'closed_date': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'sms_alert': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['alerts.SmsAlertModel']", 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'db_index': 'True'}),
            'task_id': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        'childcount.bcpillreport': {
            'Meta': {'object_name': 'BCPillReport', 'db_table': "'cc_bcprpt'", '_ormbases': ['childcount.CCReport']},
            'ccreport_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['childcount.CCReport']", 'unique': 'True', 'primary_key': 'True'}),
            'pills': ('django.db.models.fields.PositiveSmallIntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'women': ('django.db.models.fields.PositiveSmallIntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'})
        },
        'childcount.bednetissuedreport': {
            'Meta': {'object_name': 'BednetIssuedReport', 'db_table': "'cc_bdnstc_rpt'", '_ormbases': ['childcount.CCReport']},
            'bednet_received': ('django.db.models.fields.PositiveSmallIntegerField', [], {'db_index': 'True'}),
            'ccreport_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['childcount.CCReport']", 'unique': 'True', 'primary_key': 'True'})
        },
        'childcount.bednetreport': {
            'Meta': {'object_name': 'BedNetReport', 'db_table': "'cc_bnrpt'", '_ormbases': ['childcount.CCReport']},
            'ccreport_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['childcount.CCReport']", 'unique': 'True', 'primary_key': 'True'}),
            'function_nets': ('django.db.models.fields.PositiveSmallIntegerField', [], {'db_index': 'True'}),
            'function_nets_observed': ('django.db.models.fields.PositiveSmallIntegerField', [], {'db_index': 'True'}),
            'sleeping_sites': ('django.db.models.fields.PositiveSmallIntegerField', [], {'db_index': 'True'})
        },
        'childcount.bednetstock': {
            'Meta': {'object_name': 'BednetStock', 'db_table': "'cc_bednetstock'"},
            'chw': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['childcount.CHW']"}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'end_point': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'distributionsite'", 'null': 'True', 'to': "orm['locations.Location']"}),
            'quantity': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'start_point': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'updated_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'childcount.bednetutilization': {
            'Meta': {'object_name': 'BednetUtilization', 'db_table': "'cc_bdnutil_rpt'", '_ormbases': ['childcount.CCReport']},
            'ccreport_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['childcount.CCReport']", 'unique': 'True', 'primary_key': 'True'}),
            'child_lastnite': ('django.db.models.fields.PositiveSmallIntegerField', [], {'db_index': 'True'}),
            'child_underfive': ('django.db.models.fields.PositiveSmallIntegerField', [], {'db_index': 'True'})
        },
        'childcount.bednetutilizationpregnancy': {
            'Meta': {'object_name': 'BednetUtilizationPregnancy', 'db_table': "'cc_bdnutilpreg_rpt'", '_ormbases': ['childcount.CCReport']},
            'ccreport_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['childcount.CCReport']", 'unique': 'True', 'primary_key': 'True'}),
            'slept_lastnite': ('django.db.models.fields.PositiveSmallIntegerField', [], {'db_index': 'True'}),
            'slept_underbednet': ('django.db.models.fields.PositiveSmallIntegerField', [], {'db_index': 'True'})
        },
        'childcount.birthreport': {
            'Meta': {'object_name': 'BirthReport', 'db_table': "'cc_birthrpt'", '_ormbases': ['childcount.CCReport']},
            'ccreport_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['childcount.CCReport']", 'unique': 'True', 'primary_key': 'True'}),
            'clinic_delivery': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_index': 'True'}),
            'weight': ('django.db.models.fields.FloatField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'})
        },
        'childcount.case': {
            'Meta': {'ordering': "('-created_on',)", 'object_name': 'Case', 'db_table': "'cc_case'"},
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'expires_on': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'patient': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['childcount.Patient']"}),
            'reports': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['childcount.CCReport']"}),
            'status': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'type': ('django.db.models.fields.SmallIntegerField', [], {}),
            'updated_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'childcount.ccreport': {
            'Meta': {'object_name': 'CCReport', 'db_table': "'cc_ccrpt'"},
            'encounter': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['childcount.Encounter']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'polymorphic_ctype': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'polymorphic_ccreport_set'", 'null': 'True', 'to': "orm['contenttypes.ContentType']"})
        },
        'childcount.cd4resultreport': {
            'Meta': {'object_name': 'CD4ResultReport', 'db_table': "'cc_cd4result'", '_ormbases': ['childcount.CCReport']},
            'ccreport_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['childcount.CCReport']", 'unique': 'True', 'primary_key': 'True'}),
            'cd4_count': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'})
        },
        'childcount.chw': {
            'Meta': {'ordering': "('first_name', 'last_name')", 'object_name': 'CHW', 'db_table': "'cc_chw'", '_ormbases': ['reporters.Reporter']},
            'clinic': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'stationed_chw'", 'null': 'True', 'to': "orm['childcount.Clinic']"}),
            'manager': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['childcount.CHW']", 'null': 'True', 'blank': 'True'}),
            'reporter_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['reporters.Reporter']", 'unique': 'True', 'primary_key': 'True'})
        },
        'childcount.chwhealthid': {
            'Meta': {'object_name': 'CHWHealthId', 'db_table': "'cc_chwhealthid'"},
            'chw': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['childcount.CHW']", 'null': 'True', 'blank': 'True'}),
            'health_id': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['childcount.HealthId']", 'unique': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'issued_on': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'used': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'childcount.clinic': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Clinic', 'db_table': "'cc_clinic'", '_ormbases': ['locations.Location']},
            'location_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['locations.Location']", 'unique': 'True', 'primary_key': 'True'})
        },
        'childcount.codeditem': {
            'Meta': {'ordering': "('type', 'code')", 'unique_together': "(('type', 'code'),)", 'object_name': 'CodedItem', 'db_table': "'cc_codeditem'"},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '10', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '2', 'db_index': 'True'})
        },
        'childcount.configuration': {
            'Meta': {'unique_together': "(('key', 'value'),)", 'object_name': 'Configuration', 'db_table': "'cc_config'"},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '255', 'blank': 'True'})
        },
        'childcount.dangersignsreport': {
            'Meta': {'object_name': 'DangerSignsReport', 'db_table': "'cc_dsrpt'", '_ormbases': ['childcount.CCReport']},
            'ccreport_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['childcount.CCReport']", 'unique': 'True', 'primary_key': 'True'}),
            'danger_signs': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['childcount.CodedItem']"})
        },
        'childcount.dbsresultreport': {
            'Meta': {'object_name': 'DBSResultReport', 'db_table': "'cc_dbsresult'", '_ormbases': ['childcount.CCReport']},
            'ccreport_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['childcount.CCReport']", 'unique': 'True', 'primary_key': 'True'}),
            'test_result': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'})
        },
        'childcount.deadperson': {
            'Meta': {'ordering': "('dod',)", 'object_name': 'DeadPerson', 'db_table': "'cc_dead_person'"},
            'chw': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['childcount.CHW']"}),
            'clinic': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['childcount.Clinic']", 'null': 'True', 'blank': 'True'}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'dob': ('django.db.models.fields.DateField', [], {}),
            'dod': ('django.db.models.fields.DateField', [], {}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'household': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'deads_household_member'", 'null': 'True', 'to': "orm['childcount.Patient']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'deads_resident'", 'null': 'True', 'to': "orm['locations.Location']"}),
            'mobile': ('django.db.models.fields.CharField', [], {'max_length': '16', 'null': 'True', 'blank': 'True'}),
            'updated_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'childcount.deathreport': {
            'Meta': {'object_name': 'DeathReport', 'db_table': "'cc_deathrpt'", '_ormbases': ['childcount.CCReport']},
            'ccreport_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['childcount.CCReport']", 'unique': 'True', 'primary_key': 'True'}),
            'death_date': ('django.db.models.fields.DateField', [], {'db_index': 'True'})
        },
        'childcount.distributionpoints': {
            'Meta': {'object_name': 'DistributionPoints', 'db_table': "'cc_distribution_points'"},
            'chw': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['childcount.CHW']", 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'chwdistributionsite'", 'null': 'True', 'to': "orm['locations.Location']"})
        },
        'childcount.drinkingwaterreport': {
            'Meta': {'object_name': 'DrinkingWaterReport', 'db_table': "'cc_drnkwater_rpt'", '_ormbases': ['childcount.CCReport']},
            'ccreport_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['childcount.CCReport']", 'unique': 'True', 'primary_key': 'True'}),
            'treat_water': ('django.db.models.fields.CharField', [], {'default': "'U'", 'max_length': '1', 'db_index': 'True'}),
            'treatment_method': ('django.db.models.fields.CharField', [], {'default': "'U'", 'max_length': '2', 'db_index': 'True', 'blank': 'True'}),
            'water_source': ('django.db.models.fields.CharField', [], {'max_length': '2', 'db_index': 'True'})
        },
        'childcount.encounter': {
            'Meta': {'object_name': 'Encounter', 'db_table': "'cc_encounter'"},
            'chw': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['childcount.CHW']"}),
            'encounter_date': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'patient': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['childcount.Patient']"}),
            'sync_omrs': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_index': 'True'})
        },
        'childcount.extendedbednetreport': {
            'Meta': {'object_name': 'ExtendedBedNetReport', 'db_table': "'cc_ebnrpt'", '_ormbases': ['childcount.BedNetReport']},
            'bednetreport_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['childcount.BedNetReport']", 'unique': 'True', 'primary_key': 'True'}),
            'people': ('django.db.models.fields.PositiveSmallIntegerField', [], {'db_index': 'True'})
        },
        'childcount.familyplanningreport': {
            'Meta': {'object_name': 'FamilyPlanningReport', 'db_table': "'cc_fprpt'", '_ormbases': ['childcount.CCReport']},
            'ccreport_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['childcount.CCReport']", 'unique': 'True', 'primary_key': 'True'}),
            'women': ('django.db.models.fields.PositiveSmallIntegerField', [], {'db_index': 'True'}),
            'women_using': ('django.db.models.fields.PositiveSmallIntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'})
        },
        'childcount.familyplanningusage': {
            'Meta': {'object_name': 'FamilyPlanningUsage', 'db_table': "'cc_fpusage'"},
            'count': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'fp_report': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['childcount.FamilyPlanningReport']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'method': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['childcount.CodedItem']"})
        },
        'childcount.feverreport': {
            'Meta': {'object_name': 'FeverReport', 'db_table': "'cc_fevrpt'", '_ormbases': ['childcount.CCReport']},
            'ccreport_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['childcount.CCReport']", 'unique': 'True', 'primary_key': 'True'}),
            'rdt_result': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_index': 'True'})
        },
        'childcount.followupreport': {
            'Meta': {'object_name': 'FollowUpReport', 'db_table': "'cc_furpt'", '_ormbases': ['childcount.CCReport']},
            'ccreport_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['childcount.CCReport']", 'unique': 'True', 'primary_key': 'True'}),
            'improvement': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_index': 'True'}),
            'visited_clinic': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_index': 'True'})
        },
        'childcount.formgroup': {
            'Meta': {'object_name': 'FormGroup', 'db_table': "'cc_frmgrp'"},
            'backend': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['reporters.PersistantBackend']"}),
            'encounter': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['childcount.Encounter']", 'null': 'True', 'blank': 'True'}),
            'entered_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'encounters_entered'", 'null': 'True', 'to': "orm['reporters.Reporter']"}),
            'entered_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'forms': ('django.db.models.fields.CharField', [], {'max_length': '150', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'childcount.healthid': {
            'Meta': {'object_name': 'HealthId', 'db_table': "'cc_healthid'"},
            'generated_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'health_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '10'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'issued_on': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'issued_to': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['childcount.Patient']", 'null': 'True', 'blank': 'True'}),
            'printed_on': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'revoked_on': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'G'", 'max_length': '1'})
        },
        'childcount.hivtestreport': {
            'Meta': {'object_name': 'HIVTestReport', 'db_table': "'cc_hivtest'", '_ormbases': ['childcount.CCReport']},
            'blood_drawn': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_index': 'True'}),
            'ccreport_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['childcount.CCReport']", 'unique': 'True', 'primary_key': 'True'}),
            'hiv': ('django.db.models.fields.CharField', [], {'max_length': '2', 'db_index': 'True'})
        },
        'childcount.householdvisitreport': {
            'Meta': {'object_name': 'HouseholdVisitReport', 'db_table': "'cc_hhvisitrpt'", '_ormbases': ['childcount.CCReport']},
            'available': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'ccreport_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['childcount.CCReport']", 'unique': 'True', 'primary_key': 'True'}),
            'children': ('django.db.models.fields.SmallIntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'counseling': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['childcount.CodedItem']", 'blank': 'True'})
        },
        'childcount.immunizationnotification': {
            'Meta': {'unique_together': "(('patient', 'immunization'),)", 'object_name': 'ImmunizationNotification', 'db_table': "'cc_immunnotif'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'immunization': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['childcount.ImmunizationSchedule']"}),
            'notified_on': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'notify_on': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'patient': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['childcount.Patient']"})
        },
        'childcount.immunizationschedule': {
            'Meta': {'object_name': 'ImmunizationSchedule', 'db_table': "'cc_immunsched'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'immunization': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'period': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'period_type': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        },
        'childcount.insurancenumberreport': {
            'Meta': {'object_name': 'InsuranceNumberReport', 'db_table': "'cc_insrpt'", '_ormbases': ['childcount.CCReport']},
            'ccreport_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['childcount.CCReport']", 'unique': 'True', 'primary_key': 'True'}),
            'insurance_no': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'})
        },
        'childcount.labreport': {
            'Meta': {'object_name': 'LabReport', 'db_table': "'cc_labreport'", '_ormbases': ['childcount.CCReport']},
            'ccreport_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['childcount.CCReport']", 'unique': 'True', 'primary_key': 'True'}),
            'lab_test': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['childcount.LabTest']"}),
            'progress_status': ('django.db.models.fields.CharField', [], {'default': "'NS'", 'max_length': '2'}),
            'results': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'sample_no': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'IC'", 'max_length': '4'})
        },
        'childcount.labtest': {
            'Meta': {'object_name': 'LabTest', 'db_table': "'cc_labtest'"},
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '10'}),
            'defined_results': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'omrs_conceptid': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'childcount.labtestresults': {
            'Meta': {'object_name': 'LabTestResults', 'db_table': "'cc_labtestresults'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'omrs_conceptid': ('django.db.models.fields.IntegerField', [], {'max_length': '15', 'null': 'True', 'blank': 'True'}),
            'ref_range': ('django.db.models.fields.CharField', [], {'max_length': '15', 'null': 'True', 'blank': 'True'}),
            'result_type': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'test': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['childcount.LabTest']"}),
            'units': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'})
        },
        'childcount.medicinegivenreport': {
            'Meta': {'object_name': 'MedicineGivenReport', 'db_table': "'cc_medsrpt'", '_ormbases': ['childcount.CCReport']},
            'ccreport_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['childcount.CCReport']", 'unique': 'True', 'primary_key': 'True'}),
            'medicines': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['childcount.CodedItem']"})
        },
        'childcount.neonatalreport': {
            'Meta': {'object_name': 'NeonatalReport', 'db_table': "'cc_neorpt'", '_ormbases': ['childcount.CCReport']},
            'ccreport_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['childcount.CCReport']", 'unique': 'True', 'primary_key': 'True'}),
            'clinic_visits': ('django.db.models.fields.PositiveSmallIntegerField', [], {'db_index': 'True'})
        },
        'childcount.nutritionreport': {
            'Meta': {'object_name': 'NutritionReport', 'db_table': "'cc_nutrpt'", '_ormbases': ['childcount.CCReport']},
            'ccreport_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['childcount.CCReport']", 'unique': 'True', 'primary_key': 'True'}),
            'muac': ('django.db.models.fields.SmallIntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'oedema': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_index': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'weight': ('django.db.models.fields.FloatField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'})
        },
        'childcount.patient': {
            'Meta': {'ordering': "('health_id',)", 'object_name': 'Patient', 'db_table': "'cc_patient'"},
            'chw': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['childcount.CHW']"}),
            'clinic': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['childcount.Clinic']", 'null': 'True', 'blank': 'True'}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'dob': ('django.db.models.fields.DateField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'elevation': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '8', 'decimal_places': '2', 'blank': 'True'}),
            'estimated_dob': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_index': 'True'}),
            'health_id': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '6', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'hiv_exposed': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'hiv_status': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'household': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'household_member'", 'null': 'True', 'to': "orm['childcount.Patient']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'latitude': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '8', 'decimal_places': '6', 'blank': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'resident'", 'null': 'True', 'to': "orm['locations.Location']"}),
            'longitude': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '8', 'decimal_places': '6', 'blank': 'True'}),
            'mobile': ('django.db.models.fields.CharField', [], {'max_length': '16', 'null': 'True', 'blank': 'True'}),
            'mother': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'child'", 'null': 'True', 'to': "orm['childcount.Patient']"}),
            'status': ('django.db.models.fields.SmallIntegerField', [], {'default': '1', 'db_index': 'True'}),
            'updated_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'childcount.patientstatusreport': {
            'Meta': {'object_name': 'PatientStatusReport', 'db_table': "'cc_patientstatus'", '_ormbases': ['childcount.CCReport']},
            'ccreport_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['childcount.CCReport']", 'unique': 'True', 'primary_key': 'True'}),
            'reason': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.SmallIntegerField', [], {'db_index': 'True'})
        },
        'childcount.poliocampaignreport': {
            'Meta': {'ordering': "('created_on',)", 'unique_together': "(('patient', 'phase'),)", 'object_name': 'PolioCampaignReport', 'db_table': "'cc_poliocampaign'"},
            'chw': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['childcount.CHW']"}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'patient': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['childcount.Patient']"}),
            'phase': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'updated_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'childcount.pregnancyregistrationreport': {
            'Meta': {'object_name': 'PregnancyRegistrationReport', 'db_table': "'cc_pregregrpt'", '_ormbases': ['childcount.CCReport']},
            'ccreport_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['childcount.CCReport']", 'unique': 'True', 'primary_key': 'True'}),
            'husband': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'husband'", 'null': 'True', 'to': "orm['childcount.Patient']"}),
            'married': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_index': 'True'}),
            'number_of_children': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'pregnancies': ('django.db.models.fields.PositiveSmallIntegerField', [], {'db_index': 'True'})
        },
        'childcount.pregnancyreport': {
            'Meta': {'object_name': 'PregnancyReport', 'db_table': "'cc_pregrpt'", '_ormbases': ['childcount.CCReport']},
            'anc_visits': ('django.db.models.fields.PositiveSmallIntegerField', [], {'db_index': 'True'}),
            'ccreport_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['childcount.CCReport']", 'unique': 'True', 'primary_key': 'True'}),
            'pregnancy_month': ('django.db.models.fields.PositiveSmallIntegerField', [], {'db_index': 'True'}),
            'weeks_since_anc': ('django.db.models.fields.PositiveSmallIntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'})
        },
        'childcount.referral': {
            'Meta': {'object_name': 'Referral', 'db_table': "'cc_referral'"},
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'expires_on': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'patient': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['childcount.Patient']"}),
            'ref_id': ('django.db.models.fields.CharField', [], {'max_length': '30', 'db_index': 'True'}),
            'reports': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['childcount.CCReport']"}),
            'status': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'updated_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'childcount.referralreport': {
            'Meta': {'object_name': 'ReferralReport', 'db_table': "'cc_refrpt'", '_ormbases': ['childcount.CCReport']},
            'ccreport_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['childcount.CCReport']", 'unique': 'True', 'primary_key': 'True'}),
            'urgency': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_index': 'True'})
        },
        'childcount.sanitationreport': {
            'Meta': {'object_name': 'SanitationReport', 'db_table': "'cc_sanitation_rpt'", '_ormbases': ['childcount.CCReport']},
            'ccreport_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['childcount.CCReport']", 'unique': 'True', 'primary_key': 'True'}),
            'share_toilet': ('django.db.models.fields.CharField', [], {'default': "'U'", 'max_length': '1', 'db_index': 'True'}),
            'toilet_lat': ('django.db.models.fields.CharField', [], {'max_length': '2', 'db_index': 'True'})
        },
        'childcount.schoolattendancereport': {
            'Meta': {'object_name': 'SchoolAttendanceReport', 'db_table': "'cc_schoolattendance'", '_ormbases': ['childcount.CCReport']},
            'attending_school': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'db_index': 'True'}),
            'attendschool_other': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'db_index': 'True'}),
            'ccreport_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['childcount.CCReport']", 'unique': 'True', 'primary_key': 'True'}),
            'household_pupil': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'db_index': 'True'}),
            'reason': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['childcount.CodedItem']"}),
            'school_type': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'db_index': 'True'})
        },
        'childcount.sickmembersreport': {
            'Meta': {'object_name': 'SickMembersReport', 'db_table': "'cc_sickrpt'", '_ormbases': ['childcount.CCReport']},
            'ccreport_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['childcount.CCReport']", 'unique': 'True', 'primary_key': 'True'}),
            'on_treatment': ('django.db.models.fields.PositiveSmallIntegerField', [], {'db_index': 'True'}),
            'positive_rdts': ('django.db.models.fields.PositiveSmallIntegerField', [], {'db_index': 'True'}),
            'rdts': ('django.db.models.fields.PositiveSmallIntegerField', [], {'db_index': 'True'}),
            'sick': ('django.db.models.fields.PositiveSmallIntegerField', [], {'db_index': 'True'})
        },
        'childcount.specimenreport': {
            'Meta': {'object_name': 'SpecimenReport', 'db_table': "'cc_specimenrpt'", '_ormbases': ['childcount.CCReport']},
            'blood_tubes': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'ccreport_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['childcount.CCReport']", 'unique': 'True', 'primary_key': 'True'}),
            'sputum_sample': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'stool_sample': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'urine_sample': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'})
        },
        'childcount.spregnancy': {
            'Meta': {'object_name': 'SPregnancy', 'db_table': "'cc_sauri_pregrpt'", '_ormbases': ['childcount.PregnancyReport']},
            'cd4_count': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'folic_suppliment': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_index': 'True'}),
            'iron_supplement': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_index': 'True'}),
            'pmtc_arv': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['childcount.CodedItem']", 'null': 'True', 'blank': 'True'}),
            'pregnancyreport_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['childcount.PregnancyReport']", 'unique': 'True', 'primary_key': 'True'}),
            'tested_hiv': ('django.db.models.fields.CharField', [], {'max_length': '2', 'db_index': 'True'})
        },
        'childcount.stillbirthmiscarriagereport': {
            'Meta': {'object_name': 'StillbirthMiscarriageReport', 'db_table': "'cc_sbmcrpt'", '_ormbases': ['childcount.CCReport']},
            'ccreport_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['childcount.CCReport']", 'unique': 'True', 'primary_key': 'True'}),
            'incident_date': ('django.db.models.fields.DateField', [], {'db_index': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '1', 'null': 'True', 'blank': 'True'})
        },
        'childcount.sunderone': {
            'Meta': {'object_name': 'SUnderOne', 'db_table': "'cc_sauri_uonerpt'", '_ormbases': ['childcount.UnderOneReport']},
            'underonereport_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['childcount.UnderOneReport']", 'unique': 'True', 'primary_key': 'True'}),
            'vaccine': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['childcount.Vaccine']"})
        },
        'childcount.underonereport': {
            'Meta': {'object_name': 'UnderOneReport', 'db_table': "'cc_uonerpt'", '_ormbases': ['childcount.CCReport']},
            'breast_only': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_index': 'True'}),
            'ccreport_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['childcount.CCReport']", 'unique': 'True', 'primary_key': 'True'}),
            'immunized': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_index': 'True'})
        },
        'childcount.vaccine': {
            'Meta': {'ordering': "('code',)", 'object_name': 'Vaccine', 'db_table': "'cc_vaccine'"},
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '10'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'childcount.verbalautopsyreport': {
            'Meta': {'object_name': 'VerbalAutopsyReport', 'db_table': "'cc_autopsyrpt'", '_ormbases': ['childcount.CCReport']},
            'ccreport_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['childcount.CCReport']", 'unique': 'True', 'primary_key': 'True'}),
            'done': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'djcelery.taskmeta': {
            'Meta': {'object_name': 'TaskMeta', 'db_table': "'celery_taskmeta'"},
            'date_done': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'result': ('picklefield.fields.PickledObjectField', [], {'default': 'None', 'null': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'PENDING'", 'max_length': '50'}),
            'task_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'traceback': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'})
        },
        'locations.location': {
            'Meta': {'ordering': "('code',)", 'object_name': 'Location'},
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'latitude': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '8', 'decimal_places': '6', 'blank': 'True'}),
            'longitude': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '8', 'decimal_places': '6', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'children'", 'null': 'True', 'to': "orm['locations.Location']"}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'locations'", 'null': 'True', 'to': "orm['locations.LocationType']"})
        },
        'locations.locationtype': {
            'Meta': {'object_name': 'LocationType'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'logger_ng.loggedmessage': {
            'Meta': {'ordering': "['-date', 'direction']", 'object_name': 'LoggedMessage'},
            'backend': ('django.db.models.fields.CharField', [], {'max_length': '75'}),
            'date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'direction': ('django.db.models.fields.CharField', [], {'default': "'O'", 'max_length': '1'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identity': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'reporter': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['reporters.Reporter']", 'null': 'True', 'blank': 'True'}),
            'response_to': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'response'", 'null': 'True', 'to': "orm['logger_ng.LoggedMessage']"}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {})
        },
        'reporters.persistantbackend': {
            'Meta': {'object_name': 'PersistantBackend'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '30'})
        },
        'reporters.reporter': {
            'Meta': {'ordering': "['last_name', 'first_name']", 'object_name': 'Reporter', '_ormbases': ['auth.User']},
            'language': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'reporters'", 'null': 'True', 'to': "orm['locations.Location']"}),
            'user_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True', 'primary_key': 'True'})
        }
    }

    complete_apps = ['childcount']
