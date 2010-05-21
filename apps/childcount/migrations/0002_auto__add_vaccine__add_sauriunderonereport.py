# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding model 'Vaccine'
        db.create_table('cc_vaccine', (
            ('code', self.gf('django.db.models.fields.CharField')(unique=True, max_length=10)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal('childcount', ['Vaccine'])

        # Adding model 'SauriUnderOneReport'
        db.create_table('cc_sauri_uonerpt', (
            ('underonereport_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['childcount.UnderOneReport'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('childcount', ['SauriUnderOneReport'])

        # Adding M2M table for field vaccine on 'SauriUnderOneReport'
        db.create_table('cc_sauri_uonerpt_vaccine', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('sauriunderonereport', models.ForeignKey(orm['childcount.sauriunderonereport'], null=False)),
            ('vaccine', models.ForeignKey(orm['childcount.vaccine'], null=False))
        ))
        db.create_unique('cc_sauri_uonerpt_vaccine', ['sauriunderonereport_id', 'vaccine_id'])
    
    
    def backwards(self, orm):
        
        # Deleting model 'Vaccine'
        db.delete_table('cc_vaccine')

        # Deleting model 'SauriUnderOneReport'
        db.delete_table('cc_sauri_uonerpt')

        # Removing M2M table for field vaccine on 'SauriUnderOneReport'
        db.delete_table('cc_sauri_uonerpt_vaccine')
    
    
    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
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
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'childcount.bednetreport': {
            'Meta': {'object_name': 'BedNetReport', 'db_table': "'cc_bnrpt'", '_ormbases': ['childcount.CCReport']},
            'ccreport_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['childcount.CCReport']", 'unique': 'True', 'primary_key': 'True'}),
            'nets': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'sleeping_sites': ('django.db.models.fields.PositiveSmallIntegerField', [], {})
        },
        'childcount.birthreport': {
            'Meta': {'object_name': 'BirthReport', 'db_table': "'cc_birthrpt'", '_ormbases': ['childcount.CCReport']},
            'ccreport_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['childcount.CCReport']", 'unique': 'True', 'primary_key': 'True'}),
            'clinic_delivery': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'weight': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'})
        },
        'childcount.case': {
            'Meta': {'object_name': 'Case', 'db_table': "'cc_case'"},
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
        'childcount.chw': {
            'Meta': {'object_name': 'CHW', 'db_table': "'cc_chw'", '_ormbases': ['reporters.Reporter']},
            'clinic': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'stationed_chw'", 'null': 'True', 'to': "orm['childcount.Clinic']"}),
            'manager': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['childcount.CHW']", 'null': 'True', 'blank': 'True'}),
            'reporter_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['reporters.Reporter']", 'unique': 'True', 'primary_key': 'True'})
        },
        'childcount.clinic': {
            'Meta': {'object_name': 'Clinic', 'db_table': "'cc_clinic'", '_ormbases': ['locations.Location']},
            'location_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['locations.Location']", 'unique': 'True', 'primary_key': 'True'})
        },
        'childcount.codeditem': {
            'Meta': {'unique_together': "(('type', 'code'),)", 'object_name': 'CodedItem', 'db_table': "'cc_codeditem'"},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '2'})
        },
        'childcount.codeditemtranslation': {
            'Meta': {'unique_together': "(('coded_item', 'language'),)", 'object_name': 'CodedItemTranslation', 'db_table': "'cc_codeditemtrans'"},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'coded_item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['childcount.CodedItem']"}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '6'})
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
        'childcount.deathreport': {
            'Meta': {'object_name': 'DeathReport', 'db_table': "'cc_deathrpt'", '_ormbases': ['childcount.CCReport']},
            'ccreport_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['childcount.CCReport']", 'unique': 'True', 'primary_key': 'True'}),
            'death_date': ('django.db.models.fields.DateField', [], {})
        },
        'childcount.encounter': {
            'Meta': {'object_name': 'Encounter', 'db_table': "'cc_encounter'"},
            'chw': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['childcount.CHW']"}),
            'encounter_date': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'patient': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['childcount.Patient']"}),
            'sync_omrs': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '1'})
        },
        'childcount.familyplanningreport': {
            'Meta': {'object_name': 'FamilyPlanningReport', 'db_table': "'cc_fprpt'", '_ormbases': ['childcount.CCReport']},
            'ccreport_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['childcount.CCReport']", 'unique': 'True', 'primary_key': 'True'}),
            'women': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'women_using': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'})
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
            'rdt_result': ('django.db.models.fields.CharField', [], {'max_length': '1'})
        },
        'childcount.followupreport': {
            'Meta': {'object_name': 'FollowUpReport', 'db_table': "'cc_furpt'", '_ormbases': ['childcount.CCReport']},
            'ccreport_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['childcount.CCReport']", 'unique': 'True', 'primary_key': 'True'}),
            'improvement': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'visited_clinic': ('django.db.models.fields.CharField', [], {'max_length': '1'})
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
        'childcount.householdvisitreport': {
            'Meta': {'object_name': 'HouseholdVisitReport', 'db_table': "'cc_hhvisitrpt'", '_ormbases': ['childcount.CCReport']},
            'available': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'ccreport_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['childcount.CCReport']", 'unique': 'True', 'primary_key': 'True'}),
            'children': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'counseling': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['childcount.CodedItem']", 'blank': 'True'})
        },
        'childcount.medicinegivenreport': {
            'Meta': {'object_name': 'MedicineGivenReport', 'db_table': "'cc_medsrpt'", '_ormbases': ['childcount.CCReport']},
            'ccreport_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['childcount.CCReport']", 'unique': 'True', 'primary_key': 'True'}),
            'medicines': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['childcount.CodedItem']"})
        },
        'childcount.neonatalreport': {
            'Meta': {'object_name': 'NeonatalReport', 'db_table': "'cc_neorpt'", '_ormbases': ['childcount.CCReport']},
            'ccreport_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['childcount.CCReport']", 'unique': 'True', 'primary_key': 'True'}),
            'clinic_visits': ('django.db.models.fields.PositiveSmallIntegerField', [], {})
        },
        'childcount.nutritionreport': {
            'Meta': {'object_name': 'NutritionReport', 'db_table': "'cc_nutrpt'", '_ormbases': ['childcount.CCReport']},
            'ccreport_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['childcount.CCReport']", 'unique': 'True', 'primary_key': 'True'}),
            'muac': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'oedema': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'status': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'weight': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'})
        },
        'childcount.patient': {
            'Meta': {'object_name': 'Patient', 'db_table': "'cc_patient'"},
            'chw': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['childcount.CHW']"}),
            'clinic': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['childcount.Clinic']", 'null': 'True', 'blank': 'True'}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'dob': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'estimated_dob': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'health_id': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '6', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'household': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'household_member'", 'null': 'True', 'to': "orm['childcount.Patient']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'resident'", 'null': 'True', 'to': "orm['locations.Location']"}),
            'mobile': ('django.db.models.fields.CharField', [], {'max_length': '16', 'null': 'True', 'blank': 'True'}),
            'mother': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'child'", 'null': 'True', 'to': "orm['childcount.Patient']"}),
            'status': ('django.db.models.fields.SmallIntegerField', [], {'default': '1'}),
            'updated_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'childcount.pregnancyreport': {
            'Meta': {'object_name': 'PregnancyReport', 'db_table': "'cc_pregrpt'", '_ormbases': ['childcount.CCReport']},
            'anc_visits': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'ccreport_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['childcount.CCReport']", 'unique': 'True', 'primary_key': 'True'}),
            'pregnancy_month': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'weeks_since_anc': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'})
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
            'urgency': ('django.db.models.fields.CharField', [], {'max_length': '1'})
        },
        'childcount.sauriunderonereport': {
            'Meta': {'object_name': 'SauriUnderOneReport', 'db_table': "'cc_sauri_uonerpt'", '_ormbases': ['childcount.UnderOneReport']},
            'underonereport_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['childcount.UnderOneReport']", 'unique': 'True', 'primary_key': 'True'}),
            'vaccine': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['childcount.Vaccine']"})
        },
        'childcount.sickmembersreport': {
            'Meta': {'object_name': 'SickMembersReport', 'db_table': "'cc_sickrpt'", '_ormbases': ['childcount.CCReport']},
            'ccreport_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['childcount.CCReport']", 'unique': 'True', 'primary_key': 'True'}),
            'on_treatment': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'positive_rdts': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'rdts': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'sick': ('django.db.models.fields.PositiveSmallIntegerField', [], {})
        },
        'childcount.stillbirthmiscarriagereport': {
            'Meta': {'object_name': 'StillbirthMiscarriageReport', 'db_table': "'cc_sbmcrpt'", '_ormbases': ['childcount.CCReport']},
            'ccreport_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['childcount.CCReport']", 'unique': 'True', 'primary_key': 'True'}),
            'incident_date': ('django.db.models.fields.DateField', [], {})
        },
        'childcount.underonereport': {
            'Meta': {'object_name': 'UnderOneReport', 'db_table': "'cc_uonerpt'", '_ormbases': ['childcount.CCReport']},
            'breast_only': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'ccreport_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['childcount.CCReport']", 'unique': 'True', 'primary_key': 'True'}),
            'immunized': ('django.db.models.fields.CharField', [], {'max_length': '1'})
        },
        'childcount.vaccine': {
            'Meta': {'object_name': 'Vaccine', 'db_table': "'cc_vaccine'"},
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '10'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'childcount.verbalautopsyreport': {
            'Meta': {'object_name': 'VerbalAutopsyReport', 'db_table': "'cc_autopsyrpt'", '_ormbases': ['childcount.CCReport']},
            'ccreport_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['childcount.CCReport']", 'unique': 'True', 'primary_key': 'True'}),
            'done': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'})
        },
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'locations.location': {
            'Meta': {'object_name': 'Location'},
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
        'reporters.persistantbackend': {
            'Meta': {'object_name': 'PersistantBackend'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '30'})
        },
        'reporters.reporter': {
            'Meta': {'object_name': 'Reporter', '_ormbases': ['auth.User']},
            'language': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'reporters'", 'null': 'True', 'to': "orm['locations.Location']"}),
            'user_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True', 'primary_key': 'True'})
        }
    }
    
    complete_apps = ['childcount']
