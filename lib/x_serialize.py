# $Id: x_serialize.py 163012 2014-11-12 03:54:34Z ycwang@NETEASE.COM $
# -*- coding: gbk -*-
	
CLASS_TAG = "_C_"
INT_DICT_TAG = "_INT_DICT_"

class CIntDict(dict): pass


# 包含msgpack/json等通用的数据类型
SIMPLE_TYPES = set([
	str, unicode, list, tuple, dict, int, long, float, type(None), bool, CIntDict,
])

# 包含python特有的数据类型，比如set/frozenset
COMPLEX_TYPES = set([
	str, unicode, list, tuple, dict, int, long, float, type(None), bool, set, frozenset, CIntDict,
]) 

OBJ_TYPE = "_TYPE_ATTR_OBJ_"

def TYPE(v):
	raw_type = type(v)
	if raw_type in SIMPLE_TYPES:
		return raw_type
	
	if hasattr(v, "CLASS_TAG"):
		return OBJ_TYPE
	else:
		raise Exception("unsupport data type: %s"%(raw_type))
		
#===========================================================================
# nor_any函数：将一个python容器，规则化成不包含coreobj的基础数据类型集合，
# 以便于被dumps函数序列化
#===========================================================================
def nor_any(v, depth = 0):
	global HANDLERS
	vtype = TYPE(v)
	return HANDLERS[vtype](v, depth) 
		
def nor_not_change(v, depth = 0):
	return v

def nor_list(v, depth = 0):
	depth = depth + 1
	return [nor_any(item, depth) for item in v]

def nor_tuple(v, depth = 0):
	depth = depth + 1
	return tuple( [nor_any(item, depth) for item in v] )

#def nor_set(v, depth = 0):
#	out = set()
#	for item in v:
#		out.add( nor_any(item, depth = depth + 1) )
#	return out
#
#def nor_frozenset(v, depth = 0):
#	out = set()
#	for item in v:
#		out.add( nor_any(item, depth = depth + 1) )
#	return frozenset(out)	
	
def nor_dict(v, depth = 0):
	out = {}
	need_str = (type(v) != dict)
	for key, value in v.iteritems():
		n_key = nor_any(key, depth = depth + 1)
		n_value = nor_any(value, depth = depth + 1)
		if need_str:
			n_key = str(n_key)
		out[ n_key ] = n_value
	if need_str:
		out[INT_DICT_TAG] = 1
	return out

def nor_obj(v, depth = 0):	
	#return [CLASS_TAG, v.CLASS_TAG, nor_any(v._base_, depth = depth + 1)]
	objdict = nor_any(v._base_, depth=depth+1)
	objdict[CLASS_TAG] = v.CLASS_TAG
	return objdict
	
HANDLERS = {
str: nor_not_change,
unicode: nor_not_change,
int: nor_not_change,
long: nor_not_change,
float: nor_not_change,
type(None): nor_not_change,
bool: nor_not_change,

list: nor_list,
tuple: nor_tuple,
dict: nor_dict,
CIntDict: nor_dict,
#set: nor_set,
#frozenset: nor_frozenset,

OBJ_TYPE: nor_obj,
}


def RTYPE(v):
	raw_type = type(v)
	if raw_type not in SIMPLE_TYPES:
		raise Exception("unsupport recover type: %s"%(raw_type))
	
	#if raw_type == list and len(v) == 3 and v[0] == CLASS_TAG:
	if raw_type == dict and v.get(CLASS_TAG, None):
		return OBJ_TYPE
	else:
		return raw_type

#===========================================================================
# recover_any函数：是nor_any函数的反函数，恢复成原来的coreobj结构
#===========================================================================
def recover_any(v, class_dict, depth = 0):
	global RECOVER_HANDLERS
	vtype = RTYPE(v)
	return RECOVER_HANDLERS[vtype](v, class_dict, depth)	

	
def recover_not_change(v, class_dict, depth = 0):
	return v

def recover_list(v, class_dict, depth = 0):
	depth = depth + 1
	return [recover_any(item, class_dict, depth) for item in v]

def recover_tuple(v, class_dict, depth = 0):
	depth = depth + 1
	return tuple( [recover_any(item, class_dict, depth) for item in v] )

#def recover_set(v, class_dict, depth = 0):
#	depth = depth + 1
#	out = set()
#	for item in v:
#		out.add( recover_any(item, class_dict, depth) )
#	return out
#
#def recover_frozenset(v, class_dict, depth = 0):
#	depth = depth + 1
#	out = set()
#	for item in v:
#		out.add( recover_any(item, class_dict, depth) )
#	return frozenset(out)	
	
def recover_dict(v, class_dict, depth = 0):
	depth = depth + 1
	if INT_DICT_TAG in v:
		need_int = True
		out = CIntDict()
		v.pop(INT_DICT_TAG)
	else:
		out = {}
		need_int = False

	for key, value in v.iteritems():
		n_key = recover_any(key, class_dict, depth)
		n_value = recover_any(value, class_dict, depth)
		if need_int:
			n_key = int(n_key)
		out[ n_key ] = n_value
	return out	
	
def recover_obj(v, class_dict, depth = 0):
	clsname = v.pop(CLASS_TAG)
	cls = class_dict[clsname]
	obj = cls()
	obj.on_create( base = recover_any(v, class_dict, depth = depth + 1) )
	return obj


RECOVER_HANDLERS = {
str: recover_not_change,
unicode: recover_not_change,
int: recover_not_change,
long: recover_not_change,
float: recover_not_change,
type(None): recover_not_change,
bool: recover_not_change,

list: recover_list,
tuple: recover_tuple,
dict: recover_dict,
CIntDict: recover_dict,
#set: recover_set,
#frozenset: recover_frozenset,

OBJ_TYPE: recover_obj,
}

def DETAIL_TYPE(v):
	raw_type = type(v)
	if raw_type in COMPLEX_TYPES:
		return raw_type
	
	if hasattr(v, "CLASS_TAG"):
		return OBJ_TYPE
	else:
		raise Exception("unsupport repr type: %s"%(raw_type))

#===========================================================================
# detail_any函数：将coreobj的当前情况以树状list的形式组织，方便各种查看/修改。
#===========================================================================
def detail_any(v, depth = 0):
	global DETAIL_HANDLERS
	return DETAIL_HANDLERS[DETAIL_TYPE(v)](v, depth)

def detail_simple(v, depth = 0):
	return v

def detail_list(v, depth = 0):
	depth = depth + 1
	return [detail_any(item, depth) for item in v]

def detail_tuple(v, depth = 0):
	depth = depth + 1
	return tuple( [detail_any(item, depth) for item in v] )

def detail_set(v, depth = 0):
	out = set()
	for item in v:
		out.add( detail_any(item, depth = depth + 1) )
	return out

def detail_frozenset(v, depth = 0):
	out = set()
	for item in v:
		out.add( detail_any(item, depth = depth + 1) )
	return frozenset(out)
	
def detail_dict(v, depth = 0):
	out = {}
	for key, value in v.iteritems():
		n_key = detail_any(key, depth = depth + 1)
		n_value = detail_any(value, depth = depth + 1)
		out[ n_key ] = n_value
	return out

def _attr_atom(attr_group, attr_value):
	return ["@%s"%(attr_group), attr_value]
def detail_obj(v, depth = 0):
	out = {CLASS_TAG: v.CLASS_TAG}
	depth += 1
	for group_name in ("BASE", "CODE", "TMP", "TABLE", "FORMULA"):
		g = getattr(v.__class__, group_name)
		for attr_name in g.iterkeys():
			attr_value = getattr(v, attr_name)
			out[attr_name] = _attr_atom(group_name, detail_any(attr_value, depth))
	
	return out

DETAIL_HANDLERS = {
str: detail_simple,
unicode: detail_simple,
int: detail_simple,
long: detail_simple,
float: detail_simple,
type(None): detail_simple,
bool: detail_simple,

list: detail_list,
tuple: detail_tuple,
dict: detail_dict,
CIntDict: detail_dict,
set: detail_set,
frozenset: detail_frozenset,

OBJ_TYPE: detail_obj,
}

# =========公开函数=========
# dump函数：将一个python容器dump成明文py
def dump(value):
	buf = []
	def write_func(msg):
		buf.append(msg)
	
	dump_any(value, write_func)
	return "".join(buf)


# =========不公开函数============
def DUMP_TYPE(v):
	raw_type = type(v)
	if raw_type in COMPLEX_TYPES:
		return raw_type
	else:
		raise Exception("unsupport data type: %s"%(raw_type))

def ASSERT_TYPE(t, errormsg):
	global DUMP_HANDLERS
	if t not in DUMP_HANDLERS:
		raise Exception("%s: %s"%(errormsg, t))

def dump_any(v, write_func, depth = 0):
	global DUMP_HANDLERS
	DUMP_HANDLERS[DUMP_TYPE(v)](v, write_func, depth)

def dump_simple(v, write_func, depth = 0):
	write_func("%s"%(str(v)))

R_TAG = "@RESERVED|" # 当一个字符串以R_TAG起始时，序列化时不需要字符串起始结束符
def dump_str(v, write_func, depth = 0):
	if v.startswith(R_TAG):
		write_func("%s"%(v[len(R_TAG):]))
	else:
		write_func("'''%s'''"%(v))

def dump_unicode(v, write_func, depth = 0):
	write_func("'''%s'''"%(v.encode("gbk")))

def _dump_sequence(v, write_func, depth = 0, start = "(", stop = ")"):
	write_func(start)
	
	for obj in v:
		dump_any(obj, write_func, depth=depth+1)
		
		# ,
		write_func(", ")
	
	write_func(stop)
	
def dump_list(v, write_func, depth = 0):
	_dump_sequence(v, write_func, depth=depth, start = "[", stop = "]")
def dump_tuple(v, write_func, depth = 0):
	_dump_sequence(v, write_func, depth=depth, start = "(", stop = ")")
def dump_set(v, write_func, depth = 0):
	_dump_sequence(v, write_func, depth=depth, start = "set((", stop = "))")
def dump_frozenset(v, write_func, depth = 0):
	_dump_sequence(v, write_func, depth=depth, start = "frozenset((", stop = "))")
	
def dump_dict(d, write_func, depth = 0):
	global PROCESSER_MAP
	
	tabs = "\t" * depth
	
	write_func("{\n")
	for key, value in d.iteritems():
		# tabs
		write_func(tabs)
		
		# processing key
		key_type = type(key)
		ASSERT_TYPE(key_type, "key type not support")
		dump_any(key, write_func, depth=depth+1)

		# :
		write_func(": ")
		
		# write value
		value_type = type(value)
		ASSERT_TYPE(value_type, "value type not support")
		dump_any(value, write_func, depth=depth+1)
		
		# ,
		write_func(",\n")
	
	write_func("%s}"%(tabs))

	
DUMP_HANDLERS = {
str: dump_str,
unicode: dump_unicode,
int: dump_simple,
long: dump_simple,
float: dump_simple,
type(None): dump_simple,
bool: dump_simple,

list: dump_list,
tuple: dump_tuple,
dict: dump_dict,
set: dump_set,
frozenset: dump_frozenset,
}	

try:
	import w_c_serialize_XXX
	nor_any = w_c_serialize.normalize
	recover_any = w_c_serialize.recover
	safecopy = w_c_serialize.safecopy
	set_base = w_c_serialize.set_base
	rebuild_all_attr = w_c_serialize.rebuild_all_attr
except ImportError, e:
	
	import copy
	safecopy = copy.deepcopy
	
	set_base = None
	rebuild_all_attr = None

# dumps和loads函数，将一个python容器进行二进制的序列化/反序列化
try:
	import msgpack
	dumps = msgpack.dumps
	loads = msgpack.loads
except ImportError, e:
	dumps = None
	loads = None


# 当v为coreobj 或 包含有coreobj时
def dumps_with_coreobj(v):
	return dumps(nor_any(v))

# 当s为适应dumps_with_coreobj得出时，需要用这个恢复字典
def loads_with_coreobj(s):
	import x_coreobj_base
	nor_v = loads(s, use_list=True)
	return recover_any(nor_v, x_coreobj_base.ALL_SAVE_CLASS_DICT)
	
def save_to_py_string(v):
	nor_v = nor_any(v)
	return dump(nor_v)

# test code
if __name__ == "__main__":
	a = {
		1: (1, 2, 3, {"k": 1}),
		"name": "wtf",
		"reserved": R_TAG + "1",
		(1, 2, 3): [4, 5, 6],
		1.234: 5.678,
		"None?": None,
		"Yes": True,
		"No": False,
		"long": long(1),
		"set1": set([1, 2]),
		"set2": frozenset(set([1, 2])),
		}
	print "dump: %s\n"%dump(a)
	print "detail_any: %s\n"%(detail_any(a))
	
	b = {
		1: [1, 2, 3, {"k": 1}],
		"name": "wtf",
		1.234: 5.678,
		"None?": None,
		"Yes": True,
		"No": False,
		"long": long(1),
		}	
	print "nor_any: %s\n"%(nor_any(b))
