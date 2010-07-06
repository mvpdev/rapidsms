#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin


from django import forms
from django.forms.models import modelformset_factory
from django.forms import ValidationError
from django.db import IntegrityError

from django_tracking.models import State, TrackedItem

from findtb.models import SpecimenMustBeReplaced, AllTestsDone,\
                          MicroscopyResult, LpaResult, MgitResult,\
                          LjResult, SirezResult, Slide
from findtb.libs.utils import send_to_dtu, dtls_is_lab_tech_at, send_to_dtls

from forms import SlidesBatchForm


"""
Forms setting states for a testing results
"""


class EqaResultsForm(forms.Form):
    """
    Use to enter all the test results for EQA then calculate the error 
    rates.
    """
    

    class Media:
        js = ('/static/findtb/js/eqa_results.js',)


    def __init__(self, slides_batch, *args, **kwargs):
        
        super(EqaResultsForm, self).__init__(*args, **kwargs)
        
        self.slides_batch = slides_batch

        self.slides_batch_form = SlidesBatchForm(instance=self.slides_batch,
                                                  *args, **kwargs)
                                                  
        SlideFormSet = modelformset_factory(Slide, exclude=('batch',), extra=0)
        self.slide_form_set = SlideFormSet(queryset=self.slides_batch.slide_set.all(),
                                           *args, **kwargs)

        for form in self.slide_form_set.forms:
            form.fields['number'].widget.attrs['size'] = 8   
            
    
    def clean(self):    
        """
            Avoid duplicate numbers
        """
        
        existing_numbers = set()
        for name, value in self.slide_form_set.data.iteritems():
        
            if 'number' in name and value:
                
                if value in existing_numbers:
                    raise ValidationError("The number '%s' is used twice" % value)
                
                if not self.slides_batch.slide_set.filter(number=value).count() \
                   and Slide.objects.filter(number=value).count():
                    
                    raise ValidationError("The number '%s' is already used by another slide" % value)
                 
                existing_numbers.add(value)    
                
        
    def is_valid(self):
        """
        Validation is made on the slides batch form and all the slides form.
        """
        
        # we don't want do use django validatin
        self.slides_batch_form.is_valid()
        self.slide_form_set.is_valid()
        return super(EqaResultsForm, self).is_valid()        


    def save(self, *args, **kwargs):
        """
        Save form data into db.
        If the entire form is filled, calculate results and change the slides
        batch state.
        """

        self.slides_batch_form.save(*args, **kwargs)
        self.slide_form_set.save(*args, **kwargs)

        # calculate all results
        if self.is_filled():
        
            result_table = self.result_table()
            results = {}
            
            for slide in self.slides_batch.slide_set.filter(cancelled=False):
                result = result_table[slide.dtu_results][slide.second_ctrl_results]
                results[result] = results.get(result, 0) + 1
                    
            res = ', '.join("%s: %s" % (x, y) in results.iteritems())
            self.slides_batch.results = res
            self.slides_batch.save()
            
            state = ResultsAvailable(slide_batch=self.slides_batch)
            #state.save()
            ti, c = TrackedItem.get_tracker_or_create(content_object=self.slides_batch)
            ti.state = state
            #ti.save()
            
            send_to_ztls(self.slides_batch.location,
                        "EQA results for %(dtu)s are: %(results)s" % {
                        'dtu': self.slides_batch.location, 'results': res
                        } )
                        
            send_to_dtls(self.slides_batch.location,
                        "EQA results for %(dtu)s are: %(results)s" % {
                        'dtu': self.slides_batch.location, 'results': res
                        } )
            
            send_to_dtu_focal_person(self.slides_batch.location,
                        "EQA results are: %(results)s" % {'results': res } )
            
        
    def is_filled(self):
        """
        Check manually if all the necessary fields have been filled.
        Since they are not mandatory in the datebase.
        """
       
        for name, value in self.slide_form_set.data.iteritems():
        
            if 'comment' in name:
                continue
                
            if not value:
                id_ = name.split('-')[1]
                cancelled = "form-%s-cancelled" % id_
                if not self.data.get(cancelled, None):
                    return False
                    
        return True
       
                
    def result_table(self, _table={}):
        """
            Generate the result table of get it out of cache if it
            exists.
            First colum is DTU result, second column is Second Controller 
            result.
        """
    
        if not _table:
            
            afbs = tuple('%s_afb' % x for x in range(1, 20))
            
            _table['negative'] = {'negative': 'Correct', 
                                  '1': 'HFN', '2': 'HFN', '3': 'HFN'}
            _table['negative'].update(dict(((afb, 'LFN') for afb in afbs)))
            
            for afb in afbs:
                _table['afb'] = {'negative': 'LFP', '1': 'Correct',
                                 '2': 'QE', '3': 'QE'}
                _table['afb'].update(dict(((afb, 'Correct') for afb in afbs)))
                
            _table['1'] = {'negative': 'HPF', 
                           '1': 'Correct', '2': 'Correct', '3': 'QE'}
            _table['1'].update(dict(((afb, 'Correct') for afb in afbs)))
            
            _table['2'] = {'negative': 'HFP', 
                           '1': 'Correct', '2': 'Correct', '3': 'Correct'}
            _table['2'].update(dict(((afb, 'QE') for afb in afbs)))
            
            _table['3'] = {'negative': 'HFP', 
                            '1': 'QE', '2': 'Correct', '3': 'Correct'}
            _table['3'].update(dict(((afb, 'QE') for afb in afbs)))
            
        return _table
        
    
    
