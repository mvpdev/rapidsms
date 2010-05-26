# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding model 'Configuration'
        db.create_table('cc_config', (
            ('value', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=255, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('key', self.gf('django.db.models.fields.CharField')(max_length=50, db_index=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
        ))
        db.send_create_signal('childcount', ['Configuration'])

        # Adding unique constraint on 'Configuration', fields ['key', 'value']
        db.create_unique('cc_config', ['key', 'value'])

        # Adding model 'Clinic'
        db.create_table('cc_clinic', (
            ('location_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['locations.Location'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('childcount', ['Clinic'])

        # Adding model 'CHW'
        db.create_table('cc_chw', (
            ('manager', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['childcount.CHW'], null=True, blank=True)),
            ('reporter_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['reporters.Reporter'], unique=True, primary_key=True)),
            ('clinic', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='stationed_chw', null=True, to=orm['childcount.Clinic'])),
        ))
        db.send_create_signal('childcount', ['CHW'])

        # Adding model 'Patient'
        db.create_table('cc_patient', (
            ('status', self.gf('django.db.models.fields.SmallIntegerField')(default=1)),
            ('chw', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['childcount.CHW'])),
            ('first_name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('last_name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('dob', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('gender', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('household', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='household_member', null=True, to=orm['childcount.Patient'])),
            ('mother', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='child', null=True, to=orm['childcount.Patient'])),
            ('clinic', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['childcount.Clinic'], null=True, blank=True)),
            ('mobile', self.gf('django.db.models.fields.CharField')(max_length=16, null=True, blank=True)),
            ('created_on', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('location', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='resident', null=True, to=orm['locations.Location'])),
            ('estimated_dob', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('updated_on', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('health_id', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=6, unique=True, null=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('childcount', ['Patient'])

        # Adding model 'Encounter'
        db.create_table('cc_encounter', (
            ('sync_omrs', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('patient', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['childcount.Patient'])),
            ('encounter_date', self.gf('django.db.models.fields.DateTimeField')()),
            ('chw', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['childcount.CHW'])),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('childcount', ['Encounter'])

        # Adding model 'FormGroup'
        db.create_table('cc_frmgrp', (
            ('entered_on', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('entered_by', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='encounters_entered', null=True, to=orm['reporters.Reporter'])),
            ('forms', self.gf('django.db.models.fields.CharField')(max_length=150, null=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('encounter', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['childcount.Encounter'], null=True, blank=True)),
            ('backend', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['reporters.PersistantBackend'])),
        ))
        db.send_create_signal('childcount', ['FormGroup'])

        # Adding model 'CodedItem'
        db.create_table('cc_codeditem', (
            ('code', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=2)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal('childcount', ['CodedItem'])

        # Adding unique constraint on 'CodedItem', fields ['type', 'code']
        db.create_unique('cc_codeditem', ['type', 'code'])

        # Adding model 'CodedItemTranslation'
        db.create_table('cc_codeditemtrans', (
            ('code', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('coded_item', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['childcount.CodedItem'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('language', self.gf('django.db.models.fields.CharField')(max_length=6)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal('childcount', ['CodedItemTranslation'])

        # Adding unique constraint on 'CodedItemTranslation', fields ['coded_item', 'language']
        db.create_unique('cc_codeditemtrans', ['coded_item_id', 'language'])

        # Adding model 'CCReport'
        db.create_table('cc_ccrpt', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('encounter', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['childcount.Encounter'])),
            ('polymorphic_ctype', self.gf('django.db.models.fields.related.ForeignKey')(related_name='polymorphic_ccreport_set', null=True, to=orm['contenttypes.ContentType'])),
        ))
        db.send_create_signal('childcount', ['CCReport'])

        # Adding model 'BirthReport'
        db.create_table('cc_birthrpt', (
            ('ccreport_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['childcount.CCReport'], unique=True, primary_key=True)),
            ('clinic_delivery', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('weight', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
        ))
        db.send_create_signal('childcount', ['BirthReport'])

        # Adding model 'DeathReport'
        db.create_table('cc_deathrpt', (
            ('ccreport_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['childcount.CCReport'], unique=True, primary_key=True)),
            ('death_date', self.gf('django.db.models.fields.DateField')()),
        ))
        db.send_create_signal('childcount', ['DeathReport'])

        # Adding model 'StillbirthMiscarriageReport'
        db.create_table('cc_sbmcrpt', (
            ('incident_date', self.gf('django.db.models.fields.DateField')()),
            ('ccreport_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['childcount.CCReport'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('childcount', ['StillbirthMiscarriageReport'])

        # Adding model 'FollowUpReport'
        db.create_table('cc_furpt', (
            ('ccreport_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['childcount.CCReport'], unique=True, primary_key=True)),
            ('visited_clinic', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('improvement', self.gf('django.db.models.fields.CharField')(max_length=1)),
        ))
        db.send_create_signal('childcount', ['FollowUpReport'])

        # Adding model 'DangerSignsReport'
        db.create_table('cc_dsrpt', (
            ('ccreport_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['childcount.CCReport'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('childcount', ['DangerSignsReport'])

        # Adding M2M table for field danger_signs on 'DangerSignsReport'
        db.create_table('cc_dsrpt_danger_signs', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('dangersignsreport', models.ForeignKey(orm['childcount.dangersignsreport'], null=False)),
            ('codeditem', models.ForeignKey(orm['childcount.codeditem'], null=False))
        ))
        db.create_unique('cc_dsrpt_danger_signs', ['dangersignsreport_id', 'codeditem_id'])

        # Adding model 'PregnancyReport'
        db.create_table('cc_pregrpt', (
            ('pregnancy_month', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
            ('weeks_since_anc', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True, blank=True)),
            ('ccreport_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['childcount.CCReport'], unique=True, primary_key=True)),
            ('anc_visits', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
        ))
        db.send_create_signal('childcount', ['PregnancyReport'])

        # Adding model 'NeonatalReport'
        db.create_table('cc_neorpt', (
            ('ccreport_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['childcount.CCReport'], unique=True, primary_key=True)),
            ('clinic_visits', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
        ))
        db.send_create_signal('childcount', ['NeonatalReport'])

        # Adding model 'UnderOneReport'
        db.create_table('cc_uonerpt', (
            ('immunized', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('ccreport_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['childcount.CCReport'], unique=True, primary_key=True)),
            ('breast_only', self.gf('django.db.models.fields.CharField')(max_length=1)),
        ))
        db.send_create_signal('childcount', ['UnderOneReport'])

        # Adding model 'NutritionReport'
        db.create_table('cc_nutrpt', (
            ('status', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('muac', self.gf('django.db.models.fields.SmallIntegerField')(null=True, blank=True)),
            ('ccreport_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['childcount.CCReport'], unique=True, primary_key=True)),
            ('oedema', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('weight', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
        ))
        db.send_create_signal('childcount', ['NutritionReport'])

        # Adding model 'FeverReport'
        db.create_table('cc_fevrpt', (
            ('ccreport_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['childcount.CCReport'], unique=True, primary_key=True)),
            ('rdt_result', self.gf('django.db.models.fields.CharField')(max_length=1)),
        ))
        db.send_create_signal('childcount', ['FeverReport'])

        # Adding model 'MedicineGivenReport'
        db.create_table('cc_medsrpt', (
            ('ccreport_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['childcount.CCReport'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('childcount', ['MedicineGivenReport'])

        # Adding M2M table for field medicines on 'MedicineGivenReport'
        db.create_table('cc_medsrpt_medicines', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('medicinegivenreport', models.ForeignKey(orm['childcount.medicinegivenreport'], null=False)),
            ('codeditem', models.ForeignKey(orm['childcount.codeditem'], null=False))
        ))
        db.create_unique('cc_medsrpt_medicines', ['medicinegivenreport_id', 'codeditem_id'])

        # Adding model 'ReferralReport'
        db.create_table('cc_refrpt', (
            ('ccreport_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['childcount.CCReport'], unique=True, primary_key=True)),
            ('urgency', self.gf('django.db.models.fields.CharField')(max_length=1)),
        ))
        db.send_create_signal('childcount', ['ReferralReport'])

        # Adding model 'HouseholdVisitReport'
        db.create_table('cc_hhvisitrpt', (
            ('available', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('ccreport_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['childcount.CCReport'], unique=True, primary_key=True)),
            ('children', self.gf('django.db.models.fields.SmallIntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal('childcount', ['HouseholdVisitReport'])

        # Adding M2M table for field counseling on 'HouseholdVisitReport'
        db.create_table('cc_hhvisitrpt_counseling', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('householdvisitreport', models.ForeignKey(orm['childcount.householdvisitreport'], null=False)),
            ('codeditem', models.ForeignKey(orm['childcount.codeditem'], null=False))
        ))
        db.create_unique('cc_hhvisitrpt_counseling', ['householdvisitreport_id', 'codeditem_id'])

        # Adding model 'FamilyPlanningReport'
        db.create_table('cc_fprpt', (
            ('ccreport_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['childcount.CCReport'], unique=True, primary_key=True)),
            ('women_using', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True, blank=True)),
            ('women', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
        ))
        db.send_create_signal('childcount', ['FamilyPlanningReport'])

        # Adding model 'BedNetReport'
        db.create_table('cc_bnrpt', (
            ('sleeping_sites', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
            ('ccreport_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['childcount.CCReport'], unique=True, primary_key=True)),
            ('nets', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
        ))
        db.send_create_signal('childcount', ['BedNetReport'])

        # Adding model 'SickMembersReport'
        db.create_table('cc_sickrpt', (
            ('rdts', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
            ('on_treatment', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
            ('ccreport_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['childcount.CCReport'], unique=True, primary_key=True)),
            ('positive_rdts', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
            ('sick', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
        ))
        db.send_create_signal('childcount', ['SickMembersReport'])

        # Adding model 'VerbalAutopsyReport'
        db.create_table('cc_autopsyrpt', (
            ('ccreport_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['childcount.CCReport'], unique=True, primary_key=True)),
            ('done', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
        ))
        db.send_create_signal('childcount', ['VerbalAutopsyReport'])

        # Adding model 'Referral'
        db.create_table('cc_referral', (
            ('status', self.gf('django.db.models.fields.SmallIntegerField')(default=0)),
            ('patient', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['childcount.Patient'])),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('ref_id', self.gf('django.db.models.fields.CharField')(max_length=30, db_index=True)),
            ('created_on', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated_on', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('expires_on', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal('childcount', ['Referral'])

        # Adding M2M table for field reports on 'Referral'
        db.create_table('cc_referral_reports', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('referral', models.ForeignKey(orm['childcount.referral'], null=False)),
            ('ccreport', models.ForeignKey(orm['childcount.ccreport'], null=False))
        ))
        db.create_unique('cc_referral_reports', ['referral_id', 'ccreport_id'])

        # Adding model 'FamilyPlanningUsage'
        db.create_table('cc_fpusage', (
            ('count', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('fp_report', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['childcount.FamilyPlanningReport'])),
            ('method', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['childcount.CodedItem'])),
        ))
        db.send_create_signal('childcount', ['FamilyPlanningUsage'])

        # Adding model 'Case'
        db.create_table('cc_case', (
            ('status', self.gf('django.db.models.fields.SmallIntegerField')(default=0)),
            ('patient', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['childcount.Patient'])),
            ('created_on', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated_on', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('type', self.gf('django.db.models.fields.SmallIntegerField')()),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('expires_on', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal('childcount', ['Case'])

        # Adding M2M table for field reports on 'Case'
        db.create_table('cc_case_reports', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('case', models.ForeignKey(orm['childcount.case'], null=False)),
            ('ccreport', models.ForeignKey(orm['childcount.ccreport'], null=False))
        ))
        db.create_unique('cc_case_reports', ['case_id', 'ccreport_id'])
    
    
    def backwards(self, orm):
        
        # Deleting model 'Configuration'
        db.delete_table('cc_config')

        # Removing unique constraint on 'Configuration', fields ['key', 'value']
        db.delete_unique('cc_config', ['key', 'value'])

        # Deleting model 'Clinic'
        db.delete_table('cc_clinic')

        # Deleting model 'CHW'
        db.delete_table('cc_chw')

        # Deleting model 'Patient'
        db.delete_table('cc_patient')

        # Deleting model 'Encounter'
        db.delete_table('cc_encounter')

        # Deleting model 'FormGroup'
        db.delete_table('cc_frmgrp')

        # Deleting model 'CodedItem'
        db.delete_table('cc_codeditem')

        # Removing unique constraint on 'CodedItem', fields ['type', 'code']
        db.delete_unique('cc_codeditem', ['type', 'code'])

        # Deleting model 'CodedItemTranslation'
        db.delete_table('cc_codeditemtrans')

        # Removing unique constraint on 'CodedItemTranslation', fields ['coded_item', 'language']
        db.delete_unique('cc_codeditemtrans', ['coded_item_id', 'language'])

        # Deleting model 'CCReport'
        db.delete_table('cc_ccrpt')

        # Deleting model 'BirthReport'
        db.delete_table('cc_birthrpt')

        # Deleting model 'DeathReport'
        db.delete_table('cc_deathrpt')

        # Deleting model 'StillbirthMiscarriageReport'
        db.delete_table('cc_sbmcrpt')

        # Deleting model 'FollowUpReport'
        db.delete_table('cc_furpt')

        # Deleting model 'DangerSignsReport'
        db.delete_table('cc_dsrpt')

        # Removing M2M table for field danger_signs on 'DangerSignsReport'
        db.delete_table('cc_dsrpt_danger_signs')

        # Deleting model 'PregnancyReport'
        db.delete_table('cc_pregrpt')

        # Deleting model 'NeonatalReport'
        db.delete_table('cc_neorpt')

        # Deleting model 'UnderOneReport'
        db.delete_table('cc_uonerpt')

        # Deleting model 'NutritionReport'
        db.delete_table('cc_nutrpt')

        # Deleting model 'FeverReport'
        db.delete_table('cc_fevrpt')

        # Deleting model 'MedicineGivenReport'
        db.delete_table('cc_medsrpt')

        # Removing M2M table for field medicines on 'MedicineGivenReport'
        db.delete_table('cc_medsrpt_medicines')

        # Deleting model 'ReferralReport'
        db.delete_table('cc_refrpt')

        # Deleting model 'HouseholdVisitReport'
        db.delete_table('cc_hhvisitrpt')

        # Removing M2M table for field counseling on 'HouseholdVisitReport'
        db.delete_table('cc_hhvisitrpt_counseling')

        # Deleting model 'FamilyPlanningReport'
        db.delete_table('cc_fprpt')

        # Deleting model 'BedNetReport'
        db.delete_table('cc_bnrpt')

        # Deleting model 'SickMembersReport'
        db.delete_table('cc_sickrpt')

        # Deleting model 'VerbalAutopsyReport'
        db.delete_table('cc_autopsyrpt')

        # Deleting model 'Referral'
        db.delete_table('cc_referral')

        # Removing M2M table for field reports on 'Referral'
        db.delete_table('cc_referral_reports')

        # Deleting model 'FamilyPlanningUsage'
        db.delete_table('cc_fpusage')

        # Deleting model 'Case'
        db.delete_table('cc_case')

        # Removing M2M table for field reports on 'Case'
        db.delete_table('cc_case_reports')
    
    
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
