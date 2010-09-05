# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Role'
        db.create_table('findtb_role', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.Group'])),
            ('reporter', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['reporters.Reporter'])),
            ('location', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['locations.Location'], null=True, blank=True)),
        ))
        db.send_create_signal('findtb', ['Role'])

        # Adding model 'Patient'
        db.create_table('findtb_patient', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('first_name', self.gf('django.db.models.fields.CharField')(default='', max_length=50, blank=True)),
            ('last_name', self.gf('django.db.models.fields.CharField')(default='', max_length=50, blank=True)),
            ('gender', self.gf('django.db.models.fields.CharField')(max_length=1, null=True, blank=True)),
            ('created_on', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('created_by', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['reporters.Reporter'])),
            ('location', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['locations.Location'])),
            ('registration_number', self.gf('django.db.models.fields.CharField')(max_length=25, db_index=True)),
            ('dob', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('estimated_dob', self.gf('django.db.models.fields.NullBooleanField')(default=True, null=True)),
            ('is_active', self.gf('django.db.models.fields.BooleanField')(default=True, blank=True)),
        ))
        db.send_create_signal('findtb', ['Patient'])

        # Adding unique constraint on 'Patient', fields ['registration_number', 'location']
        db.create_unique('findtb_patient', ['registration_number', 'location_id'])

        # Adding model 'Specimen'
        db.create_table('findtb_specimen', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('patient', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['findtb.Patient'])),
            ('location', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['locations.Location'])),
            ('created_on', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('created_by', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['reporters.Reporter'])),
            ('tracking_tag', self.gf('django.db.models.fields.CharField')(unique=True, max_length=8, db_index=True)),
            ('tc_number', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=12, unique=True, null=True, blank=True)),
        ))
        db.send_create_signal('findtb', ['Specimen'])

        # Adding model 'Configuration'
        db.create_table('findtb_configuration', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('key', self.gf('django.db.models.fields.CharField')(max_length=50, db_index=True)),
            ('value', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=255, blank=True)),
        ))
        db.send_create_signal('findtb', ['Configuration'])

        # Adding model 'SlidesBatch'
        db.create_table('findtb_slidesbatch', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('location', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['locations.Location'])),
            ('created_on', self.gf('django.db.models.fields.DateField')(default=datetime.date.today)),
            ('created_by', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['reporters.Reporter'], null=True, blank=True)),
            ('comment', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('results', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
        ))
        db.send_create_signal('findtb', ['SlidesBatch'])

        # Adding model 'Slide'
        db.create_table('findtb_slide', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('batch', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['findtb.SlidesBatch'])),
            ('number', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=20, unique=True, null=True, blank=True)),
            ('dtu_results', self.gf('django.db.models.fields.CharField')(max_length=10, blank=True)),
            ('first_ctrl_results', self.gf('django.db.models.fields.CharField')(max_length=10, blank=True)),
            ('second_ctrl_results', self.gf('django.db.models.fields.CharField')(max_length=10, blank=True)),
            ('cancelled', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
        ))
        db.send_create_signal('findtb', ['Slide'])

        # Adding model 'Notice'
        db.create_table('findtb_notice', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('location', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['locations.Location'], null=True, blank=True)),
            ('reporter', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['reporters.Reporter'], null=True, blank=True)),
            ('recieved_on', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('text', self.gf('django.db.models.fields.CharField')(max_length=450, null=True, blank=True)),
            ('response', self.gf('django.db.models.fields.CharField')(max_length=450, null=True, blank=True)),
            ('responded_on', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('responded_by', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='notice_response', null=True, to=orm['auth.User'])),
        ))
        db.send_create_signal('findtb', ['Notice'])

        # Adding model 'Sref'
        db.create_table('findtb_sref', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('note', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('specimen', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['findtb.Specimen'])),
        ))
        db.send_create_signal('findtb', ['Sref'])

        # Adding model 'SpecimenInvalid'
        db.create_table('findtb_specimeninvalid', (
            ('sref_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['findtb.Sref'], unique=True, primary_key=True)),
            ('cause', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('new_requested', self.gf('django.db.models.fields.BooleanField')(default=True, blank=True)),
        ))
        db.send_create_signal('findtb', ['SpecimenInvalid'])

        # Adding model 'SpecimenMustBeReplaced'
        db.create_table('findtb_specimenmustbereplaced', (
            ('sref_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['findtb.Sref'], unique=True, primary_key=True)),
            ('next_specimen', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['findtb.Specimen'], null=True, blank=True)),
        ))
        db.send_create_signal('findtb', ['SpecimenMustBeReplaced'])

        # Adding model 'SpecimenRegistered'
        db.create_table('findtb_specimenregistered', (
            ('sref_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['findtb.Sref'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('findtb', ['SpecimenRegistered'])

        # Adding model 'SpecimenSent'
        db.create_table('findtb_specimensent', (
            ('sref_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['findtb.Sref'], unique=True, primary_key=True)),
            ('sending_method', self.gf('django.db.models.fields.CharField')(max_length=20)),
        ))
        db.send_create_signal('findtb', ['SpecimenSent'])

        # Adding model 'SpecimenReceived'
        db.create_table('findtb_specimenreceived', (
            ('sref_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['findtb.Sref'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('findtb', ['SpecimenReceived'])

        # Adding model 'AllTestsDone'
        db.create_table('findtb_alltestsdone', (
            ('sref_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['findtb.Sref'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('findtb', ['AllTestsDone'])

        # Adding model 'Eqa'
        db.create_table('findtb_eqa', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('note', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('slides_batch', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['findtb.SlidesBatch'])),
        ))
        db.send_create_signal('findtb', ['Eqa'])

        # Adding model 'EqaStarts'
        db.create_table('findtb_eqastarts', (
            ('eqa_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['findtb.Eqa'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('findtb', ['EqaStarts'])

        # Adding model 'CollectedFromDtu'
        db.create_table('findtb_collectedfromdtu', (
            ('eqa_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['findtb.Eqa'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('findtb', ['CollectedFromDtu'])

        # Adding model 'DeliveredToFirstController'
        db.create_table('findtb_deliveredtofirstcontroller', (
            ('eqa_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['findtb.Eqa'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('findtb', ['DeliveredToFirstController'])

        # Adding model 'PassedFirstControl'
        db.create_table('findtb_passedfirstcontrol', (
            ('eqa_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['findtb.Eqa'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('findtb', ['PassedFirstControl'])

        # Adding model 'CollectedFromFirstController'
        db.create_table('findtb_collectedfromfirstcontroller', (
            ('eqa_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['findtb.Eqa'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('findtb', ['CollectedFromFirstController'])

        # Adding model 'DeliveredToSecondController'
        db.create_table('findtb_deliveredtosecondcontroller', (
            ('eqa_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['findtb.Eqa'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('findtb', ['DeliveredToSecondController'])

        # Adding model 'ResultsAvailable'
        db.create_table('findtb_resultsavailable', (
            ('eqa_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['findtb.Eqa'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('findtb', ['ResultsAvailable'])

        # Adding model 'ReadyToLeaveNtrl'
        db.create_table('findtb_readytoleaventrl', (
            ('eqa_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['findtb.Eqa'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('findtb', ['ReadyToLeaveNtrl'])

        # Adding model 'ReceivedAtDtu'
        db.create_table('findtb_receivedatdtu', (
            ('eqa_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['findtb.Eqa'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('findtb', ['ReceivedAtDtu'])

        # Adding model 'MicroscopyResult'
        db.create_table('findtb_microscopyresult', (
            ('sref_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['findtb.Sref'], unique=True, primary_key=True)),
            ('result', self.gf('django.db.models.fields.CharField')(max_length=10)),
        ))
        db.send_create_signal('findtb', ['MicroscopyResult'])

        # Adding model 'MgitResult'
        db.create_table('findtb_mgitresult', (
            ('sref_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['findtb.Sref'], unique=True, primary_key=True)),
            ('result', self.gf('django.db.models.fields.CharField')(max_length=10)),
        ))
        db.send_create_signal('findtb', ['MgitResult'])

        # Adding model 'LpaResult'
        db.create_table('findtb_lparesult', (
            ('sref_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['findtb.Sref'], unique=True, primary_key=True)),
            ('rif', self.gf('django.db.models.fields.CharField')(max_length=15)),
            ('inh', self.gf('django.db.models.fields.CharField')(max_length=15)),
        ))
        db.send_create_signal('findtb', ['LpaResult'])

        # Adding model 'LjResult'
        db.create_table('findtb_ljresult', (
            ('sref_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['findtb.Sref'], unique=True, primary_key=True)),
            ('result', self.gf('django.db.models.fields.CharField')(max_length=10)),
        ))
        db.send_create_signal('findtb', ['LjResult'])

        # Adding model 'SirezResult'
        db.create_table('findtb_sirezresult', (
            ('sref_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['findtb.Sref'], unique=True, primary_key=True)),
            ('rif', self.gf('django.db.models.fields.CharField')(max_length=15)),
            ('inh', self.gf('django.db.models.fields.CharField')(max_length=15)),
            ('str', self.gf('django.db.models.fields.CharField')(max_length=15)),
            ('emb', self.gf('django.db.models.fields.CharField')(max_length=15)),
            ('pza', self.gf('django.db.models.fields.CharField')(max_length=15)),
        ))
        db.send_create_signal('findtb', ['SirezResult'])


    def backwards(self, orm):
        
        # Deleting model 'Role'
        db.delete_table('findtb_role')

        # Deleting model 'Patient'
        db.delete_table('findtb_patient')

        # Removing unique constraint on 'Patient', fields ['registration_number', 'location']
        db.delete_unique('findtb_patient', ['registration_number', 'location_id'])

        # Deleting model 'Specimen'
        db.delete_table('findtb_specimen')

        # Deleting model 'Configuration'
        db.delete_table('findtb_configuration')

        # Deleting model 'SlidesBatch'
        db.delete_table('findtb_slidesbatch')

        # Deleting model 'Slide'
        db.delete_table('findtb_slide')

        # Deleting model 'Notice'
        db.delete_table('findtb_notice')

        # Deleting model 'Sref'
        db.delete_table('findtb_sref')

        # Deleting model 'SpecimenInvalid'
        db.delete_table('findtb_specimeninvalid')

        # Deleting model 'SpecimenMustBeReplaced'
        db.delete_table('findtb_specimenmustbereplaced')

        # Deleting model 'SpecimenRegistered'
        db.delete_table('findtb_specimenregistered')

        # Deleting model 'SpecimenSent'
        db.delete_table('findtb_specimensent')

        # Deleting model 'SpecimenReceived'
        db.delete_table('findtb_specimenreceived')

        # Deleting model 'AllTestsDone'
        db.delete_table('findtb_alltestsdone')

        # Deleting model 'Eqa'
        db.delete_table('findtb_eqa')

        # Deleting model 'EqaStarts'
        db.delete_table('findtb_eqastarts')

        # Deleting model 'CollectedFromDtu'
        db.delete_table('findtb_collectedfromdtu')

        # Deleting model 'DeliveredToFirstController'
        db.delete_table('findtb_deliveredtofirstcontroller')

        # Deleting model 'PassedFirstControl'
        db.delete_table('findtb_passedfirstcontrol')

        # Deleting model 'CollectedFromFirstController'
        db.delete_table('findtb_collectedfromfirstcontroller')

        # Deleting model 'DeliveredToSecondController'
        db.delete_table('findtb_deliveredtosecondcontroller')

        # Deleting model 'ResultsAvailable'
        db.delete_table('findtb_resultsavailable')

        # Deleting model 'ReadyToLeaveNtrl'
        db.delete_table('findtb_readytoleaventrl')

        # Deleting model 'ReceivedAtDtu'
        db.delete_table('findtb_receivedatdtu')

        # Deleting model 'MicroscopyResult'
        db.delete_table('findtb_microscopyresult')

        # Deleting model 'MgitResult'
        db.delete_table('findtb_mgitresult')

        # Deleting model 'LpaResult'
        db.delete_table('findtb_lparesult')

        # Deleting model 'LjResult'
        db.delete_table('findtb_ljresult')

        # Deleting model 'SirezResult'
        db.delete_table('findtb_sirezresult')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
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
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'django_tracking.state': {
            'Meta': {'object_name': 'State'},
            'cancelled': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_current': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_final': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'origin': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '60', 'blank': 'True'}),
            'tracked_item': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'states'", 'to': "orm['django_tracking.TrackedItem']"}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'})
        },
        'django_tracking.trackeditem': {
            'Meta': {'unique_together': "(('object_id', 'content_type'),)", 'object_name': 'TrackedItem'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        'findtb.alltestsdone': {
            'Meta': {'object_name': 'AllTestsDone', '_ormbases': ['findtb.Sref']},
            'sref_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['findtb.Sref']", 'unique': 'True', 'primary_key': 'True'})
        },
        'findtb.collectedfromdtu': {
            'Meta': {'object_name': 'CollectedFromDtu', '_ormbases': ['findtb.Eqa']},
            'eqa_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['findtb.Eqa']", 'unique': 'True', 'primary_key': 'True'})
        },
        'findtb.collectedfromfirstcontroller': {
            'Meta': {'object_name': 'CollectedFromFirstController', '_ormbases': ['findtb.Eqa']},
            'eqa_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['findtb.Eqa']", 'unique': 'True', 'primary_key': 'True'})
        },
        'findtb.configuration': {
            'Meta': {'object_name': 'Configuration'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '255', 'blank': 'True'})
        },
        'findtb.deliveredtofirstcontroller': {
            'Meta': {'object_name': 'DeliveredToFirstController', '_ormbases': ['findtb.Eqa']},
            'eqa_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['findtb.Eqa']", 'unique': 'True', 'primary_key': 'True'})
        },
        'findtb.deliveredtosecondcontroller': {
            'Meta': {'object_name': 'DeliveredToSecondController', '_ormbases': ['findtb.Eqa']},
            'eqa_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['findtb.Eqa']", 'unique': 'True', 'primary_key': 'True'})
        },
        'findtb.eqa': {
            'Meta': {'object_name': 'Eqa'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'note': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'slides_batch': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['findtb.SlidesBatch']"})
        },
        'findtb.eqastarts': {
            'Meta': {'object_name': 'EqaStarts', '_ormbases': ['findtb.Eqa']},
            'eqa_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['findtb.Eqa']", 'unique': 'True', 'primary_key': 'True'})
        },
        'findtb.ljresult': {
            'Meta': {'object_name': 'LjResult', '_ormbases': ['findtb.Sref']},
            'result': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'sref_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['findtb.Sref']", 'unique': 'True', 'primary_key': 'True'})
        },
        'findtb.lparesult': {
            'Meta': {'object_name': 'LpaResult', '_ormbases': ['findtb.Sref']},
            'inh': ('django.db.models.fields.CharField', [], {'max_length': '15'}),
            'rif': ('django.db.models.fields.CharField', [], {'max_length': '15'}),
            'sref_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['findtb.Sref']", 'unique': 'True', 'primary_key': 'True'})
        },
        'findtb.mgitresult': {
            'Meta': {'object_name': 'MgitResult', '_ormbases': ['findtb.Sref']},
            'result': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'sref_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['findtb.Sref']", 'unique': 'True', 'primary_key': 'True'})
        },
        'findtb.microscopyresult': {
            'Meta': {'object_name': 'MicroscopyResult', '_ormbases': ['findtb.Sref']},
            'result': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'sref_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['findtb.Sref']", 'unique': 'True', 'primary_key': 'True'})
        },
        'findtb.notice': {
            'Meta': {'object_name': 'Notice'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.Location']", 'null': 'True', 'blank': 'True'}),
            'recieved_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'reporter': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['reporters.Reporter']", 'null': 'True', 'blank': 'True'}),
            'responded_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'notice_response'", 'null': 'True', 'to': "orm['auth.User']"}),
            'responded_on': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'response': ('django.db.models.fields.CharField', [], {'max_length': '450', 'null': 'True', 'blank': 'True'}),
            'text': ('django.db.models.fields.CharField', [], {'max_length': '450', 'null': 'True', 'blank': 'True'})
        },
        'findtb.passedfirstcontrol': {
            'Meta': {'object_name': 'PassedFirstControl', '_ormbases': ['findtb.Eqa']},
            'eqa_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['findtb.Eqa']", 'unique': 'True', 'primary_key': 'True'})
        },
        'findtb.patient': {
            'Meta': {'unique_together': "(('registration_number', 'location'),)", 'object_name': 'Patient'},
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['reporters.Reporter']"}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'dob': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'estimated_dob': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '50', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '50', 'blank': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.Location']"}),
            'registration_number': ('django.db.models.fields.CharField', [], {'max_length': '25', 'db_index': 'True'})
        },
        'findtb.readytoleaventrl': {
            'Meta': {'object_name': 'ReadyToLeaveNtrl', '_ormbases': ['findtb.Eqa']},
            'eqa_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['findtb.Eqa']", 'unique': 'True', 'primary_key': 'True'})
        },
        'findtb.receivedatdtu': {
            'Meta': {'object_name': 'ReceivedAtDtu', '_ormbases': ['findtb.Eqa']},
            'eqa_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['findtb.Eqa']", 'unique': 'True', 'primary_key': 'True'})
        },
        'findtb.resultsavailable': {
            'Meta': {'object_name': 'ResultsAvailable', '_ormbases': ['findtb.Eqa']},
            'eqa_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['findtb.Eqa']", 'unique': 'True', 'primary_key': 'True'})
        },
        'findtb.role': {
            'Meta': {'object_name': 'Role'},
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.Location']", 'null': 'True', 'blank': 'True'}),
            'reporter': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['reporters.Reporter']"})
        },
        'findtb.sirezresult': {
            'Meta': {'object_name': 'SirezResult', '_ormbases': ['findtb.Sref']},
            'emb': ('django.db.models.fields.CharField', [], {'max_length': '15'}),
            'inh': ('django.db.models.fields.CharField', [], {'max_length': '15'}),
            'pza': ('django.db.models.fields.CharField', [], {'max_length': '15'}),
            'rif': ('django.db.models.fields.CharField', [], {'max_length': '15'}),
            'sref_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['findtb.Sref']", 'unique': 'True', 'primary_key': 'True'}),
            'str': ('django.db.models.fields.CharField', [], {'max_length': '15'})
        },
        'findtb.slide': {
            'Meta': {'object_name': 'Slide'},
            'batch': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['findtb.SlidesBatch']"}),
            'cancelled': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'dtu_results': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'first_ctrl_results': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '20', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'second_ctrl_results': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        },
        'findtb.slidesbatch': {
            'Meta': {'object_name': 'SlidesBatch'},
            'comment': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['reporters.Reporter']", 'null': 'True', 'blank': 'True'}),
            'created_on': ('django.db.models.fields.DateField', [], {'default': 'datetime.date.today'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.Location']"}),
            'results': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'})
        },
        'findtb.specimen': {
            'Meta': {'object_name': 'Specimen'},
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['reporters.Reporter']"}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.Location']"}),
            'patient': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['findtb.Patient']"}),
            'tc_number': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '12', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'tracking_tag': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '8', 'db_index': 'True'})
        },
        'findtb.specimeninvalid': {
            'Meta': {'object_name': 'SpecimenInvalid', '_ormbases': ['findtb.Sref']},
            'cause': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'new_requested': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'sref_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['findtb.Sref']", 'unique': 'True', 'primary_key': 'True'})
        },
        'findtb.specimenmustbereplaced': {
            'Meta': {'object_name': 'SpecimenMustBeReplaced', '_ormbases': ['findtb.Sref']},
            'next_specimen': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['findtb.Specimen']", 'null': 'True', 'blank': 'True'}),
            'sref_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['findtb.Sref']", 'unique': 'True', 'primary_key': 'True'})
        },
        'findtb.specimenreceived': {
            'Meta': {'object_name': 'SpecimenReceived', '_ormbases': ['findtb.Sref']},
            'sref_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['findtb.Sref']", 'unique': 'True', 'primary_key': 'True'})
        },
        'findtb.specimenregistered': {
            'Meta': {'object_name': 'SpecimenRegistered', '_ormbases': ['findtb.Sref']},
            'sref_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['findtb.Sref']", 'unique': 'True', 'primary_key': 'True'})
        },
        'findtb.specimensent': {
            'Meta': {'object_name': 'SpecimenSent', '_ormbases': ['findtb.Sref']},
            'sending_method': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'sref_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['findtb.Sref']", 'unique': 'True', 'primary_key': 'True'})
        },
        'findtb.sref': {
            'Meta': {'object_name': 'Sref'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'note': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'specimen': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['findtb.Specimen']"})
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
        'reporters.reporter': {
            'Meta': {'object_name': 'Reporter', '_ormbases': ['auth.User']},
            'language': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'reporters'", 'null': 'True', 'to': "orm['locations.Location']"}),
            'user_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True', 'primary_key': 'True'})
        }
    }

    complete_apps = ['findtb']
