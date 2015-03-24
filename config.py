# -*- coding:utf8 -*-

import sys
sys.path.append('lib')
sys.path.append('obj')

import obj_proj
import obj_logs_info
import obj_diffs_info

#mongdb的配置
DB_config={'IP':"192.168.10.154",
      'PORT':27017,
      'DBUSER':'zltest',
      'DBPWD':'zltest',
      'DBNAME':'zlmongo',
      'POOLSIZE':100,
    }

#默认数据库的名字tag
DEFAULT_DB_TAG = "DB_GATE"

#默认表的列表
OBJ_CLASS_LIST =  [
	obj_proj.CObj,
    obj_logs_info.CObj,
    obj_diffs_info.CObj,
]

# CG Config
PREPROCESS_GAME_IDS = ['tdg_server']

CG_SVN_URL ={
    'tdg_server':"https://svn-cg.gz.netease.com/cggame/src/66-tdg/server/",
    }

CG_LOG_START = {
    'tdg_server':"/cggame/src/66-tdg/server/",
    }

CG_SVN_PATH = "/home/zhangle/diff_tdg/cgsrc2"

TMP_DIR = "tmp/"
CVG_DIR = "cvg/"
