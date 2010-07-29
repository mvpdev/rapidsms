#!/usr/bin/env python

import rapidsms

class App (rapidsms.app.App):
  
    def handle(self, message):
       return False
