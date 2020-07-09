file_ext_dict = {}
file_ext_dict['python'] = ['.py', '.pyo']
file_ext_dict['java'] = ['.java']
file_ext_dict['javascript'] = ['.js']
file_ext_dict['ruby'] = ['.rb', '.erb']
file_ext_dict['r'] = ['.r']
file_ext_dict['tex'] = ['.tex']
file_ext_dict['c'] = ['.c', '.cc']
file_ext_dict['c++'] = ['.cpp', '.cxx']
file_ext_dict['c#'] = ['.cs']

supported_languages = ['python', 'java', 'javascript', 'ruby','tex', 'c', 'c++', 'c#']

ck_thresholds = {}
ck_thresholds['cbo'] = 9
ck_thresholds['wmc'] = 20
ck_thresholds['dit'] = 2
ck_thresholds['rfc'] = 40
ck_thresholds['lcom'] = 0