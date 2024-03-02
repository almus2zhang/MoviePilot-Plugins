
# MoviePilot library
from app.log import logger
from pathlib import Path
from app.plugins import _PluginBase
from app.core.event import eventmanager
from app.schemas.types import EventType
from app.utils.system import SystemUtils
from typing import Optional, Any, List, Dict, Tuple
import subprocess
import os
import shutil
import threading
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import time
import pytz
from app.core.config import settings
import paramiko

try:
    from pyparsebluray import mpls
except:
    subprocess.run(["pip3", "install", "pyparsebluray"])
    subprocess.run(["pip3", "install", "ffmpeg-python"])
try:
    import ffmpeg
except:
    logger.error("requirements 安装失败")

class BDRemuxermod(_PluginBase):
    # 插件名称
    plugin_name = "BDMV Remuxer mod"
    # 插件描述
    plugin_desc = "提取蓝光原盘目录，合并为MKV文件。修改自https://github.com/hankunyu"
    # 插件图标
    plugin_icon = ""
    # 主题色
    plugin_color = "#3B5E8E"
    # 插件版本
    plugin_version = "1.1.1"
    # 插件作者
    plugin_author = "hankun"
    # 作者主页
    author_url = "https://github.com/almus2zhang/MoviePilot-Plugins"
    # 插件配置项ID前缀
    plugin_config_prefix = "BDRemuxermod_"
    # 加载顺序
    plugin_order = 1
    # 可使用的用户级别
    auth_level = 1

    # 私有属性
    _enabled = False
    _delete = False
    _run_once = False
    _path = ""
    _temppath = ""
    _outpath = ""
    _isooutpath = ""
    _isopath = ""
    _delaymin = 0
    _scheduler: Optional[BackgroundScheduler] = None
    _mkvfile = ""
    _hostip = ""
    _hostroot = ""
    _hostpass = ""
    _hostheader = ""
    def init_plugin(self, config: dict = None):
        if config:
            self._enabled = config.get("enabled")
            self._delete = config.get("delete")
            self._run_once = config.get("run_once")
            self._path = config.get("path")
            self._temppath = config.get("temppath")
            self._delaymin = config.get("delaymin") or 0
            self._outpath = config.get("outpath")
            self._isooutpath = config.get("isooutpath")
            self._isopath = config.get("isopath")
            self._emount = config.get("emount")
            self._eumount = config.get("eumount")
            self._hostip = config.get("hostip")
            self._hostroot = config.get("hostroot")
            self._hostpass = config.get("hostpass")
            self._hostheader = config.get("hostheader")
        if self._enabled:
            self._scheduler = BackgroundScheduler(timezone=settings.TZ)
            logger.info("BD Remuxer 插件初始化完成")
            if self._run_once:
                logger.info("添加任务3秒后处理目录：" + self._path)
                self._scheduler.add_job(self.schedlerremux_sub, 'date', 
                                        run_date=datetime.now(tz=pytz.timezone(settings.TZ)) + timedelta(seconds=3),
                                        args=(self._path,))
                # 启动任务
                if self._scheduler.get_jobs():
                    self._scheduler.print_jobs()
                    self._scheduler.start()
                #thread = threading.Thread(target=self.extract, args=(self._path,))
                #thread.start()
            if self._emount:
                logger.info("添加任务3秒后挂载iso")
                self._scheduler.add_job(self.schedlerisomount, 'date', 
                                        run_date=datetime.now(tz=pytz.timezone(settings.TZ)) + timedelta(seconds=3),
                                        args=(self._isopath,self._isooutpath,))
                # 启动任务
                if self._scheduler.get_jobs():
                    self._scheduler.print_jobs()
                    self._scheduler.start()
                #thread = threading.Thread(target=self.extract, args=(self._path,))
                #thread.start()
            if self._eumount and not self._emount:
                logger.info("添加任务3秒后卸载iso")
                self._scheduler.add_job(self.schedlerisoumount, 'date', 
                                        run_date=datetime.now(tz=pytz.timezone(settings.TZ)) + timedelta(seconds=3),
                                        args=(self._isooutpath,))
                # 启动任务
                if self._scheduler.get_jobs():
                    self._scheduler.print_jobs()
                    self._scheduler.start()
                #thread = threading.Thread(target=self.extract, args=(self._path,))
                #thread.start()            
            self.update_config({
                "enabled": self._enabled,
                "delete": self._delete,
                "run_once": False,
                "path": self._path,
                "temppath": self._temppath,
                "delaymin": self._delaymin,
                "outpath": self._outpath,
                "isopath": self._isopath,
                "isooutpath": self._isooutpath,
                "emount": False,
                "eumount": False,
                "hostip": self._hostip,
                "hostroot": self._hostroot,
                "hostpass": self._hostpass,
                "hostheader": self._hostheader,
            })

    def get_state(self) -> bool:
        return self._enabled
    
        
        
    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        pass

    def get_api(self) -> List[Dict[str, Any]]:
        pass
    
    # 插件配置页面
    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        """
        拼装插件配置页面，需要返回两块数据：1、页面配置；2、数据结构
        """
        return [
            {
                'component': 'VForm',
                'content': [
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                    'md': 4
                                },
                                'content': [
                                    {
                                        'component': 'VSwitch',
                                        'props': {
                                            'model': 'enabled',
                                            'label': '启用插件',
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                    'md': 4
                                },
                                'content': [
                                    {
                                        'component': 'VSwitch',
                                        'props': {
                                            'model': 'delete',
                                            'label': '删除原始文件',
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                    'md': 4
                                },
                                'content': [
                                     {
                                        'component': 'VSwitch',
                                        'props': {
                                            'model': 'run_once',
                                            'label': '指定目录运行一次',
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                    'md': 6
                                },
                                'content': [
                                    {
                                        'component': 'VTextarea',
                                        'props': {
                                            'model': 'path',
                                            'label': '手动指定BDMV文件夹路径,结尾加/ A会遍历所有子目录处理',
                                            'rows': 1,
                                            'placeholder': '路径指向BDMV父文件夹',
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                    'md': 6
                                },
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'delaymin',
                                            'label': '入库后延时处理时间（分钟）',
                                            'placeholder': '0'
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12
                                },
                                'content': [
                                    {
                                        'component': 'VTextarea',
                                        'props': {
                                            'model': 'temppath',
                                            'label': 'mkv临时路径,为空不启用，不能和处理路径跨盘，建议设置，避免未完成的文件被识别转移',
                                            'rows': 1,
                                            'placeholder': '指定生成mkv的临时目录，避免未生成完毕就开始识别转移',
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12
                                },
                                'content': [
                                    {
                                        'component': 'VTextarea',
                                        'props': {
                                            'model': 'outpath',
                                            'label': '输出目录，不设定则输出在原盘目录，原盘目录只读时需要设定',
                                            'rows': 1,
                                            'placeholder': '原盘目录只读时需要设定',
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        'component': 'VDivider'
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                    'md': 4
                                },
                                'content': [
                                    {
                                        'component': 'VSwitch',
                                        'props': {
                                            'model': 'emount',
                                            'label': '挂载iso',
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                    'md': 4
                                },
                                'content': [
                                    {
                                        'component': 'VSwitch',
                                        'props': {
                                            'model': 'eumount',
                                            'label': '卸载iso',
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                    'md': 4
                                },
                                'content': [
                                    {
                                        'component': 'VTextarea',
                                        'props': {
                                            'model': 'hostip',
                                            'label': 'Host IP',
                                            'rows': 1,
                                            'placeholder': '172.17.0.1',
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                    'md': 4
                                },
                                'content': [
                                    {
                                        'component': 'VTextarea',
                                        'props': {
                                            'model': 'hostroot',
                                            'label': 'Host root权限用户',
                                            'rows': 1,
                                            'placeholder': 'root',
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                    'md': 4
                                },
                                'content': [
                                    {
                                        'component': 'VTextarea',
                                        'props': {
                                            'model': 'hostpass',
                                            'v-model': 'password',
                                            'label': 'Host root权限用户密码',
                                            'rows': 1,
                                            'placeholder': 'pass',
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12
                                },
                                'content': [
                                    {
                                        'component': 'VTextarea',
                                        'props': {
                                            'model': 'isopath',
                                            'label': '指定扫描.iso文件路径,挂载内容需重启MP才会生效',
                                            'rows': 1,
                                            'placeholder': ' ',
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                    'md': 6
                                },
                                'content': [
                                    {
                                        'component': 'VTextarea',
                                        'props': {
                                            'model': 'isooutpath',
                                            'label': 'iso挂载目录',
                                            'rows': 1,
                                            'placeholder': ' ',
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                    'md': 6
                                },
                                'content': [
                                    {
                                        'component': 'VTextarea',
                                        'props': {
                                            'model': 'hostheader',
                                            'label': '转换关系，:分割，比如/movie4:/volume2/movie4',
                                            'rows': 1,
                                            'placeholder': 'MP目录:HOST对应目录',
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'content': [
                                    {
                                        'component': 'VAlert',
                                        'props': {
                                            'type': 'info',
                                            'variant': 'flat',
                                            'text': '自用插件，可能不稳定',
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ], {
            "enabled": False,
            "delete": False,
            "path": "",
            "temppath": "",
            "run_once": False,
            "delaymin": 0,
            "outpath": "",
            "isopath": "",
            "isooutpath": "",
            "emount": False,
            "eumount": False,	
            "hostip": "",
            "hostroot": "",
            "hostpass": "",
            "hostheader": "",
        }

    def get_page(self) -> List[dict]:
        pass
    def mount_iso(self,isoname,mpoint,header):
        if not os.path.exists(mpoint):
            try:
                logger.info('目录不存在，创建:' + mpoint)
                os.makedirs(mpoint)
            except OSError as e:
                logger.error(e)
        else:
            logger.info('目录:' + mpoint + '存在')
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=self._hostip,port=22,username=self._hostroot,password=self._hostpass)
        hostheader = header.split(':')[1]
        mpheader = header.split(':')[0]
        if mpheader:
            if isoname.find(mpheader) == -1:
                logger.warn('ISO目录不包含：' + mpheader)
                return
            if mpoint.find(mpheader) == -1:
                logger.warn('挂载点目录不包含：' + mpheader)
                return    
            cmdisoname = isoname.replace(mpheader, hostheader, 1)
            cmdmpoint = mpoint.replace(mpheader, hostheader, 1)
        else:
            cmdisoname = hostheader + isoname	
            cmdmpoint = hostheader + mpoint
        #mountcmd = 'mount -o ro \"' + header + isoname +'\" "' + header + mpoint +'\"'
        mountcmd = 'mount -o ro \"' + cmdisoname +'\" "' + cmdmpoint +'\"'
        logger.info('挂载命令：' + mountcmd)
        #'mount -o ro "/volume4/movie4/video/movie/Limbo.iso" "/volume4/movie4/video/movie/testiso"'
        stdin,stdout,stderr = ssh.exec_command(mountcmd)
        result = stdout.read().decode()
        reerr = stderr.read()
        if result:
            logger.info('挂载结果：' + str(result))
        if reerr:
            logger.info('挂载错误：' + str(reerr))
        ssh.close()
    def unmountiso(self,mpoint,header):
        # 实例化一个transport对象
        trans = paramiko.Transport((self._hostip, 22))
        # 建立连接
        trans.connect(username=self._hostroot, password=self._hostpass)
    
        # 将sshclient的对象的transport指定为以上的trans
        ssh = paramiko.SSHClient()
        ssh._transport = trans
        # 执行命令，和传统方法一样
        #  stdin, stdout, stderr = ssh.exec_command('df -hl')
        #  print(stdout.read().decode())
    
        # 关闭连接
        #  trans.close()
    
        #  ssh = paramiko.SSHClient()
        #  ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        #  ssh.connect(hostname='192.168.10.222',port=22,username='admin',password='5b6cs1')
        hostheader = header.split(':')[1]
        mpheader = header.split(':')[0]
        if mpheader:
            if mpoint.find(mpheader) == -1:
                logger.warn('挂载点目录不包含：' + mpheader)
                return    
            cmdmpoint = mpoint.replace(mpheader, hostheader, 1)
        else:
            cmdmpoint = hostheader + mpoint
        umountcmd = 'umount \"' + cmdmpoint +'\"'    
        #umountcmd = 'umount \"' + header + mpoint +'\"'
        logger.info('卸载命令：' + umountcmd)
        #'mount -o ro "/movie4/video/movie/Limbo.iso" "/movie4/video/movie/testiso"'
        stdin,stdout,stderr = ssh.exec_command(umountcmd)
        result = stdout.read().decode()
        reerr = stderr.read()
        if result:
            logger.info('卸载结果：' + str(result))
        if reerr:
            logger.info('卸载错误：' + str(reerr))
        trans.close() 
    def isomount(self,isopath,isooutpath):
        logger.info("搜索iso目录：" + self._isopath)
        logger.info("挂载点目录：" + self._isooutpath)
        header = self._hostheader
        for root, dirs, files in os.walk(isopath):
            for file in files:
                if file.endswith('.iso') or file.endswith('.ISO'):
                    mpath = os.path.join(root, file)
                    mpointpath = os.path.join(isooutpath, file[:-4])
                    self.mount_iso(mpath,mpointpath,header)
                    if not self._enabled:
                        logger.info('未使能，中断处理')
                        return
        logger.info('挂载iso处理完毕')
    def isoumount(self,isooutpath):
        logger.info("卸载挂载点目录：" + isooutpath)     
        files = os.listdir(isooutpath)
        header = self._hostheader
        for file in files:
            if os.path.isfile(os.path.join(isooutpath, file)):
                logger.info('文件跳过：' + file)
            if os.path.isdir(os.path.join(isooutpath, file)):
                logger.info('卸载目录：' + file)
                umpath = os.path.join(isooutpath, file)
                self.unmountiso(umpath,header)
                dirlens = os.listdir(umpath)
                if len(dirlens) == 0:
                    os.rmdir(umpath)
                if not self._enabled:
                    logger.info('未使能，中断处理')
                    return
        logger.info('卸载iso处理完毕')

    def extract_sub(self,path : str):
        if path.endswith('/ A'):
            # 获取所有子目录
            newpath = path[:-2]
            logger.info('处理所有子目录：' + newpath)
            sub_dirs = os.listdir( newpath )
            # 输出结果
            for file in sub_dirs:
                allfile = newpath+file
                logger.info('处理目录：' + allfile)
                self.extract(allfile)
                if not self._enabled:
                    logger.info('未使能，中断处理')
                    return
            logger.info('处理子目录结束：' + path)
        else:
            logger.info('处理单独目录：' + newpath)
            self.extract(path)
    def extract(self,bd_path : str):
        logger.info('开始提取BDMV。')
        if self._outpath:
            outdir = os.path.join(self._outpath, os.path.basename(bd_path))
            if not os.path.exists(outdir):
                logger.info('输出目录不存在，创建:' + outdir)
                try:
                    os.makedirs(outdir)
                except:
                    logger.warn('目录创建失败')
            output_name = os.path.basename(bd_path) + "-BDRem.mkv"
            output_name = os.path.join(outdir, output_name)
        else:
            outdir = bd_path
            output_name = os.path.basename(bd_path) + "-BDRem.mkv"
            output_name = os.path.join(bd_path, output_name)
        bdmv_path = bd_path + '/BDMV'
        if not os.path.exists(bdmv_path):
            logger.info('失败。输入路径不存在BDMV文件夹')
            return
        mpls_path = bd_path + '/BDMV' + '/PLAYLIST/'
        if not os.path.exists(mpls_path):
            logger.info('失败。找不到PLAYLIST文件夹')
            return
        #file_paths = self.get_all_m2ts(mpls_path)
        mpls_path = bd_path + '/BDMV' + '/STREAM/'
        file_paths = self.get_max_m2ts(mpls_path)
        if not file_paths:
            logger.info('失败。找不到m2ts文件')
            return
        logger.info('输出文件：' + output_name)
        if os.path.exists(output_name):
            logger.info('失败。输出文件已存在' + output_name)
            return
        if self.check_files(outdir,'mkv'):
            logger.info('失败。文件已存在' + self._mkvfile)
            return
        #filelist_string = '\n'.join([f"file '{file}'" for file in file_paths])
        # 将filelist_string写入filelist.txt
        #logger.info('搜索到需要提取的m2ts文件: ' + filelist_string)
        #with open('/tmp/filelist.txt', 'w') as file:
        #    file.write(filelist_string)
        usetemppath = False
        tmp_output = output_name
        if self._temppath:
            if self._temppath[0] == '/':
                if self._temppath[:self._temppath.find('/',1)] == bd_path[:bd_path.find('/',1)]:
                    try:
                        os.makedirs(self._temppath)
                    except:
                        pass
                    tmp_output = os.path.join(self._temppath, 'tmp_bdremuxer.mkv')
                    usetemppath = True
                else:
                    logger.info('临时目录和处理目录跨盘')
            else:
                logger.info('临时目录不是/开头，不启用临时目录：' + self._temppath) 
        else:
            logger.info('临时目录为空，不启用临时目录')
        if usetemppath:
            logger.info('采用临时目录：' + self._temppath)
        else:
            logger.info('不采用临时目录')
        logger.info('输出文件：' + tmp_output)
        
        if os.path.exists(tmp_output):
            logger.info('删除文件：'+tmp_output)
            os.remove(tmp_output)
        # 提取流程
        # 分析m2ts文件，提取视频流和音频流信息
        #test_file = file_paths[0]
        test_file = mpls_path + file_paths
        logger.info('搜索到需要提取的m2ts文件: ' + test_file)
        
        filelist_string = '\n'.join([f"file '{test_file}'"])
        # 将filelist_string写入filelist.txt
        logger.info('搜索到需要提取的m2ts文件: ' + filelist_string)
        with open('/tmp/filelist.txt', 'w') as file:
            file.write(filelist_string)
            
        probe = ffmpeg.probe(test_file)
        video_streams = [stream for stream in probe['streams'] if stream['codec_type'] == 'video']
        audio_streams = [stream for stream in probe['streams'] if stream['codec_type'] == 'audio']
        subtitle_streams = [stream for stream in probe['streams'] if stream['codec_type'] == 'subtitle']
        
        # 选取第一个视频流作为流编码信息
        video_codec = video_streams[0]['codec_name']
        # 获得每一条音频流的编码信息
        audio_codec = []
        for audio_stream in audio_streams:
            if audio_stream['codec_name'] == 'pcm_bluray':
                audio_codec.append('pcm_s16le')
            else:   
                audio_codec.append('copy')
            # print(audio_stream['codec_name'])
        
        # 获得每一条字幕流的编码信息
        subtitle_codec = []
        for subtitle_stream in subtitle_streams:
            if subtitle_stream['codec_name'] == 'hdmv_pgs_subtitle':
                subtitle_codec.append('copy')
            else:
                subtitle_codec.append('copy')
        
        # 整理参数作为字典
        dict = {  }
        for i in range(len(audio_codec)):
            dict[f'acodec:{i}'] = audio_codec[i]
        for i in range(len(subtitle_codec)):
            dict[f'scodec:{i}'] = subtitle_codec[i]
        # 使用ffmpeg合并m2ts文件
        try:
            (
            ffmpeg
            .input(
                '/tmp/filelist.txt', 
                format='concat', 
                safe=0, 
                )
            .output(
                tmp_output,
                vcodec='copy',
                **dict,
                map='0',  # 映射所有输入流
                map_metadata='0',  # 复制输入流的元数据
                map_chapters='0',  # 复制输入流的章节信息
            )
            .run()
            )
        except ffmpeg.Error as e:
            logger.error(e.stderr)
            logger.info('失败。')
            if os.path.exists(tmp_output):
                os.remove(tmp_output)
            try:
                log_file = open(os.path.join('/config', 'bdoutlist.log'),'a')
                log_file.write('失败 ' + output_name + ' \n')
                log_file.close()
            except:
                logger.info('写入log文件失败')
            return
        # remuxer成功，移动到目标目录  
        try:  
            os.rename(tmp_output,output_name)
        except:
            logger.warn('转移失败' + tmp_output + ' to ' + output_name)
        try:
            log_file = open(os.path.join('/config', 'bdoutlist.log'),'a')
            log_file.write('成功 ' + output_name + '\n')
            log_file.close()
        except:
            logger.info('写入log文件失败')
        if self._delete:
        # 删除原始文件
            shutil.rmtree(bd_path)
            logger.info('成功提取BDMV。并删除原始文件。')
        else:
            logger.info('成功提取BDMV。')
    
        
    def get_all_m2ts(self,mpls_path) -> list:
        """
        Get all useful m2ts file paths from mpls file
        :param mpls_path: path to mpls 00000 file
        :return: list of m2ts file paths
        """
        files = []
        play_items = []
        for file in os.listdir(mpls_path):
            if os.path.isfile(os.path.join(mpls_path, file)) and file.endswith('.mpls'):
                if file == '00000.mpls': continue # 跳过00000.mpls
                files.append(os.path.join(mpls_path, file))
        files.sort()
        for file in files:
            with open(file, 'rb') as mpls_file:
                header = mpls.load_movie_playlist(mpls_file)
                mpls_file.seek(header.playlist_start_address, os.SEEK_SET)
                pls = mpls.load_playlist(mpls_file)
                for item in pls.play_items:
                    if item.uo_mask_table == 0:
                        stream_path = os.path.dirname(os.path.dirname(file)) + '/STREAM/'
                        file_path = stream_path + item.clip_information_filename + '.m2ts'
                        play_items.append(file_path)
                if play_items:
                    return play_items
        return play_items
    def get_max_m2ts(self,mpls_path):
        """
        Get max size m2ts file
        """
        largest_size = -1 # 初始化为-1表示没有任何文件
        largest_filename = ""
    
        for filename in os.listdir(mpls_path):
            filepath = os.path.join(mpls_path, filename)
        
            if os.path.isfile(filepath): # 只处理文件而不包括子目录
                filesize = os.stat(filepath).st_size
            
                if filesize > largest_size:
                    largest_size = filesize
                    largest_filename = filename
        return largest_filename
    def schedlerisomount(self,isopath : str,isooutpath : str):
        thread = threading.Thread(target=self.isomount, args=(isopath,isooutpath,))
        thread.start()
    def schedlerisoumount(self,isooutpath : str):
        thread = threading.Thread(target=self.isoumount, args=(isooutpath,))
        thread.start()
    def schedlerremux_sub(self,bd_path : str):
        thread = threading.Thread(target=self.extract_sub, args=(bd_path,))
        thread.start()
    def schedlerremux(self,bd_path : str):
        thread = threading.Thread(target=self.extract, args=(bd_path,))
        thread.start()        
    def check_files(self,directory, extension):
        files = os.listdir(directory)
        for file in files:
            if file.endswith('.' + extension):
                logger.info("目录" + directory + "中包含了后缀为." + extension + "的文件")
                self._mkvfile = file
                return True
    
        logger.info("目录" + directory + "中不存在后缀为." + extension + "的文件")
        return False    
    #@eventmanager.register(EventType.TransferComplete)
    def remuxer(self, event):
        logger.info('传输完毕触发')
        return
        if not self._enabled:
            logger.info('未使能')
            return
        logger.info('1')
        item = event.event_data
        logger.info('2')
        if not item:
            logger.info('event data error')
            logger.info(item)
            return
        logger.info('3')            
        # 媒体信息
        item_media: MediaInfo = item.get("mediainfo")
        # 转移信息
        logger.info('4')
        item_transfer: TransferInfo = item.get("transferinfo")
        # 类型
        logger.info('5')
        item_type = item_media.type
        # 目的路径
        logger.info('6')
        item_dest: Path = item_transfer.target_path
        # 是否蓝光原盘
        logger.info('7')
        item_bluray = item_transfer.is_bluray
        # 文件清单
        logger.info('8')
        item_file_list = item_transfer.file_list_new  
        logger.info('9')
        if not item_bluray:
            logger.info('非蓝光原盘')
            return        
        logger.info('11')    
        bd_path = item_dest.resolve()
        logger.info('12')
        #logger.info(raw_data)
        #target_file = raw_data.get("transferinfo").get("file_list_new")[0]
        #bd_path = os.path.dirname(target_file)
        # 检查是否存在BDMV文件夹
        if not os.path.exists(bd_path + '/BDMV'):
            logger.warn('失败。找不到BDMV文件夹: ' + bd_path)
            return
        logger.info('13')    
        # 提取流程
        # thread = threading.Thread(target=self.extract, args=(bd_path,))
        # thread.start()
        # 延时提取
        logger.warn('延时' + self._delaymin + '分钟处理蓝光原盘目录: ' + bd_path)
        self._scheduler.add_job(self.schedlerremux, 'date', 
                                run_date=datetime.now(tz=pytz.timezone(settings.TZ)) + timedelta(minutes=float(self._delaymin)),
                                args=(bd_path,))
        # 启动任务
        logger.info('14')
        if self._scheduler.get_jobs():
            self._scheduler.print_jobs()
            self._scheduler.start()

    def stop_service(self):
        """
        退出插件
        """
        try:
            if self._scheduler:
                self._scheduler.remove_all_jobs()
                if self._scheduler.running:
                    self._scheduler.shutdown()
                self._scheduler = None
        except Exception as e:
            logger.error("退出插件失败：%s" % str(e))
        pass
