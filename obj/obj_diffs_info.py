# coding: gbk

import x_coreobj

class CObj(x_coreobj.CObj):
	CLASS_TAG = "diffs_info"
	BASE = {
        '_id':0,
		'proj': 0,
        'rev':0,
        'filename':0,
        'diffinfo':0,
	}

	INDEX_CONFIG = {
		'index_proj': {
				'keylist': (('proj', 1),('rev',1),('filename',1)),
				'unique': False,
		},
	}

	ID_NEED_AUTO_INC = True

	def on_create(self, base={}):
		super(CObj, self).on_create(base)






