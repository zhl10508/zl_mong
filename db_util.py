# -*- coding:utf8 -*-
import os, sys
import traceback
import cPickle
import time
import db_mongo



g29_path = ['/home/chroot_env/home/popogame/cgame_servers/game50330/game/','/home/chroot_env/home/popogame/cgame_servers/cgsdk_mobile/']



#-----------------------------------
#对外接口
#--------------------------------
#取某个项目的当前版本
def get_proj_version(proj):
  obj =db_mongo.proj_find(proj)
  return obj.rev

def set_proj_version(proj,rev):
  obj = db_mongo.proj_find(proj,rev)
  return obj.rev

#存日志.logs为数组
def save_logs(proj,logs):
  for onelog in logs:
    rev = onelog['rev']
    db_mongo.logs_find(proj,onelog['rev'],0,onelog)
  return rev

#查日志,返回数组
def get_logs(proj,start_rev,end_rev=0):
  result = db_mongo.logs_find(proj,start_rev,end_rev)
  return result

#存diff信息
def save_diffs(proj,file_name,rev,diff_info):
  onediff={}
  onediff['proj']= proj
  onediff['rev'] = rev
  onediff['filename'] = file_name
  onediff['diffinfo'] = diff_info
  obj = db_mongo.diffs_find(proj,file_name,rev,0,onediff)
  return obj



#查询某个文件的diffdict，key:A,D,A_info,D_info,A是在新的版本，D是旧的版本
def get_filediff(proj,file_name,rev):
  obj = db_mongo.diffs_find(proj,file_name,rev)[0]
  diffdict = obj.save_to_dict()
  return diffdict

#-----------------------------------
#处理covinfo
####################

def del_startpath(oneinfo,start_path):
    result = {}
    for key in oneinfo.keys():
      for onestart_path in start_path:
        if key.startswith(onestart_path):
            onekey = key.replace(onestart_path,'')
            result[onekey]=oneinfo[key]
    return result

#给定proj和版本号，返回数组,result[rev]=[oneinfo,oneinfo],oneinfo=dict{}
def get_allcvginfo(proj,version,end_ver=0):
    if end_ver==0:
        end_ver=version
    sql="""select * from """+cvg_table+""" where proj='"""+proj+"""' and version BETWEEN """+str(version)+""" AND """+str(end_ver)
    sums,cds = select(sql)
    result = {}
    if sums>0:
        for i in range(sums):
            oneproj = cds[i][0]
            oneversion = cds[i][1]
            onestart_time = cds[i][2]
            onemsg = cds[i][3]
            oneupdate_time = cds[i][4]
            oneinfo = {}
            oneinfo['proj']=oneproj
            oneinfo['version']=oneversion
            oneinfo['start_time']=onestart_time
            oneinfo['info']=del_startpath(cPickle.loads(str(onemsg)),g29_path)
            oneinfo['update_time']=oneupdate_time
            if oneversion in result.keys():
              result[oneversion].append(oneinfo)
            else:
              result[oneversion] = [oneinfo]
    return result

#给定proj和版本号，返回字典result[rev]={file:line}
def get_cvginfo(proj,version,end_ver=0):
  all_cvginfo = get_allcvginfo(proj,version,end_ver)
 # print type(all_cvginfo)
  result = {}
  for onekey in all_cvginfo.keys():
    one_cvginfos = all_cvginfo[onekey]
 #   print onekey,type(one_cvginfos)
    one_info = {}
    for one_cvginfo in one_cvginfos:
      oneinfo = one_cvginfo['info']
      if one_info:
        for okey in oneinfo.keys():
          #w文件是否存在
          if okey in one_info.keys():
            #合并行
            onefile_info = one_info[okey]
            addfile_info = oneinfo[okey]
            for oneline in addfile_info.keys():
              if oneline in onefile_info.keys():
                onefile_info[oneline] = onefile_info[oneline] + addfile_info[oneline]
              else:
                onefile_info[oneline] = addfile_info[oneline]
            one_info[okey] = onefile_info
          else:
            one_info[okey] = oneinfo[okey]
      else:
        one_info = oneinfo
    print 'onekey',onekey
    result[onekey] = one_info
  return result
#################################################

############################
#--得到最新的版本覆盖信息
############################
def save_nowcvginfo(proj,rev,info):
  sql=u"""REPLACE into """ + cvginfo_table + """ values(%s,%s,%s)"""
  para = (proj,rev,info)
  ret = save(sql,para)
  assert ret>0,"wrong in set rev"
  return ret

def get_nowcvginfo(proj):
  sql=u"""select rev,info from %s where proj="%s" """%(cvginfo_table,proj)
  summ,cds = select(sql)
  assert summ==1,"proj:%s not get_cvginfo "%(proj)
  result = {}
  result['rev'],result['info'] = cds[0]
  return result





if __name__=="__main__":
  proj="tdg_server"
  rev = get_proj_version(proj)
  print rev
  print set_proj_version(proj,174001)
  rev = 175210
  logs = get_logs(proj,rev,rev+10000)
#  print type(logs)
#  print logs[0].save_to_dict()
  file_name = "/cggame/src/66-tdg/server/tdg_room_player.py"
  import svn_util
  from config import *
  log_start = CG_LOG_START[proj]
  filepath = CG_SVN_URL[proj]+file_name.replace(log_start,'')
#  diff = svn_util.svn_diff(proj,175218,175219,filepath)
 # diff_dict = diff.diff_info
  #diffinfo = diff_dict[diff_dict.keys()[0]]
 # print diffinfo
  onediff={}
  onediff['proj']= proj
  onediff['rev'] = 175219
  onediff['filename'] = file_name
 # onediff['diffinfo'] = diffinfo
  #print db_mongo.diffs_find(proj,file_name,175219,0,onediff)
  print get_filediff(proj,file_name,175219)



#  import svn_util
#  logs = svn_util.svn_log(proj,174800)
#  print onelog[0].keys()
#  save_logs(proj,logs)

#  onediff = get_filediff(proj,file_name,rev)
#  print onediff.keys()
#  log = get_logs(proj,rev)
  #print log['comment'].encode('utf8')
 # print type(log['files'][0])


  #result = get_allcvginfo(proj,174000,175000)
  #onekey = result.keys()[0]
  #onekey_file = result[onekey][0]['info'].keys()[0]
 # print onekey_file
  #print result[onekey][0]['info'][onekey_file]

  #result = get_cvginfo(proj,174000,175000)
 # ke = result.keys()[0]
 # print result[ke].keys()




