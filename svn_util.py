# -*- coding: utf-8-*-
import subprocess
import  config

class DiffResult(object):

    def __init__(self, old_rev, new_rev):
        self.old_rev = old_rev
        self.new_rev = new_rev
        self.blocks = {}
        # blocks 格式
        # { 'filename(e.g. /foo/bar/baz.py)': [ DiffBlocks ] }
        self.diff_info = {}
        # diff_info 格式：
        # { 'filename(e.g. /foo/bar/baz.py)': { 'A': [38,71,72,105,106,107,108], 'D': [38,99,100] } }
        # 'A' 表示新添加的行在新版本中的行号
        # 'D' 表示删除的行在旧版本中的行号（暂时不会用到，先记录下来以后没准用到）
        self.cur_filename = None
        self.cur_block_id = -1
        self.cur_block = None   # 指向当前快的快捷指针
        self.line_num = -1  # 当前处理的这一行代码再新版本代码中的行号
        #self.line_num2 = -1  # 当前处理的这一行代码在旧版本代码中的行号

    def new_file(self, filename):
        """
        开始处理一个新文件的Diff
        """
        self.diff_info[filename] = { 'A': [], 'D': [],'A_info':{},'D_info':{} }
        self.blocks[filename] = []
        self.cur_filename = filename

    def new_block(self, from_line, to_line, from_line2, to_line2):
        """
        开始处理一个新块
        from_line, to_line为该块在新版本代码中的起始行号和终止行号，
        from_line2, to_line2为该块在旧版本代码中的起始行号和终止行号
        """
        if self.cur_filename:
            new_block = DiffBlock(from_line, to_line)
            block_id = len(self.blocks[self.cur_filename])     # block id依次递增，0、1、2、3……
            self.blocks[self.cur_filename].append(new_block)
            self.cur_block_id = block_id
            self.cur_block = new_block
            self.line_num = from_line
            self.line_num2 = from_line2
        else:
            print "[Error] block is not in any file."

    def process_line(self, line):
        """
        处理当前代码行
        """
        if self.cur_filename and self.cur_block_id >= 0:
            try:
              line = line.decode('gbk').encode('utf8')
            except:
              line = line
            if line.startswith('+'):
                self.diff_info[self.cur_filename]['A'].append(str(self.line_num))
                self.diff_info[self.cur_filename]['A_info'][str(self.line_num)] = line
                self.line_num += 1
            elif line.startswith('-'):
                self.diff_info[self.cur_filename]['D'].append(str(self.line_num2))
                self.diff_info[self.cur_filename]['D_info'][str(self.line_num2)] = line
                self.line_num2 += 1
            else:
                self.line_num += 1
                self.line_num2 += 1
            self.cur_block.collect(line + '\r\n')
        else:
            print "[Error] line is not in any file or block."


class DiffBlock(object):

    def __init__(self, from_line, to_line):#, from_line2, to_line2):    是否需要存代码块在旧版本中的起始和结束行号？
        self.from_line = from_line
        self.to_line = to_line
        self.content = ""

    def collect(self, line):
        self.content += line

    def display(self):
        print "[ %d, %d ]" % (self.from_line, self.to_line)
        print self.content


def process_diff(diff_str, old_rev, new_rev):
    """ 处理svn diff的文本结果，转化为字典结构。 """
    diff_res = DiffResult(old_rev, new_rev)
    cur_filename = None
    cur_block_id = None
    in_block = False

    lines = diff_str.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].rstrip('\r')  # remove trailing CR if any
        #print line
        if line.startswith("Index: ") and lines[i+1] == "===================================================================":
            #print "[Debug] proc new file"
            # 新的文件开始
            filename = line[7:]  # skip the beginning "Index: "
            #print filename
            diff_res.new_file(filename)
            i += 3  # skip the next two lines (=====... & --- filename ... & +++ filename ...)
        elif line.startswith("@@") and line.endswith("@@"):
            #print "[Debug] proc new block"
            # 新的块开始
            line = line.strip("@@")
            parts = line.split()
            line_n_cnt = parts[0][1:]
            if ',' in line_n_cnt:
                from_line, line_cnt = line_n_cnt.split(',')
            else:
                from_line = line_n_cnt
                line_cnt = 1
            from_line = int(from_line)
            line_cnt = int(line_cnt)
            to_line = from_line + line_cnt
            line_n_cnt = parts[1][1:]
            if ',' in line_n_cnt:
                from_line2, line_cnt2 = line_n_cnt.split(',')
            else:
                from_line2 = line_n_cnt
                line_cnt2 = 1
            from_line2 = int(from_line2)
            line_cnt2 = int(line_cnt2)
            to_line2 = from_line2 + line_cnt2
            diff_res.new_block(from_line2, to_line2, from_line, to_line)
        else:
            # 处理当前代码行
            #print line
            diff_res.process_line(line)
        i += 1

    return diff_res

def process_diff_file(diff_file, old_rev, new_rev):
    """ 处理svn diff结果文件（调用process_diff）。 """
    f = open(diff_file)
    content = f.read()
    f.close()
    return process_diff(content, old_rev, new_rev)


#---------------------------------------------------
#SVN log
#给定svn的log文件地址
NEW_LINE = '\n'

def get_svnlog(log_path):
  f = open(log_path, 'r')
  content = f.read()
  f.close()
  return process_log(content)

def process_log(content):
  logs = []
  all = content.split("------------------------------------------------------------------------")
  for entry in all:
    log = {}
    lines = entry.split(NEW_LINE)[1:]
    if len(lines) <= 3:
      continue
    parts = lines[0].split('|')
    log['rev'] = int(parts[0].strip()[1:])   # remove the beginning 'r'
    log['author'] = parts[1].strip()
    log['date'] = parts[2].strip()
    log['date'] = ' '.join(log['date'].split()[:2])
    log['files'] = []
    i = 2
    for line in lines[2:]:
      if line == '':
        break
      parts = line.split()
      onefile = {}
      onefile['status'] = parts[0]
      onefile['path'] = parts[1]
      log['files'].append(onefile)
      i = i + 1
    log['comment'] = NEW_LINE.join(lines[i+1:]).decode('utf-8')
    logs.append(log)
  return logs

#----------------------------------------------------------
# SVN Methods
#----------------------------------------------------------
#game_id 为key，c开头为client，s开头为server
def get_svn_url(game_name):
    svn_url = config.CG_SVN_URL[game_name]
    return svn_url
# get customized env
def get_env():
  import os
  env = os.environ.copy()
  env['LC_ALL'] = 'zh_CN.UTF-8'
  return env

#给定游戏的key，生成的a到b的diff
def svn_diff(game_name, old_rev, new_rev,svn_url=None):
    if not svn_url:
      svn_url = get_svn_url(game_name)
    diff_filename = config.TMP_DIR + "/diff_tmp.txt"
    diff_res_file = open(diff_filename, "w")
    ret = subprocess.call(["svn", "diff", svn_url, "-r", "%s:%s" % (old_rev, new_rev)], stdout=diff_res_file)
    assert ret == 0, "Svn diff returns non-zero. %s" % ret
    diff_res_file.close()
    return process_diff_file(diff_filename, old_rev, new_rev)

def svn_log(game_name,old_rev,new_rev="HEAD"):
  svn_url = get_svn_url(game_name)
  print svn_url
  log_filename = config.TMP_DIR+"/log_tmp.txt"
  log_res_file = open(log_filename,"w")
  log_ret = subprocess.call(["svn","log",svn_url,"-v","-r","%s:%s"%(old_rev,new_rev)],stdout=log_res_file,env=get_env())
  assert log_ret==0,"Svn log returns non-zero.%s"%log_ret
  log_res_file.close()
  return get_svnlog(log_filename)

if __name__ == "__main__":
  proj = "tdg_server"
  #diff = svn_diff(proj,165207,165208)
  log = svn_log(proj,174800)
  print log
