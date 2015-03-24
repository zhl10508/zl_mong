# -*- coding: utf-8-*-

import db_util
import svn_util
import config


####################################
##保存日志和数据diff
###################################

def save_svn(proj):
  #得到现在proj的版本号
  now_rev = db_util.get_proj_version(proj)
  print 'proj:%s,now_rev:%s'%(proj,str(now_rev))
  logs = svn_util.svn_log(proj,now_rev)
  if logs:
    max_rev = logs[-1]['rev']
    print 'max_rev',max_rev
    if now_rev>=max_rev:
      return
    logs=logs[1:]
    #存logs到数据库
    now_rev = db_util.save_logs(proj,logs)
    db_util.set_proj_version(proj,now_rev)
    #对于每个log，取diff文件
    for onelog in logs:
      onerev = onelog["rev"]
      modfiles = onelog["files"]
      oneproj = proj
      if modfiles:
        for onemodfile in modfiles:
          status = onemodfile["status"]
          file_path = onemodfile["path"]
          if '.' in file_path:
            log_start = config.CG_LOG_START[proj]
            if not file_path.startswith(log_start):
              continue
            filepath = config.CG_SVN_URL[proj]+file_path.replace(log_start,'')
            if status=="D" or status=="A":
              diff_info ={}
            else:
              onediff_obj = svn_util.svn_diff(proj,onerev-1,onerev,filepath)
              diff_dict = onediff_obj.diff_info
              diff_info = diff_dict[diff_dict.keys()[0]]
            db_util.save_diffs(proj,file_path,onerev,diff_info)


def save_cvg(proj):
  #得到现在proj的版本号
  cvg_proj = 'cov_'+proj
  now_rev = db_util.get_proj_version(cvg_proj)
  print 'proj:%s,now_rev:%s'%(cvg_proj,str(now_rev))
  new_cvginfo = db_util.get_cvginfo(proj,now_rev+1,now_rev+10000)
  if not new_cvginfo:
    print 'no new_cvginfo'
    return
  print 'new_cvginfo revs:',new_cvginfo.keys()
  try:
    now_cvginfo = db_util.get_nowcvginfo(proj)
  except:
    now_cvginfo = None
  print 'now_cvginfo:',type(now_cvginfo)
  if now_cvginfo:
    want_merge_cvginfo = new_cvginfo
    now_rev = now_cvginfo['rev']
    now_info = now_cvginfo['info']
    want_merge_cvginfo[now_rev,now_info]
    merge_cvginfo(proj,want_merge_cvginfo)
  else:
    merge_cvginfo(proj,new_cvginfo)

def merge_cvginfo(proj,new_cvginfo):
  rev_list = sorted(new_cvginfo.keys())
  print 'merge_cvginfo revs:',rev_list
  if len(rev_list) == 1:
    onerev = rev_list[0]
    #初始新建
    cvginfo = new_cvginfo[onerev]
    db_util.save_nowcvginfo(proj,onerev,cPickle.dumps(cvginfo))
    db_util.set_proj_version('cov_'+proj,onerev)
  else:
    now_rev =0
    now_info = {}
    for onerev in rev_list:
      if now_rev==0:
        now_rev = onerev
        now_info = new_cvginfo[onerev]
      else:
        #取svn的diff
        print 'get svnlog ',now_rev,onerev
        new_logs = db_util.get_logs(proj,now_rev,onerev)
        if not new_logs:
          print 'in merge_cvginfo no new_logs '
          now_info = merge_dict(now_info,new_cvginfo[onerev])
          now_rev = onerev
          continue
        rev_newlist = sorted(new_logs.keys())
        print 'in merge_cvginfo rev_newlist',rev_newlist
        print new_logs
        now_rev = onerev
      print now_rev
      print now_info.keys()

#将2个字典合并
def merge_dict(onedict,twodict):
  for onefile in twodict.keys():
    if onefile in onedict.keys():
      onefile_info = onedict[onefile]
      twofile_info = twodict[onefile]
      for oneline in twofile_info.keys():
        if oneline in onefile_info.keys():
          onefile_info[oneline] = onefile_info[oneline]+twofile_info[oneline]
        else:
          onefile_info[oneline] = twofile_info[oneline]
      onedict[onefile] = onefile_info
    else:
      onedict[onefile] = twodict[onefile]
  return onedict






if __name__ == "__main__":
  proj = "tdg_server"
  save_svn(proj)
  #save_cvg(proj)
  #logs = db_util.get_logs(proj,174909,180000)
  #print logs.keys()
