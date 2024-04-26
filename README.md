# MoviePilot-Plugins
MoviePilot官方插件市场：https://github.com/jxxghp/MoviePilot-Plugins
- [食用说明](MP-readme.md)

### 本仓库插件

#### [KODI库同步刷新]
- KODI开启HTTP 具体参见：https://kodi.wiki/view/JSON-RPC_API
- 插件具体实现方式参考：https://kodi.wiki/view/HOW-TO:Remotely_update_library
#### [Bdremuxer]
- 合并蓝光原盘为mkv文件
- 1.1.2 增加挂载和卸载iso文件功能
####  

# 微信交互设置
- 首先参考[通过CF实现公网访问](https://github.com/almus2zhang/MoviePilot-Plugins/blob/main/CFplusLuck.md "通过CF实现公网访问")
- 微信推送设置参考 
- [mp微信推送教程](https://github.com/hjfzzm/md_files/blob/main/Movie-Pilot%E9%83%A8%E7%BD%B2%E4%B8%8E%E5%BE%AE%E4%BF%A1%E6%8E%A8%E9%80%81%E6%95%99%E7%A8%8B.md "mp微信推送教程")
- 因为前面已经实现了无公网v4的外网访问，所以不需要教程里的VPS以及FRP。
- 首先在lucky配置好mp外网访问地址，比如https://mp.youdomain.com:8443/
- 确保外网可以打开mp。
- 然后只需要配置企业微信的时候把回调地址改为自己的地址，注意token改为自己的token。
- https://mp.youdomain.com:8443/api/v1/message/?token=moviepilot
