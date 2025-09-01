import time
import urllib.request
import urllib.response

from typing import Any, List, Dict, Tuple, Optional
from datetime import datetime, timedelta
from pathlib import Path

import pytz
from apscheduler.schedulers.background import BackgroundScheduler


from app.core.config import settings
from app.core.context import MediaInfo
from app.core.event import eventmanager, Event
from app.modules.emby import Emby
from app.modules.jellyfin import Jellyfin
from app.modules.plex import Plex
from app.plugins import _PluginBase
from app.schemas import TransferInfo, RefreshMediaItem
from app.schemas.types import EventType
from app.log import logger


class KodiLibRefresh(_PluginBase):
    # 插件名称
    plugin_name = "KODI库刷新"
    # 插件描述
    plugin_desc = "媒体库更新后同步让KODI刷新库"
    # 插件图标
    plugin_icon = "Kodi_A.png"
    # 插件版本
    plugin_version = "1.0"
    # 插件作者
    plugin_author = "almus"
    # 作者主页
    author_url = "https://github.com/almus2zhang/MoviePilot-Plugins"
    # 插件配置项ID前缀
    plugin_config_prefix = "kodilibrefresh_"
    # 加载顺序
    plugin_order = 14
    # 可使用的用户级别
    auth_level = 1

    # 私有属性
    _enabled = False
    _onlyonce = False
    _delay = 0
    _scheduler: Optional[BackgroundScheduler] = None

    def init_plugin(self, config: dict = None):
        if config:
            self._enabled = config.get("enabled")
            self._delay = config.get("delay") or 0
            self._kodiserver = config.get("kodiserver")
            self._kodiuser = config.get("kodiuser")
            self._kodipass = config.get("kodipass")
            self._onlyonce = config.get("onlyonce")
            self._kodiclean = config.get("kodiclean")
        if self._enabled:

            self._scheduler = BackgroundScheduler(timezone=settings.TZ)
            if self._onlyonce:
                logger.info(f"KODI库刷新，立即运行一次")
                self._scheduler.add_job(func=self.runonce, trigger='date',
                                        run_date=datetime.now(tz=pytz.timezone(settings.TZ)) + timedelta(seconds=3),
                                        name='KODIRefresh')
                self._onlyonce = False
                self.update_config({
                    "onlyonce": False,
                    "enabled": self._enabled,
                    "delay": self._delay,
                    "kodiserver": self._kodiserver,
                    "kodiuser": self._kodiuser,
                    "kodipass": self._kodipass,
                    "kodiclean": self._kodiclean,
                })

            # 启动任务
            if self._scheduler.get_jobs():
                self._scheduler.print_jobs()
                self._scheduler.start()
                
    def get_state(self) -> bool:
        return self._enabled

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        pass

    def get_api(self) -> List[Dict[str, Any]]:
        pass

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
                                            'model': 'kodiclean',
                                            'label': '清除无效资源',
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
                                            'model': 'onlyonce',
                                            'label': '立即运行一次',
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
                                },
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'delay',
                                            'label': '延迟时间（秒）',
                                            'placeholder': '0'
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
                                },
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'kodiuser',
                                            'label': 'Kodi用户名',
                                            'placeholder': 'admin'
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
                                },
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'kodipass',
                                            'label': 'Kodi密码',
                                            'placeholder': 'pass'
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
                                },
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'kodiserver',
                                            'label': 'Kodi地址',
                                            'placeholder': 'http://127.0.0.1:8080/jsonrpc'
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
            "delay": 0
        }

    def get_page(self) -> List[dict]:
        pass
    def runonce(self):
        if not self._enabled:
            logger.warn("kodi refresh not enable");
            return

        if self._kodiuser:
            userName = self._kodiuser
        else: 
            userName = 'admin'
        if self._kodipass:	  
            passWord = self._kodipass
        else: 
            passWord = 'pass'
        if self._kodiserver:
            top_level_url = self._kodiserver
            #"http://192.168.10.186:8080/jsonrpc"
        else:
            logger.warn("kodi server not set")
            return
        p = urllib.request.HTTPPasswordMgrWithDefaultRealm()
        p.add_password(None, top_level_url, userName, passWord);

        auth_handler = urllib.request.HTTPBasicAuthHandler(p)
        opener = urllib.request.build_opener(auth_handler)

        urllib.request.install_opener(opener)

        DATA = b'{"jsonrpc": "2.0", "method": "VideoLibrary.Scan", "id": "1"}'
        try:
            req = urllib.request.Request(self._kodiserver, data=DATA, headers={'Content-Type': 'application/json'})    
            result = opener.open(req)
            messages = result.read()
            logger.info(f"kodi刷新命令返回信息:")
            logger.info(messages)
        except IOError as e:
            logger.warn(e)
        if self._kodiclean:
            DATA = b'{"jsonrpc": "2.0", "method": "VideoLibrary.Clean", "id": "1"}'
            try:
                req = urllib.request.Request(self._kodiserver, data=DATA, headers={'Content-Type': 'application/json'})    
                result = opener.open(req)
                messages = result.read()
                logger.info("kodi清理命令返回信息:")
                logger.info(messages)
            except IOError as e:
                logger.warn(e)   
            
    @eventmanager.register(EventType.TransferComplete)
    def refresh(self, event: Event):
        """
        发送通知消息
        """
        if not self._enabled:
            logger.warn("kodi refresh not enable");
            return
        if self._delay:
            logger.info(f"延迟 {self._delay} 秒后刷新KODI库... ")
            time.sleep(float(self._delay))    
        self.runonce()
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
