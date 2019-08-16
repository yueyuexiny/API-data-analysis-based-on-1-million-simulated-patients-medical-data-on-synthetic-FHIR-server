import gzip
import json
import os
import hashlib
from pprint import pprint
import operator
import numpy as np

# Python 2
import urllib2

# Python 3
#import urllib

import util_5353

BASE_URL = 'https://syntheticmass.mitre.org/fhir/'
MAX_PATIENTS = 5000
CACHE_FILE = 'cache.dat'
PATH_CACHE = {}

# Returns the JSON result at the given URL.  Caches the results so we don't
# unnecessarily hit the FHIR server.  Note this ain't the best caching, as
# it's going to save a bunch of tiny files that could probably be handled more
# efficiently.
def get_url(url):
  # First check the cache
  if len(PATH_CACHE) == 0:
    for line in open(CACHE_FILE).readlines():
      split = line.strip().split('\t')
      cached_path = split[0]
      cached_url = split[1]
      PATH_CACHE[cached_url] = cached_path
  if url in PATH_CACHE:
    return json.loads(gzip.open(PATH_CACHE[url]).read().decode('utf-8'))

  print('Retrieving:', url)

  print('You are about to query the FHIR server, which probably means ' + \
        'that you are doing something wrong.  But feel free to comment ' + \
        'out this bit of code and proceed right ahead.')
  exit(1)
  print('Note: the code below is not tested for Python 3, you will likely ' + \
        'need to make a few changes, e.g., urllib2')

  resultstr = urllib2.urlopen(url).read()
  json_result = json.loads(resultstr)

  # Remove patient photos, too much space
  if url.replace(BASE_URL, '').startswith('Patient'):
    for item in json_result['entry']:
      item['resource']['photo'] = 'REMOVED'

  m = hashlib.md5()
  m.update(url)
  md5sum = m.hexdigest()

  path_dir = 'cache/' + md5sum[0:2] + '/' + md5sum[2:4] + '/'
  if not os.path.exists('cache'):
    os.mkdir('cache')
  if not os.path.exists('cache/' + md5sum[0:2]):
    os.mkdir('cache/' + md5sum[0:2])
  if not os.path.exists(path_dir):
    os.mkdir(path_dir)
  path = path_dir + url.replace(BASE_URL, '')

  w = gzip.open(path, 'wb')
  w.write(json.dumps(json_result))
  w.close()
  w = open(CACHE_FILE, 'a')
  w.write(path + '\t' + url + '\n')
  w.close()
  PATH_CACHE[url] = path

  return json_result

# For pagination, returns the next URL
def get_next(result):
  links = result['link']
  for link in links:
    if link['relation'] == 'next':
      return link['url']

# Returns the list of patients based on the given filter
def get_patients(pt_filter):
  patients = []
  url = BASE_URL + 'Patient?_offset=0&_count=1000'
  while url is not None:
    patients_page = get_url(url)
    if 'entry' not in patients_page:
      break
    for patient_json in patients_page['entry']:
      if pt_filter.include(patient_json['resource']):
        patients.append(patient_json['resource'])
        if MAX_PATIENTS is not None and len(patients) == MAX_PATIENTS:
          return patients
    url = get_next(patients_page)
  return patients

# Returns the conditions for the patient with the given patient_id
def get_conditions(patient_id):
  url = BASE_URL + 'Condition?patient=' + patient_id + '&_offset=0&_count=1000'
  conditions = []
  while url is not None:
    conditions_page = get_url(url)
    if 'entry' in conditions_page:
      conditions.extend([c['resource'] for c in conditions_page['entry']])
    url = get_next(conditions_page)
  return conditions

# Returns the observations for the patient with the given patient_id
def get_observations(patient_id):
  url = BASE_URL + 'Observation?patient=' + patient_id + '&_offset=0&_count=1000'
  observations = []
  while url is not None:
    observations_page = get_url(url)
    if 'entry' in observations_page:
      observations.extend([o['resource'] for o in observations_page['entry']])
    url = get_next(observations_page)
  return observations

# Returns the medications for the patient with the given patient_id
def get_medications(patient_id):
  url = BASE_URL + 'MedicationRequest?patient=' + patient_id + '&_offset=0&_count=1000'
  medications = []
  DBG = 0
  while url is not None:
    medications_page = get_url(url)
    if 'entry' in medications_page:
      medications.extend([c['resource'] for c in medications_page['entry']])
    url = get_next(medications_page)
  return medications

# Problem 1 [10 points]
def num_patients(pt_filter):
  tup = None
  # Begin CODE
  name_buffer=[]
  unique_buffer = []
  b = get_patients(pt_filter)
  for patients in b:
    surname = patients['name'][0]['family']
    name_buffer.append(surname)
    if surname not in unique_buffer:
      unique_buffer.append(surname)
  tup = tuple((len(name_buffer), len(unique_buffer)))
  #print(tup)
  # End CODE
  return tup


# Problem 2 [10 points]
def patient_stats(pt_filter):
  stats = {}
  # Begin CODE
  b= get_patients(pt_filter)
  ethnicity={}
  gender={}
  maritalStatus={}
  race ={}
  address = {'yes_address':0, 'no_address':0}
  birthyear={}

  for patients in b:

    if 'gender' not in patients:
      gender1='UNK'
    else:
      gender1 = str(patients['gender'])
    if gender1 not in gender:
      gender[gender1] = 1
    else:
      gender[gender1] += 1


    if 'maritalStatus' not in patients:
      maritalStatus1 ='UNK'
    else:
      maritalStatus1 = str(patients['maritalStatus']['coding'][0]['code'])
    if maritalStatus1 not in maritalStatus:
      maritalStatus[maritalStatus1] = 1
    else:
      maritalStatus[maritalStatus1] += 1

    race1 ='UNK'
    race1 = str(patients['extension'][0]['valueCodeableConcept']['coding'][0]['display'])
    if race1 not in race:
      race[race1] = 1
    else:
      race[race1] += 1

    ethnicity1 = 'UNK'
    ethnicity1 = str(patients['extension'][1]['valueCodeableConcept']['coding'][0]['display'])
    if ethnicity1 not in ethnicity:
      ethnicity[ethnicity1] =1
    else:
      ethnicity[ethnicity1] += 1

    if 'address' not in patients:
      address1= 'no_address'
      address[address1] += 1
    else:
      address1 = 'yes_address'
      address[address1] += 1

    birthyear1 = str(patients['birthDate'])[:4]    # select year from year-mm-dd
    birthyear1 = birthyear1[:3] +'0'
    if birthyear1 not in birthyear:
        birthyear[birthyear1] = 1
    else:
        birthyear[birthyear1] += 1

  total = sum(gender.itervalues(), 0.0)
  gender = {k: v / total for k, v in gender.iteritems()}
  total = sum(maritalStatus.itervalues(), 0.0)
  maritalStatus = {k: v / total for k, v in maritalStatus.iteritems()}
  total = sum(race.itervalues(), 0.0)
  race = {k: v / total for k, v in race.iteritems()}
  total = sum(ethnicity.itervalues(), 0.0)
  ethnicity = {k: v / total for k, v in ethnicity.iteritems()}
  total = sum(birthyear.itervalues(), 0.0)
  birthyear = {k: v / total for k, v in birthyear.iteritems()}
  total = sum(address.itervalues(), 0.0)
  address = {k: v / total for k, v in address.iteritems()}

  stats['gender']= gender
  stats['marital_status']= maritalStatus
  stats['race']= race
  stats['ethnicity']= ethnicity
  stats['age']= birthyear
  stats['with_address'] = address
  #pprint(stats)
  # End CODE
  return stats

# Problem 3 [15 points]
def diabetes_quality_measure(pt_filter):
  tup = None
  # Begin CODE
  b= get_patients(pt_filter)
  diabetes_num =0
  hemo_num = 0
  hemo_value_num=0

  for patients in b:
    patient_id =str(patients['id'])
    c = get_conditions(patient_id)

    for observation in c:
      diabetes = str(observation['code']['coding'][0]['code'])
      if diabetes == "44054006":
        #print(diabetes)
        diabetes_num +=1
        o = get_observations(patient_id)
        hemo_Bool = False
        hemo_value_Bool = False
        #print(d[0])
        for obser in o:
          hemo = str(obser['code']['coding'][0]['code'])
          #print(hemo)
          if hemo == '4548-4':
            hemo_Bool = True
            if 'valueQuantity' in obser:
              value =float(obser['valueQuantity']['value'])
            if value > 6.0:
              hemo_value_Bool = True
        if hemo_Bool:
          hemo_num += 1
        if hemo_value_Bool:
          hemo_value_num += 1
  tup = tuple((diabetes_num, hemo_num,hemo_value_num ))
  #print(tup)
  # End CODE
  return tup

# Problem 4 [10 points]
def common_condition_pairs(pt_filter):
  pairs = []
  # Begin CODE
  b= get_patients(pt_filter)
  dict = {}
  cnew =[]
  for patients in b:
    patient_id =str(patients['id'])
    c = get_conditions(patient_id)
    d_4 =[]
    for condi in c:
      d_4.append(str(condi['code']['coding'][0]['display']))
    d_4 = list(set(d_4))
    #print(len(cnew))

    if len(d_4) >1 :
      for i in range(len(d_4)-1):
        for j in range(i,len(d_4)):
          disease1= d_4[i]
          disease2= d_4[j]
          if disease1 != disease2:
            co = tuple(sorted((disease2, disease1)))
            if co in dict:
              dict[co] += 1
            else:
              dict[co] = 1

  dict = sorted(dict.items(), key=operator.itemgetter(1))
  #pprint(dict)
  index= -1
  while index > -11:
    pairs.append(dict[index][0])
    index -=1
  #pprint(pairs)
  # End CODE
  return pairs

# Problem 5 [10 points]
def common_medication_pairs(pt_filter):
  pairs = []
  # Begin CODE
  b= get_patients(pt_filter)
  dict = {}
  act_med = []
  for patients in b:
    patient_id =str(patients['id'])
    m = get_medications(patient_id)
    #pprint(m)
    d_5 =[]
    for medi in m:
      if medi['status'] =='active':
        d_5.append(str(medi['medicationCodeableConcept']['coding'][0]['display']))
    d_5 = list(set(d_5))

    if len(d_5) >1:
      for i in range(len(d_5)-1):
        for j in range(i,len(d_5)):
          medication1= d_5[i]
          medication2= d_5[j]
          if medication1 != medication2:
            co = tuple(sorted((medication1, medication2)))
            if co in dict:
              dict[co] -=1
            else:
              dict[co] =-1

  dict = sorted(dict.items(), key =operator.itemgetter(1,0))
  #pprint(dict)
  index= 0
  while index < 10:
    pairs.append(dict[index][0])
    index +=1
  pprint(pairs)
  # End CODE
  return pairs

# Problem 6 [10 points]
def conditions_by_age(pt_filter):
  tup = None
  # Begin CODE
  b= get_patients(pt_filter)
  id_50=[]
  id_15=[]
  dict_50 ={}
  dict_15 ={}
  list_50=[]
  list_15=[]
  for patients in b:
    birth = int(str(patients['birthDate']).replace('-',''))    # select year from year-mm-dd
    if birth <= 19680131 :
      id_50.append(str(patients['id']))
    if birth >= 20030201:
      id_15.append(str(patients['id']))
  for patient_id in id_50:
    c = get_conditions(patient_id)
    for patients in c:
      if str(patients['clinicalStatus']) == 'active':
        condition=str(patients['code']['coding'][0]['display'])
        if not ((condition.endswith('itis')) or ('itis' in condition)):
          if condition in dict_50:
            dict_50[condition] -= 1
          else:
            dict_50[condition] = -1
  #pprint(dict_50)
  dict_50 = sorted(dict_50.items(), key=operator.itemgetter(1,0))
  index= 0
  while index < 10:
    list_50.append(dict_50[index][0])
    index +=1
  #print(list_50)

  for patient_id in id_15:
    c = get_conditions(patient_id)
    for patients in c:
      if str(patients['clinicalStatus']) == 'active':
        condition=str(patients['code']['coding'][0]['display'])
        if not ((condition.endswith('itis')) or ('itis' in condition)):
          if condition in dict_15:
            dict_15[condition] -=1
          else:
            dict_15[condition] =-1
  dict_15 = sorted(dict_15.items(), key=operator.itemgetter(1,0))
  #pprint(dict_15)
  index= 0
  while index <10:
    list_15.append(dict_15[index][0])
    index +=1
  tup = tuple((list_50, list_15))
  #pprint(tup)
  # End CODE
  return tup

# Problem 7 [10 points]
def medications_by_gender(pt_filter):
  tup = None
  # Begin CODE
  b= get_patients(pt_filter)
  medication_female_dict={}
  medication_male_dict ={}
  med_female =[]
  med_male = []
  
  for patients in b:
    gender = str(patients['gender'])
    if gender == 'female':
      id_female = str(patients['id'])
      m_female = get_medications(id_female)

      for patients in m_female:
        if str(patients['status']) == 'active':
          medication_female = str(patients['medicationCodeableConcept']['coding'][0]['display'])
          if medication_female not in medication_female_dict:
            medication_female_dict[medication_female] = -1
          else:
            medication_female_dict[medication_female] -= 1

    if gender == 'male':
      id_male = str(patients['id'])
      m_male = get_medications(id_male)

      for patients in m_male:
        if str(patients['status']) == 'active':
          medication_male = str(patients['medicationCodeableConcept']['coding'][0]['display'])
          if medication_male not in medication_male_dict:
            medication_male_dict[medication_male] = -1
          else:
            medication_male_dict[medication_male] -= 1

  medication_female_dict = sorted(medication_female_dict.items(), key=operator.itemgetter(1,0))
  index= 0
  while index <10:
    med_female.append(medication_female_dict[index][0])
    index +=1

  medication_male_dict = sorted(medication_male_dict.items(), key=operator.itemgetter(1,0))
  index= 0
  while index <10:
    med_male.append(medication_male_dict[index][0])
    index +=1
  #pprint(medication_female)
  tup = tuple((med_male, med_female))
  #pprint(tup)
  # End CODE
  return tup

# Problem 8 [25 points]
def bp_stats(pt_filter):
  stats = []
  # Begin CODE
  norm_p = []
  abnm_p = []
  unkn_p = []
  sys_bp = []
  dia_bp = []
  b= get_patients(pt_filter)
  for patients in b:
    patient_id =str(patients['id'])
    o = get_observations(patient_id)
    for observation in o:
      if observation['code']['coding'][0]['code'] == '55284-4':
        sys_blood = int(observation['component'][0]['valueQuantity']['value'])
        dia_blood = int(observation['component'][1]['valueQuantity']['value'])
        sys_bp.append(sys_blood)
        dia_bp.append(dia_blood)
    if not sys_bp:
      unkn_p.append(patient_id)
    else:
      bp_all = len(sys_bp)
      bp_good = 0
      for s_bp in sys_bp:
        d_bp = dia_bp[sys_bp.index(s_bp)]
        if 90 <= s_bp <= 140 and  60 <= d_bp <= 90:
          bp_good += 1
      if float(bp_good) / float(bp_all) >= 0.9:
        norm_p.append(patient_id)
      else:
        abnm_p.append(patient_id)
    sys_bp = []
    dia_bp = []
  #print(len(norm_p), len(abnm_p), len(unkn_p))


  dict_norm = {}
  con_numb = []
  for id in norm_p:
    con_norm = get_conditions(id)
    con_numb.append(len(con_norm))
  con_numb = sorted(con_numb)
  dict_norm["min"] = float(con_numb[0])
  dict_norm["max"] = float(con_numb[-1])
  con_numb_len = len(con_numb)
  if float(con_numb_len)/2 ==0:
    dict_norm["median"] = float(con_numb[con_numb_len/2 -1] + con_numb[con_numb_len/2])/2
  else:
    dict_norm["median"] = float(con_numb[len(con_numb)/2])
  dict_norm["mean"] = sum(con_numb) / float(con_numb_len)
  dict_norm["stddev"] = np.std(con_numb)

  dict_abnm = {}
  con_abnm = []
  for id in abnm_p:
    con_abnorm = get_conditions(id)
    con_abnm.append(len(con_abnorm))
  con_abnm = sorted(con_abnm)
  dict_abnm["min"] = float(con_abnm[0])
  dict_abnm["max"] = float(con_abnm[-1])
  con_abnm_len = len(con_abnm)
  if float(con_abnm_len)/2 ==0:
    dict_abnm["median"] = float(con_abnm[con_abnm_len/2 -1] + con_abnm[con_abnm_len/2])/2
  else:
    dict_abnm["median"] = float(con_abnm[len(con_abnm)/2])
  dict_abnm["mean"] = sum(con_abnm) / float(con_abnm_len)
  dict_abnm["stddev"] = np.std(con_abnm)

  dict_unkn = {}
  con_unkn = []
  for id in unkn_p:
    con_unknown = get_conditions(id)
    con_unkn.append(len(con_unknown))
  con_unkn = sorted(con_unkn)
  dict_unkn["min"] = float(con_unkn[0])
  dict_unkn["max"] = float(con_unkn[-1])
  con_unkn_len = len(con_unkn)
  if float(con_unkn_len)/2 ==0:
    dict_unkn["median"] = float(con_unkn[con_unkn_len/2 -1] + con_unkn[con_unkn_len/2])/2
  else:
    dict_unkn["median"] = float(con_unkn[len(con_unkn)/2])
  dict_unkn["mean"] = sum(con_unkn) / float(con_unkn_len)
  dict_unkn["stddev"] = np.std(con_unkn)

  stats = [dict_norm, dict_abnm, dict_unkn]
  #pprint(stats)

  # End CODE
  return stats


# Basic filter, lets everything pass
class all_pass_filter:
  def id(self):
    return 'all_pass'
  def include(self, patient):
    util_5353.assert_dict_key(patient, 'id', 'pt_filter')
    util_5353.assert_dict_key(patient, 'name', 'pt_filter')
    util_5353.assert_dict_key(patient, 'address', 'pt_filter')
    util_5353.assert_dict_key(patient, 'birthDate', 'pt_filter')
    util_5353.assert_dict_key(patient, 'gender', 'pt_filter')
    return True

# Note: don't mess with this code block!  Your code will be tested by an outside
# program that will not call this __main__ block.  So if you mess with the
# following block of code you might crash the autograder.  You're definitely
# encouraged to look at this code, however, especially if your code crashes.
if __name__ == '__main__':

  # Include all patients
  pt_filter = all_pass_filter()

  print('::: Problem 1 :::')
  one_ret = num_patients(pt_filter)
  util_5353.assert_tuple(one_ret, 2, '1')
  util_5353.assert_int_range((0, 10000000), one_ret[0], '1')
  util_5353.assert_int_range((0, 10000000), one_ret[1], '1')

  print('::: Problem 2 :::')
  two_ret = patient_stats(pt_filter)
  util_5353.assert_dict(two_ret, '2')
  util_5353.assert_dict_key(two_ret, 'gender', '2')
  util_5353.assert_dict_key(two_ret, 'marital_status', '2')
  util_5353.assert_dict_key(two_ret, 'race', '2')
  util_5353.assert_dict_key(two_ret, 'ethnicity', '2')
  util_5353.assert_dict_key(two_ret, 'age', '2')
  util_5353.assert_dict_key(two_ret, 'with_address', '2')
  util_5353.assert_dict(two_ret['gender'], '2')
  util_5353.assert_dict(two_ret['marital_status'], '2')
  util_5353.assert_dict(two_ret['race'], '2')
  util_5353.assert_dict(two_ret['ethnicity'], '2')
  util_5353.assert_dict(two_ret['age'], '2')
  util_5353.assert_dict(two_ret['with_address'], '2')
  util_5353.assert_prob_dict(two_ret['gender'], '2')
  util_5353.assert_prob_dict(two_ret['marital_status'], '2')
  util_5353.assert_prob_dict(two_ret['race'], '2')
  util_5353.assert_prob_dict(two_ret['ethnicity'], '2')
  util_5353.assert_prob_dict(two_ret['age'], '2')
  util_5353.assert_prob_dict(two_ret['with_address'], '2')

  print('::: Problem 3 :::')
  three_ret = diabetes_quality_measure(pt_filter)
  util_5353.assert_tuple(three_ret, 3, '3')
  util_5353.assert_int_range((0, 1000000), three_ret[0], '3')
  util_5353.assert_int_range((0, 1000000), three_ret[1], '3')
  util_5353.assert_int_range((0, 1000000), three_ret[2], '3')

  print('::: Problem 4 :::')
  four_ret = common_condition_pairs(pt_filter)
  util_5353.assert_list(four_ret, 10, '4')
  for i in range(len(four_ret)):
    util_5353.assert_tuple(four_ret[i], 2, '4')
    util_5353.assert_str(four_ret[i][0], '4')
    util_5353.assert_str(four_ret[i][1], '4')

  print('::: Problem 5 :::')
  five_ret = common_medication_pairs(pt_filter)
  util_5353.assert_list(five_ret, 10, '5')
  for i in range(len(five_ret)):
    util_5353.assert_tuple(five_ret[i], 2, '5')
    util_5353.assert_str(five_ret[i][0], '5')
    util_5353.assert_str(five_ret[i][1], '5')

  print('::: Problem 6 :::')
  six_ret = conditions_by_age(pt_filter)
  util_5353.assert_tuple(six_ret, 2, '6')
  util_5353.assert_list(six_ret[0], 10, '6')
  util_5353.assert_list(six_ret[1], 10, '6')
  for i in range(len(six_ret[0])):
    util_5353.assert_str(six_ret[0][i], '6')
    util_5353.assert_str(six_ret[1][i], '6')

  print('::: Problem 7 :::')
  seven_ret = medications_by_gender(pt_filter)
  util_5353.assert_tuple(seven_ret, 2, '7')
  util_5353.assert_list(seven_ret[0], 10, '7')
  util_5353.assert_list(seven_ret[1], 10, '7')
  for i in range(len(seven_ret[0])):
    util_5353.assert_str(seven_ret[0][i], '7')
    util_5353.assert_str(seven_ret[1][i], '7')

  print('::: Problem 8 :::')
  eight_ret = bp_stats(pt_filter)
  util_5353.assert_list(eight_ret, 3, '8')
  for i in range(len(eight_ret)):
    util_5353.assert_dict(eight_ret[i], '8')
    util_5353.assert_dict_key(eight_ret[i], 'min', '8')
    util_5353.assert_dict_key(eight_ret[i], 'max', '8')
    util_5353.assert_dict_key(eight_ret[i], 'median', '8')
    util_5353.assert_dict_key(eight_ret[i], 'mean', '8')
    util_5353.assert_dict_key(eight_ret[i], 'stddev', '8')

  print('~~~ All Tests Pass ~~~')


