# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'DeliveryToFirstCtrlLate'
        db.create_table('findtb_deliverytofirstctrllate', (
            ('collectedfromdtu_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['findtb.CollectedFromDtu'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('findtb', ['DeliveryToFirstCtrlLate'])


    def backwards(self, orm):
        
        # Deleting model 'DeliveryToFirstCtrlLate'
        db.delete_table('findtb_deliverytofirstctrllate')


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
        'findtb.deliverytofirstctrllate': {
            'Meta': {'object_name': 'DeliveryToFirstCtrlLate', '_ormbases': ['findtb.CollectedFromDtu']},
            'collectedfromdtu_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['findtb.CollectedFromDtu']", 'unique': 'True', 'primary_key': 'True'})
        },
        'findtb.dtucollectionislate': {
            'Meta': {'object_name': 'DtuCollectionIsLate', '_ormbases': ['findtb.EqaStarts']},
            'eqastarts_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['findtb.EqaStarts']", 'unique': 'True', 'primary_key': 'True'})
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
            'number': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '20', 'null': 'True', 'blank': 'True'}),
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
