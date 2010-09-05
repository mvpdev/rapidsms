# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting field 'State.is_current_state'
        db.delete_column('django_tracking_state', 'is_current_state')

        # Deleting field 'State.final'
        db.delete_column('django_tracking_state', 'final')

        # Adding field 'State.title'
        db.add_column('django_tracking_state', 'title', self.gf('django.db.models.fields.CharField')(default='', max_length=60, blank=True), keep_default=False)

        # Adding field 'State.origin'
        db.add_column('django_tracking_state', 'origin', self.gf('django.db.models.fields.CharField')(default='', max_length=30, blank=True), keep_default=False)

        # Adding field 'State.is_final'
        db.add_column('django_tracking_state', 'is_final', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True), keep_default=False)

        # Adding field 'State.is_current'
        db.add_column('django_tracking_state', 'is_current', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True), keep_default=False)

        # Deleting field 'TrackedItem.current_state'
        db.delete_column('django_tracking_trackeditem', 'current_state_id')


    def backwards(self, orm):
        
        # Adding field 'State.is_current_state'
        db.add_column('django_tracking_state', 'is_current_state', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True), keep_default=False)

        # Adding field 'State.final'
        db.add_column('django_tracking_state', 'final', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True), keep_default=False)

        # Deleting field 'State.title'
        db.delete_column('django_tracking_state', 'title')

        # Deleting field 'State.origin'
        db.delete_column('django_tracking_state', 'origin')

        # Deleting field 'State.is_final'
        db.delete_column('django_tracking_state', 'is_final')

        # Deleting field 'State.is_current'
        db.delete_column('django_tracking_state', 'is_current')

        # Adding field 'TrackedItem.current_state'
        db.add_column('django_tracking_trackeditem', 'current_state', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['django_tracking.State'], null=True, blank=True), keep_default=False)


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
        }
    }

    complete_apps = ['django_tracking']
