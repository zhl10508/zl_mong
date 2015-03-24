# -*- coding: utf8 -*-

import pymongo
import uuid
from config import *
import traceback

import sys
sys.path.append('lib')
sys.path.append('obj')

global DB
DB={}
# 用于自增长的collection的名字
COUNTERS_COLLECTION = "_COUNTERS_"

def db_ini(dat):
  ip = dat['IP']
  port = int(dat['PORT'])
  size = int(dat['POOLSIZE'])
  dbname = dat['DBNAME']
  dbuser = dat['DBUSER']
  dbpwd = dat['DBPWD']
  client = pymongo.MongoClient(ip, port, max_pool_size=size)
  db = client[dbname]
  db.authenticate(dbuser, dbpwd)
  return db

def init():
  try_create_index()

def dbinit():
  db_conf = DB_config
  db = db_ini(db_conf)
  global DB
  DB['DB_GATE'] = db
#------------------------------------------------
#--database.py
#--------------------------------------------
def _gen_auto_inc_id(cls, minid=1):
  query = { "_id": cls.CLASS_TAG }
  update= { "$inc": { "seq": minid } }
  kwargs = {"query": query, "update": update, "new":True, "upsert":True}
  db_tag = _get_dbtag(cls)
  seq = _execute(db_tag, COUNTERS_COLLECTION, "find_and_modify", kwargs=kwargs)
  return seq["seq"]

def _get_dbtag(cls):
  db_tag = getattr(cls, "DB_TAG", None)
  if db_tag is None:
    db_tag = DEFAULT_DB_TAG
  return db_tag

def _execute(db_tag, collection_name, function_name, kwargs={}):
  global DB
  db = DB.get(db_tag,None)
  collection = db[collection_name]
  function = getattr(collection, function_name)
  print "[DBOPT] %(db)s[%(col)s].%(func)s(**%(kwargs)s)"\
          % {'db': db_tag, 'col': collection_name, 'func': function_name, 'kwargs': kwargs}
  return function(**kwargs)

def _execute_by_clstag(cls, function_name, kwargs={}):
  db_tag = _get_dbtag(cls)
  collection_name = cls.CLASS_TAG
  return _execute(db_tag, collection_name, function_name, kwargs)

# 删除整张表格
def drop_collection(cls):
  _execute_by_clstag(cls, "drop")

# 创建index
def try_create_index():
  for cls in OBJ_CLASS_LIST:
    # TODO: 对比新旧index, 已有了的index,如果没有变化,则不create_index
    # old_index_info = _execute_by_clstag(context, cls, "index_information")
    for name, cnf in cls.INDEX_CONFIG.iteritems():
      kwargs = {
          "name": name,
          "key_or_list": cnf["keylist"],
          "unique": cnf["unique"],
          }
      _execute_by_clstag(cls, "ensure_index", kwargs)

# 保存obj
def save(obj):
  if (not obj._id):
    if obj.ID_NEED_AUTO_INC:
      obj._id = _gen_auto_inc_id(obj)
    else:
      obj._id = uuid.uuid4().hex
  base = obj.save_to_dict()
  query = {"_id": base["_id"]}
  update = {"$set":base}
  ret = _execute_by_clstag(obj,
          "update", {"spec": query, "document": update, "upsert":True})
  return ret

# 查询一批
def find_objs(cls, kwargs={}):
  objlist = []
  cursor = _execute_by_clstag(cls, "find", kwargs)
  for dct in cursor:
    obj = cls()
    obj.on_create(dct)
    objlist.append( obj )
  return objlist

def remove(obj):
  if obj._id:
    args = {"spec_or_id":obj._id}
    ret = _execute_by_clstag(obj,"remove", args )
    return ret
  else:
    print "obj has not _id. cannot remove obj:%s"%obj

# 查找1调记录,
# create=True:如果不存在,则创建一个新的对象
def find_one_obj(cls, kwargs, create):
  objlist = find_objs(cls, kwargs)
  if objlist:
    obj = objlist[0]
  elif create:
    obj = cls()
    base = {}
    if obj.ID_NEED_AUTO_INC:
      base["_id"] = _gen_auto_inc_id(cls)
    obj.on_create(base)
  else:
      obj = None
  return obj

####################################################################
#给定obj的文件名，id，要寻找的key
def find(cls,_id,find_key='_id'):
  kwargs = {'spec': {find_key: _id}}
  import sys
  cobj_module = sys.modules.get(cls)
  cobj = getattr(cobj_module,'CObj')
  try:
    obj = find_one_obj(cobj,kwargs,False)
    return obj
  except Exception,err:
    print 'fine cls:%s,err:%s,_id:%s' %(cls,err,str(_id))


#设置obj的——id的对应的key和data
def update(cls,_id,set_data,find_key='_id'):
  obj = find(cls,_id,find_key)
  import sys
  cobj_module = sys.modules.get(cls)
  cobj = getattr(cobj_module,'CObj')
  query = {"_id":_id}
  update = {"$set":set_data}
  ret = _execute_by_clstag(cobj,"update",{"spec":query,"document":update,"upsert":True})
  return ret

#没有obj的，表查找
#kwargs = {'spec': {'_id': 1}}
#cursor = db_find('DB_GATE','role','find',kwargs)
def db_find(db_tag,table_name,cmd,kwargs):
  cursor = _execute(db_tag,table_name,cmd,kwargs)
  return cursor


################################################################
#-----svn diff interface
###############################################
def call_find(cls,args_dict,find_data):
  pass

#查询表的数据,不存在就新建
def proj_find(proj,rev=0):
  obj = find('obj_proj',proj,find_key='proj')
  if not obj:
    obj = obj_proj.CObj()
    base = {}
    if obj.ID_NEED_AUTO_INC:
      base["_id"] = _gen_auto_inc_id(obj_proj.CObj)
    base['proj'] = proj
    base['rev'] = rev
    obj.on_create(base)
    save(obj)
  if rev:
    obj.rev = rev
    save(obj)
  return obj

def logs_find(proj,start_rev,end_rev=0,log={}):
  if end_rev==0:
    end_rev = start_rev
  kwargs = {'spec': {'proj': proj,'rev':{'$gte':start_rev,'$lte':end_rev}}}
  obj = find_objs(obj_logs_info.CObj,kwargs)
  if log :
    if not obj:
      obj = obj_logs_info.CObj()
      base = {}
      if obj.ID_NEED_AUTO_INC:
        base["_id"] = _gen_auto_inc_id(obj_logs_info.CObj)
      base['proj'] = proj
      base['rev'] = log['rev']
      base['comment'] = log['comment']
      base['author'] = log['author']
      base['files'] = log['files']
      base['date'] = log['date']
      obj.on_create(base)
      save(obj)
    else :
      for onekey,onevalue in log.items():
        setattr(obj,onekey,onevalue)
      save(obj)
  return obj

def diffs_find(proj,filename,start_rev,end_rev=0,diffs={}):
  if end_rev==0:
    end_rev = start_rev
  kwargs = {'spec': {'proj': proj,'filename':filename,'rev':{'$gte':start_rev,'$lte':end_rev}}}
  obj = find_objs(obj_diffs_info.CObj,kwargs)
  if diffs:
    if not obj:
      obj = obj_diffs_info.CObj()
      base = {}
      if obj.ID_NEED_AUTO_INC:
        base["_id"] = _gen_auto_inc_id(obj_diffs_info.CObj)
      base['proj'] = proj
      base['rev'] = diffs['rev']
      base['filename'] = diffs['filename']
      base['diffinfo'] = diffs['diffinfo']
      obj.on_create(base)
      save(obj)
    else :
      for onekey,onevalue in diffs.items():
        setattr(obj,onekey,onevalue)
      save(obj)
  return obj

dbinit()
init()


if __name__ == '__main__':
  #obj = proj_find('tdg_server','178000')
  #print type(obj)
  proj = 'tdg_server'
  rev = 1
  obj = logs_find(proj,rev)
  obj_dic = obj.save_to_dict()
  print obj_dic
