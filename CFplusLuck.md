# 1 CF注册
电子邮件和密码注册，注意密码规则
![](http://v.nasnas.site:8080/content/uploadfile/202404/4deb1714112669.jpg)
注册完毕点击 Add a website or application
![](http://v.nasnas.site:8080/content/uploadfile/202404/a1db1714112670.jpg)
填写你的域名，点击Continue
![](http://v.nasnas.site:8080/content/uploadfile/202404/ca851714112999.jpg)
Free 肯定选择Free。
然后会出现当前域名的解析结果，读取完毕后点击Continue。
![](http://v.nasnas.site:8080/content/uploadfile/202404/c54a1714112670.jpg)
然后会自动跳到填写的域名控制面板，提示还未激活，记录下来CF给的两个DNS服务器。
![](http://v.nasnas.site:8080/content/uploadfile/202404/94f71714112629.png)

接下来需要到你的域名提供商去设定，比如我的是阿里云的域名。
![](http://v.nasnas.site:8080/content/uploadfile/202404/0ca51714113446.png)
登录阿里云之后，打开控制台，点击域名，在想要加到CF的域名后面点击管理
![](http://v.nasnas.site:8080/content/uploadfile/202404/14001714113482.png)
左边选择DNS修改
![](http://v.nasnas.site:8080/content/uploadfile/202404/3a291714113509.png)
点击修改DNS服务器
![](http://v.nasnas.site:8080/content/uploadfile/202404/8e471714113534.png)
修改为刚才CF提供的两个服务器后点击确定，然后过一会儿去CF刷新看看域名是否激活成功。
这个修改DNS服务器的具体步骤CF也有说明。
至此CF的设定告一段落，可以开始配置Lucky。


# 2 Lucky安装
Lucky负责DDNS以及反代，DDNS功能和DDNS-go一样，可以省掉DDNS-go。
Lucky采用docker安装，如下命令安装，注意修改一下映射卷的地址
> docker run -d --name lucky --restart always --net=host -v /volume2/docker/goodluck:/goodluck gdy666/lucky

------------

安装完毕后端口16601打开，默认用户名666密码666.登录后记得修改密码。


# 3 Lucky配置DDNS
打开lucky修改完密码后，左边选择动态域名->添加任务
  ![](http://v.nasnas.site:8080/content/uploadfile/202404/73e91714114396.png)
服务商选择Cloudflare
类型选择ipv6，因为没有ipv4公网IP，如果有v4公网，可以把v4也选上。
域名列表填写自己的域名以及*.域名两条*
  ![](http://v.nasnas.site:8080/content/uploadfile/202404/46a51714114581.png)
这里面需要填写CF的token，直接点击创建令牌->编辑区域DNS(使用模板)会跳到CF网站创建API令牌界面。
![](http://v.nasnas.site:8080/content/uploadfile/202404/29821714114699.png)
点击创建令牌后，点击编辑区域DNS后面的使用模板。
![](http://v.nasnas.site:8080/content/uploadfile/202404/50541714114749.png)
然后区域资源里面的特定资源后面select下拉框选择对应的域名。然后点击继续以显示摘要
![](http://v.nasnas.site:8080/content/uploadfile/202404/4d291714117201.png)
这个时候会出现摘要信息，包含指定域名的DNS修改权限，点击创建令牌。
![](http://v.nasnas.site:8080/content/uploadfile/202404/ce491714117002.png)
接下来会出现你的访问令牌，这个令牌以后不会在显示，可以复制保存下来。
![](http://v.nasnas.site:8080/content/uploadfile/202404/1c8d1714115045.png)
接着回到Lucy界面，把这个令牌填入，然后点击添加任务
![](http://v.nasnas.site:8080/content/uploadfile/202404/101b1714115152.png)
稍等片刻回到CF控制台DNS->记录，应该可以看到Lucky添加的两条DNS记录，对应V6地址。
![](http://v.nasnas.site:8080/content/uploadfile/202404/73391714115347.png)
这时候IP后面的代理状态应该是仅DNS，图标是灰色的云朵。点击需要代理的域名右边编辑，代理状态下面的勾打开，然后保存。
![](http://v.nasnas.site:8080/content/uploadfile/202404/4a511714115397.png)
这时候域名IP后面应该变成黄色云朵 已代理。
至此CF以及Lucky DDNS已经设定完毕。可以试试域名加端口看能否访问相应的服务。
这里需要注意CF只支持以下端口
HTTP 80 8080 8880 2052 2082 2086 2095
HTTPS 443 2053 2083 2087 2096 8443
如果访问正常，就已经通过CF实现了公网V4转V6的访问。
如果客户端有v6的时候能打开，但是没有v6的时候打不开，就是没成功。
![](http://v.nasnas.site:8080/content/uploadfile/202404/23141714116616.png)


# 4 Lucky反代实现不同子域名同一个端口转到不同主机:端口的服务
上面已经实现了无v4情况下通过CF外网访问的效果，但是CF提供的端口有限，所以需要用Lucky反代的功能实现更多访问
打开Lucky界面，左边选择web服务->添加web服务规则
![](http://v.nasnas.site:8080/content/uploadfile/202404/8ee91714118808.png)
名称随意，监听选择tcp6，因为没有v4公网ip，从CF过来的都是v6。端口选择上面CF支持的HTTP端口，这里8880示意。
![](http://v.nasnas.site:8080/content/uploadfile/202404/f9611714118840.png)
然后点击添加web服务子规则
![](http://v.nasnas.site:8080/content/uploadfile/202404/8a841714118924.png)
名称无所谓，服务类型反向代理前端地址自己随意定义子域名，比如想要访问jellyfin，前端地址添加a.youdomain.com 这里域名需要修改为自己的。
后端地址是内网访问jellyfin的地址。
万事大吉启用。然后点击下面的添加web服务规则。
至此一条反代就实现了，可以试试访问a.youdomain.com:8880 看能否打开jellyfin界面。

# 5 开启HTTPS访问
首先到CF控制台SSL/TLS->概述，右边选择完全。
![](http://v.nasnas.site:8080/content/uploadfile/202404/aa601714119365.png)
然后到边缘证书看，应该有CF管理的域名对应的证书。
![](http://v.nasnas.site:8080/content/uploadfile/202404/689f1714119378.png)
到Lucky上和第四步一样添加web规则，但是打开TLS，并且选择CF支持的HTTPS端口，比如8443.同样添加自规则后测试是否https可以访问
![](http://v.nasnas.site:8080/content/uploadfile/202404/a55d1714119566.png)
