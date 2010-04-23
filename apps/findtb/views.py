#!/usr/bin/env python
# -*- coding= UTF-8 -*-


from django.shortcuts import render_to_response
import random

def home(request, *arg, **kwargs):
    
    warnings = []
    for x in range(0, random.randint(0, 5)) :
        warnings.append("Sputum #%s is %s day(s) late" % (random.randint(1000, 9999),
                                                          random.randint(0, 5)))
                                                          
    districts = ["All", "Gulu", "Kabale", "Kampala", "Kumi"]
    batchs = [random.randint(1000, 9999) for x in range(random.randint(0, 6))]

    return render_to_response("home.html", locals())
    
    

def tracking(request, *args, **kwargs):
    
    batchs = ["#%s" % random.randint(1000, 9999) for x in range(5)]
    
    possible_results = ("Not selected",
                        "Negative",) +\
                        tuple("%s AFB" % x for x in range(1, 9)) +\
                        ("1+", "2+", "3+")
                        
    batch_arrived = random.randint(0, 1)
    
    slides = ["#%s" % random.randint(1000, 9999) for x in range(10)]
    
    events = ["Something is happening!"] * random.randint(0, 7)
    
    districts = ["Gulu", "Kabale", "Kampala", "Kumi"]
    
    batch_arrives = True
    
    types = ["DTU", "DTLS", "DLAB", "DLFP", "DTLF"]
    names = ["Keyta", "Kamara", "Camara", "Dolo", "Cissoko"]
    contacts = []
    for x in range(0, random.randint(0, 5)) :
        contacts.append({"type": types.pop(), "name": names.pop()})

    return render_to_response("tracking.html", locals())
