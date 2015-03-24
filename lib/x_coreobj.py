# $Id: x_coreobj.py 163760 2014-11-20 02:32:51Z akara@NETEASE.COM $
# -*- coding: gbk -*-
# coreobj_base的mysql扩展
import copy
import x_coreobj_base
import x_serialize

##########################################################################
# 支持mongodb后端的coreobj
##########################################################################
class CObj(x_coreobj_base.CObj):

	DB_TAG = None

	# 定义本类型对象的存盘标记
	CLASS_TAG = "_attrobj_"

	# 存盘时, _id是否需要使用自增长的数值
	# 如果True,则_id会是自增长的int
	# 如果False, 则_id会是一个uuid的字符串
	ID_NEED_AUTO_INC = True

	# 索引相关
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

	

