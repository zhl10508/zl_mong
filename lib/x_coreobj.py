# $Id: x_coreobj.py 163760 2014-11-20 02:32:51Z akara@NETEASE.COM $
# -*- coding: gbk -*-
# coreobj_base��mysql��չ
import copy
import x_coreobj_base
import x_serialize

##########################################################################
# ֧��mongodb��˵�coreobj
##########################################################################
class CObj(x_coreobj_base.CObj):

	DB_TAG = None

	# ���屾���Ͷ���Ĵ��̱��
	CLASS_TAG = "_attrobj_"

	# ����ʱ, _id�Ƿ���Ҫʹ������������ֵ
	# ���True,��_id������������int
	# ���False, ��_id����һ��uuid���ַ���
	ID_NEED_AUTO_INC = True

	# �������
	INDEX_CONFIG = {} 
	# format:
	# INDEX_CONFIG = {
	#	"index_name": 
	#	{
	#		#direction: pymongo.ASCENDING,pymongo.DESCENDING,pymongo.TEXT,pymongo.HASHED,pymongo.HASHED
	#		"keylist": ( ("uid",1), ),
	#		"unique": False,
	#	},
	# }

	

