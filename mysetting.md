# 我的MP设定说明
我才用docker部署方式，环境变量尽量减少，配置在app.env里面。

## 目录设定：
我的目录架构如下
![[Pasted image 20240106112836.png]]
movie4宿主机目录为/volume4/movie4
其中movie4/video下面的目录是下载目录。
movie4/nastoollink目录是整理后的媒体目录。
我的二级策略为
movie: 只有一个分类是电影
tv: 只有两个分类是电视剧和动漫
我QB和TR同样的映射目录，任务很多，没办法更改了
QB和TR的映射是
/volume4/movie4/video:/video4
MP如果同样的映射
/volume4/movie4/video:/video4
nastoollink目录进不来
所以我把movie4也映射进来
/volume4/movie4:/movie4

我的MP设定
DOWNLOAD_PATH='/video4'
DOWNLOAD_MOVIE_PATH='/video4/movie'
DOWNLOAD_TV_PATH='/video4/tv'
这样电影和电视剧的订阅可以下载到对应目录。
媒体目录设置如下：
LIBRARY_PATH='/movie4'
LIBRARY_MOVIE_NAME='nastoollink'
LIBRARY_TV_NAME='nastoollink'
LIBRARY_ANIME_NAME='nastoollink'
LIBRARY_CATEGORY='True'
监控插件设置如下：
/movie4/video/movie:/movie4/nastoollink
/movie4/video/tv:/movie4/nastoollink

订阅下载或者监控下载器整理的会按照 {LIBRARY_PATH}/{LIBRARY_MOVIE(/TV/ANIME)_NAME}/二级策略分类 来整理
目录监控的会按照设置的对应目录加上二级策略分类来整理。
这样设置两个会整理到同样的目录。
