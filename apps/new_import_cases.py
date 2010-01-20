#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

import csv
import codecs
import sys
import re
import datetime

import os
from os import path

# figure out where all the extra libs (rapidsms and contribs) are
libs=[os.path.abspath('lib'),os.path.abspath('apps')] # main 'rapidsms/lib'
try:
    for f in os.listdir('contrib'):
        pkg = path.join('contrib',f)
        if path.isdir(pkg) and \
                'lib' in os.listdir(pkg):
            libs.append(path.abspath(path.join(pkg,'lib')))
except:
    # could be several reasons:
    # no 'contrib' dir, 'contrib' not a dir
    # 'contrib' not readable, in any case
    # ignore and leave 'libs' as just
    # 'rapidsms/lib'
    pass

# add extra libs to the python sys path
sys.path.extend(libs)

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.core.management import setup_environ

try:
    from rapidsms.webui import settings
    setup_environ(settings)
except:
    sys.exit("you may have to set an environment variable specifying your ini file\
    on a *nix system, do something like this from the command line:\
    $ export RAPIDSMS_INI=/absolute/path/to/my/local.ini")


from childcount.models import general
from reporters.models import Reporter
from reporters.models import Location

from muac.models import ReportMalnutrition as pb

def get_good_date(date):
    # TODO move to a utils file?
    delimiters = r"[./\\-]+"
    # expecting DD-MM-YYYY, DD-MM-YY, D-M-YY, etc (with any of the delimiters)
    Allsect=re.split(delimiters,date)            
    if Allsect is not None:
        try:
            year = Allsect[2]
            #day = Allsect[0]
            #month = Allsect[1]         
            day = Allsect[1]
            month = Allsect[0]
            # make sure we have a real day
            if month.isdigit():
                if int(month) == 2:
                    if int(day) > 28:
                        day = 28
                if int(month) in [4, 6, 9, 11]:
                    if int(day) > 30:
                        day = 30
            else:
                return None

            # if there are letters in the date, give up
            if not year.isdigit():
                return None
            if not day.isdigit():
                return None

            # add leading digits if they are missing
            # TODO use datetime.strptime for this?
            if len(year) < 4 : 
                year = "20%s" % year        
            if len(month) < 2:
                month = "0%s" % month
            if len(day) == 1:
                day = "0%s" % day         
            if len(day) == 0:
                day = "15"
            good_date_str = "%s-%s-%s" % (int(year),int(month),int(day))
            #good_date_obj = datetime.date(int(year), int(month), int(day))
            return good_date_str
        except Exception, e:
            return None

def age_to_estimated_bday(age_in_months):
    # TODO move to a utils file? (same code is in apps/childcount/app.py)
    try:
        age_in_months = re.sub(r'\D', '', age_in_months)
        if age_in_months.isdigit():
            #les informations ont ete saisies il y a deux mois
            mois_en_plus = 2
            years = (int(age_in_months )+mois_en_plus) / 12
            months = (int(age_in_months )+mois_en_plus) % 12
            est_year = abs(datetime.date.today().year - int(years))
            #
            delta=datetime.date.today().month - int(months)
            if delta==0:
               est_month = months
            else:
                if delta<0:
                   est_month = 12 + datetime.date.today().month - months 
                   est_year=est_year-1 
                else:
                    est_month=delta
            #
            #est_month = abs(datetime.date.today().month - int(months))
            #if est_month == 0:
            #    est_month = 1

            estimate = ("%s-%s-%s" % (est_year, est_month, 15))
            return estimate
        else:
            return None
    except Exception, e:
        sys.exit(e)


def import_cases_from_csv(csvfile):
    try:
        reporter = Reporter.objects.get(alias='import')
    except (ObjectDoesNotExist, MultipleObjectsReturned):
        sys.exit("Cases require a foreign key relationship with a reporter.\
                    You must create a reporter with alias=import")

    try:
        location = Location.objects.get(code='dsa')
    except (ObjectDoesNotExist, MultipleObjectsReturned):
        sys.exit("Cases require a foreign key relationship with a location.\
                    You must create a location with code=dsa")

    # use codecs.open() instead of open() so all characters are utf-8 encoded
    # BEFORE we start dealing with them. 
    # rU option is for universal-newline mode which takes care of \n or \r etc
    csvee = codecs.open("darousalam.csv", "rU", encoding='utf-8', errors='ignore')

    # sniffer attempts to guess the file's dialect e.g., excel, etc
    dialect = csv.Sniffer().sniff(csvee.read(1024))
    csvee.seek(0)
    # DictReader uses first row of csv as key for data in corresponding column
    reader = csv.DictReader(csvee, dialect=dialect)

    try:
        for row in reader:
            # dict for collecting field keys and values
            case = {}
            muac = {}
            # break name into last name and first name(s)
            if row.has_key('first_name')  :
                if row['first_name'] != "":
                    #first_name, sep, last_name = row['name'].rstrip().rpartition(' ')
                    first_name = row['first_name']
                    case.update({'first_name' : first_name})
            if row.has_key('last_name')  :
                if row['last_name'] != "":
                    last_name=row['last_name']
                    case.update({'last_name' : last_name})
            if row.has_key('gender')  :
                if row['gender'] != "":
                    gender=row['gender']
                    case.update({'gender' : gender})

            # if there is date_of_birth, format it and set 'estimated_dob' flag to false
            if row.has_key('date_of_birth'):
                if row['date_of_birth'] != "":
                    try:
                        dob = get_good_date(row['date_of_birth'])
                        if dob is not None:
                            case.update({'dob' : dob, 'estimated_dob' : False })
                        else:
                            # TODO DRY
                            if row.has_key('age'):
                                if row['age'] != "":
                                    try:
                                        est_bday = age_to_estimated_bday(row['age'])
                                        if est_bday is not None:
                                            case.update({'dob' : est_bday,\
                                                    'estimated_dob' : True })
                                    except Exception, e:
                                        sys.exit(e + " " + case)
                            
                    except Exception, e:
                        sys.exit(e + ' ' + case)

                # if there is no date_of_birth, estimate date of birth instead and set flag
                else: 
                    # TODO DRY
                    if row.has_key('age'):
                        if row['age'] != "":
                            try:
                                est_bday = age_to_estimated_bday(row['age'])
                                if est_bday is not None:
                                    case.update({'dob' : est_bday,\
                                            'estimated_dob' : True })
                            except Exception, e:
                                sys.exit(e + " " + case)
            
            if row.has_key('guardian_first_name'):
                if row['guardian_first_name'] != "":
                    if row.has_key('guardian_last_name'):
                       if row['guardian_last_name'] != "": 
                            guardian=row['guardian_first_name']+' '+row['guardian_last_name']
                            case.update({'guardian' : guardian})         
                       else:
                            guardian=row['guardian_first_name']
                            case.update({'guardian' : guardian})         
                    else:
                        guardian=row['guardian_first_name']
                        case.update({'guardian' : guardian})         
                else:
                    if row.has_key('guardian_last_name'):
                       if row['guardian_last_name'] != "": 
                            guardian=row['guardian_last_name']
                            case.update({'guardian' : guardian})         
            else:
                if row.has_key('guardian_last_name'):
                    if row['guardian_last_name'] != "": 
                       guardian=row['guardian_last_name']
                       case.update({'guardian' : guardian})          
            

            if row.has_key('guardian_id'):
                # not sure how one of these became None
                if row['guardian_id'] != "" and row['guardian_id'] is not None:
                    case.update({'guardian_id' : row['guardian_id']})


            # if case already exists, or we haven't
            # gathered any fields, do nothing
            try:
                if len(case) > 0:
                    exists = general.Case.objects.get(**case)
                else:
                    continue

            # if it does not exist, create and save
            except ObjectDoesNotExist:
                try:
                    case.update({'reporter' : reporter, 'location' : location})
                except Exception, e:
                    sys.exit(e + " " + case)
                new_case = general.Case(**case)
                new_case.save()
            
                #muac/pb
                if row.has_key('PB'):
                    # not sure how one of these became None
                    if row['PB'] != "" and row['PB'] is not None:
                        case_muac = general.Case.objects.get(**case)                        
                        muac.update({'case' : case_muac,'reporter' : reporter,'muac' : row['PB']})
                        new_muac = pb(**muac)
                        new_muac.save()
                
                
 
                   
            # if many exist, you are probably surprised, so exit
            except MultipleObjectsReturned:
                sys.exit(case)    

    except csv.Error, e:
        # TODO handle this error?
        sys.exit('%d : %s' % (reader.reader.line_num, e))


if __name__ == "__main__":
    import_cases_from_csv(sys.argv) 
