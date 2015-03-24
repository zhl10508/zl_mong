# coding: gbk

import x_coreobj

class CObj(x_coreobj.CObj):
	CLASS_TAG = "logs_info"
	BASE = {
        '_id':0,
		'proj': 0,
        'rev':0,
        'author':0,
        'comment':0,
        'date':0,
        'files':0,
	}

	INDEX_CONFIG = {
		'index_proj': {
				'keylist': (('proj', 1),('rev',1)),
				'unique': False,
		},
	}

	ID_NEED_AUTO_INC = True

	def on_create(self, base={}):
		super(CObj, self).on_create(base)






