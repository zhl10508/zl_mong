# coding: gbk

import x_coreobj

class CObj(x_coreobj.CObj):
	CLASS_TAG = "proj_info"
	BASE = {
        '_id':0,
		'proj': 0,
        'rev':0,
	}

	INDEX_CONFIG = {
		'index_proj': {
				'keylist': (('proj', 1),),
				'unique': True,
		},
	}

	ID_NEED_AUTO_INC = True

	def on_create(self, base={}):
		super(CObj, self).on_create(base)






