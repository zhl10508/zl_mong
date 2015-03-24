# $Id: x_coreobj_base.py 165791 2014-12-10 03:52:31Z akara@NETEASE.COM $
# -*- coding: gbk -*-
import sys
import os
import x_serialize

CONSTS_TYPES = set([int, long, str, float, bool, list, type(None), unicode])

# opts
type = type
getattr = getattr
setattr = setattr
property = property

ALL_SAVE_CLASS_DICT = {}
		
COREOBJ_CLASS_ATTR_TUPLE = ("BASE", "CODE", "TMP", "TABLE", "FORMULA", 
	"ATTR_VISIBILITY_INFO", "VISIBILITY_TO_ATTRS", "ATTR_EDITABLE_INFO", "ATTR_DIRTY_INFO",
	"BASE_DATATYPE")		
		
class Meta(type):

	def __init__(cls, name, bases, attrs):
		# 每个cls的定义独立
		for n in COREOBJ_CLASS_ATTR_TUPLE:
			orgi_v = getattr(cls, n)
			new_v = x_serialize.safecopy( orgi_v )
			
			# 以派生类优先原则，将基类相关定义k/v补回
			for base_cls in bases:
				b_v = getattr(base_cls, n, None)
				if b_v is not None:
					for k, v in b_v.iteritems():
						if k not in new_v:
							new_v[k] = x_serialize.safecopy(v)
							#print "%s 自动补回了基类 %s.%s 的定义 %s = %s"%(cls, 
							#	base_cls, n, k, str(new_v[k]))
			
			setattr(cls, n, new_v)
			
		# 检查BASE/CODE/TMP的value，不允许mutable的对象
		for d in (cls.BASE, cls.CODE, cls.TMP):
			for v in d.itervalues():
				if type(v) not in CONSTS_TYPES:
					raise Exception("BASE/CODE/TMP defaults MUST be immuatable! '%s'(%s) is invalid!"%(str(type(v)), str(v)))
			
		cls.refresh_all_reg_attrs()
		
		super(Meta, cls).__init__(name, bases, attrs)

# 属性类的基类
class CObj(object):

	# 定义本类型对象的存盘标记
	CLASS_TAG = "_attrobj_base_"

	# 定义本类型对象的xls配置属性
	#（自动填充下面的 COREOBJ_CLASS_ATTR_TUPLE ）
	# None表示无相关xls补充
	PATCH_MODULE_NAME = None	
	
	################################################################
	# Meta类对以下 COREOBJ_CLASS_ATTR_TUPLE中的几个字典做了特殊处理：
	# 它们的定义是支持继承特性的
	################################################################
	# format: {attrname : default_value}
	BASE = {"_id": 0, }
	# format: {attrname : default_value}
	CODE = {}
	# format: {attrname : default_value}
	TMP = {}
	# format: {attrname: (name, depend_attr_name,the_table), ...}
	TABLE = {}
	# format: {attrname: module_name, }
	FORMULA = {}
	
	# format: {attrname: 0/1/2/.., }
	ATTR_VISIBILITY_INFO = {}
	# format: {1: [attrname_1, attrname_2, ..], 2: [attrname_3, ..]}
	VISIBILITY_TO_ATTRS = {}
	# format: {attrname: True/False, }
	ATTR_EDITABLE_INFO = {}
	# format: {attrname: [attrname_1, attrname_2, ...], }
	ATTR_DIRTY_INFO = {}
	# format: {attrname: type_name_string, ...}
	BASE_DATATYPE = {"_id": "uint64"}
	
	#######################################
	__metaclass__ = Meta
	#######################################
	
	def __init__(self):
		
		self._base_ = {}
		self._code_ = {}
		self._tmp_ = {}
		self._table_ = {}
		self._formula_ = {}
		
		self._is_attr_dirty_ = True
		
	# 根据存盘字典，恢复所有基础属性的_base_字典（包括class实例的属性）
	# 并填充_tmp_为默认值
	def set_base(self, base):
		if (type(base) != dict):
			raise Exception("[%s] must load from a dict"%(self.CLASS_TAG))

		# 根据存盘数据，设基础属性的key/value
		_BASE = self.__class__.BASE
		_base_ = self._base_
		for k, v in base.iteritems():
			if k in _BASE:
				_base_[k] = v
			else:
				pass
				#if __debug__:
				#	print "自动跳过当前不支持的BASE的key：%s"%(k)
		
		# 存盘数据中没有的基础属性key，使用默认值填充
		for k, v in _BASE.iteritems():
			if k not in self._base_:
				_base_[k] = v
			
		# 填充代码属性的默认值
		_code_ = self._code_
		for k, v in self.__class__.CODE.iteritems():
			_code_[k] = v
			
		# 计算并刷新所有属性
		self.rebuild_all_attr()			

	# =======================================================
	# 将存盘内容保存成dumps后的dict
	# 通常用于server服务器存盘
	def save_to_string(self):
		return x_serialize.dumps_with_coreobj(self._base_)	
	
	# 从一个用save_to_string接口生成的string中，
	# 递归恢复成base（这个base字典里面已经自动生成了所有sub coreobjs）
	def get_base_from_string(self, s):
		return x_serialize.loads_with_coreobj(s)
	# =========================================================

	def save_to_dict(self):
		return x_serialize.nor_any(self._base_)

	def get_base_from_dict(self, d):
		return x_serialize.recover_any(d, ALL_SAVE_CLASS_DICT)

	def create_int_dict(self, *args, **kwargs):
		return x_serialize.CIntDict(*args, **kwargs)
	
	############################################################
	# 将存盘内容保存成py语法的文本
	# 通常用于场景或地图格式的保存
	def save_to_py_string(self):
		return x_serialize.save_to_py_string(self._base_)
	
	# 从一个字典中递归恢复成base（这个base字典里面已经自动生成了所有sub coreobjs）
	def get_base_from_normalize_dict(self, d):
		return x_serialize.recover_any(d, ALL_SAVE_CLASS_DICT)
	###########################################################		

	# 本函数调用完，才算是真正可用的对象
	def on_create(self, base=None):
		if base is None: 
			base = {}
		if x_serialize.set_base is not None:
			x_serialize.set_base(self, base)
		else:
			self.set_base(base)
		self.rebuild_all_attr()
	
	def destroy(self):
		pass
		
	def rebuild_all_attr(self):
		if x_serialize.rebuild_all_attr is not None:
			return x_serialize.rebuild_all_attr(self)

		#########todo: delte codes below###############
			
		# 不脏的不用rebuild
		if not self._is_attr_dirty_:
			return
	
		# 设置临时属性的默认值
		for k, v in self.__class__.TMP.iteritems():
			self._tmp_[k] = v

		# 获取装备加成的临时属性值，并加到原有的TMP default上
		for k, v in self.get_addon_attrs_to_self().iteritems():
			if k in self.__class__.TMP:
				self._tmp_[k] += v
				#if self._tmp[k] < 0:
				#	self._tmp[k] = 0
			else:
				raise Exception("unsupported tmp attr name：%s"%(k))
	
		# 重算查表属性
		for name in self.__class__.TABLE:
			self._table_[name] = getattr(self, name)
		
		# 重算公式属性
		for name in self.__class__.FORMULA:
			self._formula_[name] = getattr(self, name)
		
		self._is_attr_dirty_ = False	
		
		
	@classmethod
	def refresh_all_reg_attrs(cls):
		# 开始填充xls模块属性
		if cls.PATCH_MODULE_NAME is not None:
			cls.reg_attr_by_module_name(cls.PATCH_MODULE_NAME)
		
		# 尝试注册save cls
		cls.try_reg_save_class()
		
		# 注册全部属性的proporty
		for k, v in cls.BASE.iteritems():
			cls.reg_base_attr(k, v)
		for k, v in cls.CODE.iteritems():
			cls.reg_code_attr(k, v)
		for k, v in cls.TMP.iteritems():
			cls.reg_tmp_attr(k, v)
		for k, v in cls.TABLE.iteritems():
			name, depend_attr_name,the_table = v
			cls.reg_table_attr(k, name, depend_attr_name, the_table)
		for k, v in cls.FORMULA.iteritems():
			cls.reg_formula_attr(k, v)		
		
	# 根据导表模块，注册几种类型的属性
	@classmethod
	def reg_attr_by_module_name(cls, module_name):
		module = __import__(module_name)
		data = module.DATA

		cls.BASE.update(data["base_default"])
		cls.CODE.update(data["code_default"])
		cls.TMP.update(data["tmp_default"])
			
		for name in data["table"]:
			info = data["table_attr_info"][name]
			depend_sheet_name = info["sheet"]
			if isinstance(info["key"], basestring):
				depend_attr_name = data["all"][info["key"]]
			else:
				depend_attr_name = (data["all"][info["key"][0]], data["all"][info["key"][1]])
			the_table = data["table_sheets"][depend_sheet_name]
			attr_name = data["all"][name]
			
			cls.TABLE[attr_name] = (name, depend_attr_name,the_table)

		for name in data["formula"]:
			attr_name = data["all"][name]
			cls.FORMULA[attr_name] = data["formula_module"]
			
		# 引用可见性信息
		cls.ATTR_VISIBILITY_INFO = data["attr_visibility_info"]
		cls.VISIBILITY_TO_ATTRS = data["visibility_to_attrs"]
		# 引用可编辑信息
		cls.ATTR_EDITABLE_INFO = data["attr_editable_info"]
		# 引用dirty信息
		cls.ATTR_DIRTY_INFO = data["attr_dirty_info"]
		# 引用存盘数据类型信息
		cls.BASE_DATATYPE = data["base_datatype"]

	# 尝试注册save cls
	@classmethod
	def try_reg_save_class(cls):
		# 不允许不同的cls定义相同的CLASS_TAG
		if cls.CLASS_TAG in ALL_SAVE_CLASS_DICT:
			the_exist_cls = ALL_SAVE_CLASS_DICT[cls.CLASS_TAG]

			file_a = os.path.abspath(sys.modules[the_exist_cls.__module__].__file__)
			file_b = os.path.abspath(sys.modules[cls.__module__].__file__)

			# 3种后缀视为同样
			def __remove_py_postfix(filename):
				py_postfixs = (".py", ".pyc", ".pyo")
				for postfix in py_postfixs:
					if filename.endswith(postfix):
						filename = filename[:-len(postfix)]
						break
				return filename

			file_a = __remove_py_postfix(file_a)
			file_b = __remove_py_postfix(file_b)

			if file_a != file_b:
				raise Exception("%s.CLASS_TAG[%s] == %s.CLASS_TAG!"%(\
					cls, cls.CLASS_TAG, the_exist_cls))
		
		ALL_SAVE_CLASS_DICT[cls.CLASS_TAG] = cls
		return True		
		
	# 注册基础属性
	@classmethod
	def reg_base_attr(cls, name, default_value=None):
		global ALL_SAVE_CLASS_DICT
	
		def _get(self):
			return self._base_[name]
		
		if name in cls.ATTR_DIRTY_INFO:
			def _set(self, v):
				self._base_[name] = v
				self._is_attr_dirty_ = True
		else:
			def _set(self, v):
				self._base_[name] = v

		setattr(cls, name, property(_get, _set))

	# 注册代码属性
	@classmethod
	def reg_code_attr(cls, name, default_value):
		def _get(self):
			return self._code_[name]
		def _set(self, v):
			self._code_[name] = v
			#代码属性因为变动频率非常大，所以不参与rebuild体系
			#self._is_attr_dirty_ = True

		setattr(cls, name, property(_get, _set))
		
	# 注册临时属性
	@classmethod
	def reg_tmp_attr(cls, name, default_value):
		def _get(self):
			return self._tmp_[name]
		
		# tmp属性用于装备和buff体系，不接受set语义
		# 只能通过addon的属性集，在rebuild_all_attr时叠加
		setattr(cls, name, property( _get ))

	# 注册查表属性
	@classmethod
	def reg_formula_attr(cls, name, formula_module_name):
		formula_name = "get_%s"%(name)
		formula_module = __import__(formula_module_name)
		f = getattr(formula_module, formula_name)
		
		def _get(self):
			if self._is_attr_dirty_:
				return f(self)
			else:
				return self._formula_[name]
		
		setattr(cls, name, property( _get ))
		
	# 注册公式属性
	@classmethod
	def reg_table_attr(cls, name, ch_name, depend_attr_name, the_table):
		def _get1(self):
			if self._is_attr_dirty_:
				depend_v = getattr(self, depend_attr_name)
				return the_table[depend_v][ch_name]
			else:
				return self._table_[name]
		def _get2(self):
			if self._is_attr_dirty_:
				depend_v1 = getattr(self, depend_attr_name[0])
				depend_v2 = getattr(self, depend_attr_name[1])
				return the_table[depend_v1][depend_v2]
			else:
				return self._table_[name]
		if isinstance(depend_attr_name, basestring):
			_get = _get1
		else:
			_get = _get2
		setattr(cls, name, property(_get))
	
	def detail(self):
		return x_serialize.dump(x_serialize.detail_any(self))
	
	# 可见性：frozenset([v_tag_1, v_tag_2, ...])
	# 如果xls中没有某个属性（即是说这个属性是代码定义的，则统一返回 None）
	def get_attr_visibility(self, attr_name):
		return self.__class__.ATTR_VISIBILITY_INFO.get(attr_name, None)
	
	# 得到某个可见性等级的属性集合
	def get_attrs_by_visiblity(self, visibility):
		attr_name_list = self.__class__.VISIBILITY_TO_ATTRS.get(visibility, None)
		if attr_name_list is None:
			return {}
		attrs = {}
		for attr_name in attr_name_list:
			attrs[attr_name] = getattr(self, attr_name)
		return attrs
	
	# 可编辑
	def get_attr_editable(self, attr_name):
		return self.__class__.ATTR_EDITABLE_INFO.get(attr_name, False)
	
	# 派生类如果需要支持装备系统，则需要重写本函数，
	# 返回【当前所有装备的所有key的对应加成值】。
	# 比如，身上总共穿着 A(临时敏捷+1, 临时力量+2)，B(临时智力+1, 临时力量+3)两件装备，
	# 则应该返回： {"tmp_dex": +1, "tmp_str": +2+3, "tmp_int": +1}
	def get_addon_attrs_to_self(self):
		return {}
	
	# 不加成到自身，但是用于加成到本对象的宿主
	# 常用方式是 get_addon_attrs_to_self 中，迭代所有的装备，
	# 对每个装备调用 get_addon_attrs_to_host() ，然后汇总结果返回。
	def get_addon_attrs_to_host(self):
		return {}

		
	######################################################################
	# 中文名(ch)，显示名(show_name)，英文名(en)，编号(num) 四者之间的转换API
	######################################################################
	@classmethod
	def _load_num_module(cls):
		if cls.PATCH_MODULE_NAME is None:
			raise Exception("must have PATCH_MODULE_NAME to use this method")
		return __import__(cls.PATCH_MODULE_NAME + "_num")
	
	@classmethod
	def num_2_en(cls, num):
		num_module = cls._load_num_module()
		return num_module.NUM_2_EN[num]
	
	@classmethod
	def en_2_num(cls, en):
		num_module = cls._load_num_module()
		return num_module.EN_2_NUM[en]
	
	@classmethod
	def en_2_ch(cls, en):
		num_module = cls._load_num_module()
		return num_module.EN_2_CH[en]
	
	@classmethod
	def en_2_show_name(cls, en):
		num_module = cls._load_num_module()
		return num_module.EN_2_SHOW_NAME[en]
	
	######################################################################
	# 根据num直接get/set对象的值
	######################################################################
	def get_attr_value_by_attr_num(self, num):
		return getattr(self, self.__class__.num_2_en(num))
		
	def set_attr_value_by_attr_num(self, num, value):
		en = self.__class__.num_2_en(num)
		setattr(self, en, value)
		
	#######################################################################
	# 根据xls配置的格式化参数，来格式化一个属性的值显示方式。比如0.2显示成"20%"
	#######################################################################
	@classmethod
	def format_attr(cls, attr_name, attr_value):
		num_module = cls._load_num_module()
		return num_module.format_attr(attr_name, attr_value)
