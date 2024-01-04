import time
import urllib.request
import urllib.response

from typing import Any, List, Dict, Tuple

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


class MediaServerRefresh(_PluginBase):
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
    author_url = "https://github.com/"
    # 插件配置项ID前缀
    plugin_config_prefix = "kodilibrefresh_"
    # 加载顺序
    plugin_order = 14
    # 可使用的用户级别
    auth_level = 1

    # 私有属性
    _enabled = False
    _delay = 0

    def init_plugin(self, config: dict = None):
        if config:
            self._enabled = config.get("enabled")
            self._delay = config.get("delay") or 0
            self._kodiuser = config.get("kodiuser")
            self._kodipass = config.get("kodipass")

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
                                    'md': 6
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
                    }
                ]
            }
        ], {
            "enabled": False,
            "delay": 0
        }

    def get_page(self) -> List[dict]:
        pass

    @eventmanager.register(EventType.TransferComplete)
    def refresh(self, event: Event):
        """
        发送通知消息
        """
        if not self._enabled:
            return

        event_info: dict = event.event_data
        if not event_info:
            return

        # 刷新媒体库
        if not settings.MEDIASERVER:
            return

        if self._delay:
            logger.info(f"延迟 {self._delay} 秒后刷新媒体库... ")
            time.sleep(float(self._delay))

        # 入库数据
        transferinfo: TransferInfo = event_info.get("transferinfo")
        mediainfo: MediaInfo = event_info.get("mediainfo")
        items = [
            RefreshMediaItem(
                title=mediainfo.title,
                year=mediainfo.year,
                type=mediainfo.type,
                category=mediainfo.category,
                target_path=transferinfo.target_path
            )
        ]
        if self._kodiuser:
            userName = self._kodiuser
        else: 
            userName = 'admin'
        if self._kodipass:	  
            passWord = self._kodipass
        else: 
            passWord = 'pass'
        top_level_url = "http://192.168.10.186:8080/jsonrpc"
        p = urllib.request.HTTPPasswordMgrWithDefaultRealm()
        p.add_password(None, top_level_url, userName, passWord);

        auth_handler = urllib.request.HTTPBasicAuthHandler(p)
        opener = urllib.request.build_opener(auth_handler)

        urllib.request.install_opener(opener)

        DATA = b'{"jsonrpc": "2.0", "method": "VideoLibrary.Scan", "id": "1"}'
        try:
            req = urllib.request.Request('http://192.168.10.186:8080/jsonrpc', data=DATA, headers={'Content-Type': 'application/json'})    
            result = opener.open(req)
            messages = result.read()
            print (messages)
        except IOError as e:
            print (e)
    def stop_service(self):
        """
        退出插件
        """
        pass
