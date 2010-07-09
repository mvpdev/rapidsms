# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'State'
        db.create_table('django_tracking_state', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('cancelled', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('final', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('is_current_state', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('tracked_item', self.gf('django.db.models.fields.related.ForeignKey')(related_name='states', to=orm['django_tracking.TrackedItem'])),
        ))
        db.send_create_signal('django_tracking', ['State'])

        # Adding model 'TrackedItem'
        db.create_table('django_tracking_trackeditem', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('current_state', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['django_tracking.State'], null=True, blank=True)),
        ))
        db.send_create_signal('django_tracking', ['TrackedItem'])

        # Adding unique constraint on 'TrackedItem', fields ['object_id', 'content_type']
        db.create_unique('django_tracking_trackeditem', ['object_id', 'content_type_id'])


    def backwards(self, orm):
        
        # Deleting model 'State'
        db.delete_table('django_tracking_state')

        # Deleting model 'TrackedItem'
        db.delete_table('django_tracking_trackeditem')

        # Removing unique constraint on 'TrackedItem', fields ['object_id', 'content_type']
        db.delete_unique('django_tracking_trackeditem', ['object_id', 'content_type_id'])


    models = {
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
            'final': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_current_state': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'tracked_item': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'states'", 'to': "orm['django_tracking.TrackedItem']"}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'})
        },
        'django_tracking.trackeditem': {
            'Meta': {'unique_together': "(('object_id', 'content_type'),)", 'object_name': 'TrackedItem'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'current_state': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['django_tracking.State']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {})
        }
    }

    complete_apps = ['django_tracking']
