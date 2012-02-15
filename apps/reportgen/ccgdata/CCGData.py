#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: ukanga

import gdata.service
import gdata.spreadsheet
import gdata.spreadsheet.service

'''
class WorksheetAlreadyExists(Exception):
    pass
'''


class CCGData(object):
    '''Connect to google and update/create a spreadsheet with report data'''

    gd_client = gdata.spreadsheet.service.SpreadsheetsService()
    email = "childcount@gmail.com"
    password = ""
    source = "childcount-gdata"

    def login(self, email=None, password=None):
        if email is None:
            self.gd_client.email = self.email
        else:
            self.gd_client.email = email
        if password is None:
            self.gd_client.password = self.password
        else:
            self.gd_client.password = password
        self.gd_client.source = self.source
        self.gd_client.ProgrammaticLogin()

    def getSpreadsheetByKey(self, key):
        feed = self.gd_client.GetSpreadsheetsFeed(key=key)
        return feed.id.text.rsplit('/', 1)[1]

    def getWorkSheetByName(self, key, name):
        feed = self.gd_client.GetWorksheetsFeed(key)
        for i, entry in enumerate(feed.entry):
            if entry.title.text.lower() == name.lower():
                return feed.entry[i].id.text.rsplit('/', 1)[1]
        return None

    def createWorksheet(self, key, name="test", cols=20, rows=20):
        wksht_id = self.getWorkSheetByName(key, name)
        if wksht_id is None:
            feed = self.gd_client.AddWorksheet(name, rows, cols, key)
            return feed.id.text.rsplit('/', 1)[1]
        else:
            return wksht_id
            '''raise WorksheetAlreadyExists("Worksheet with name '" + name + \
                                            "' already exists!")'''

    def cellsUpdateAction(self, key, wksht_id, row, col, inputValue):
        entry = self.gd_client.UpdateCell(row=row, col=col, \
                    inputValue=inputValue, key=key, wksht_id=wksht_id)
        if isinstance(entry, gdata.spreadsheet.SpreadsheetsCell):
            return True
        return False
