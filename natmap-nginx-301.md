# openwrt NATMAP配置
natmap安装完成后，在服务natmap可以打开配置页面，点击添加
![[https://github.com/almus2zhang/MoviePilot-Plugins/blob/main/img/PIC20241215140917001.jpg]]
协议一般是TCP，如果还需要UDP就再加一个
地址仅IPv4
接口选择wan
keep-alive 30以内
STUN server 这里有个坑我用stunserver.stunprotocol.org一直不行，可能是这个服务器坏了
这里有可用的stun服务器列表 [连接]([always-online-stun/valid_hosts_tcp.txt at master · pradt2/always-online-stun · GitHub](https://github.com/pradt2/always-online-stun/blob/master/valid_hosts_tcp.txt))
http server用一个稳定可靠的网站，是用来连接用的。
Bind port随意
如果像转发到本地局域网的服务则勾选 forward mode
下面填上局域网服务的ip和端口。
这里面特别注意如果勾选了Forward mode，就不要在防火墙里面加对应的端口转发了。
创建完毕后启动
![[https://github.com/almus2zhang/MoviePilot-Plugins/blob/main/img/PIC20241215140917001.jpg]]
过一会儿能看到外部ip和端口就是stun打洞成功了。
这个时候访问 外部ip:外部端口 就可以连到上面转发设置的目标ip:目标端口了。如果无法访问，看一下WAN的防火墙是不是接受入站了。我的OP的WAN防火墙入站总是自己变成拒绝。

如果总是不成功（没有外部IP和端口）就要看一下自己是不是NAT1.
有一个小工具pystun3可以检测NAT类型，建议直接拨号的路由器运行
pip install pystun3  或者 apt install python-pystun3
然后运行pystun3可以看看NAT类型
如下就是NAT1了
![[https://github.com/almus2zhang/MoviePilot-Plugins/blob/main/img/PIC20241215140917001.jpg]]

# 搭配Nginx跳转
以上打洞成功，可以通过外部访问了，但是并不知道外部ip和端口什么时候会变。
NATMAP在建立连接之后可以运行脚本，就可以实现很多功能，比如把ip和端口发给微信，发给网站等等。
首选要有一个可以公网访问的nginx服务器。
让脚本修改nginx配置的跳转文件，这样ip和端口更新后更新跳转文件，结合nginx的跳转指令，可以输入固定的地址入口对应的调到更新后的地址。
nginx配置文件里面增加map
```
map $uri $redirect_url{
        include /root/docker/nginx/redirect.map;
        include /root/docker/nginx/jellyfin.map;
        include /root/docker/nginx/emby.map;
        include /root/docker/nginx/iptv.map;
        }

并且在location下增加

location / {
            rewrite ^ $redirect_url redirect;
            add_header Location '';
            # 禁止浏览器缓存重定向
            add_header Cache-Control 'no-store';
    }

```
意思是uri匹配到关键字后，跳转到 redirect_url
map文件示例
`/emby http://1.2.3.4:888;`
意思是访问/emby会自动跳转到 http://1.2.3.4:888
这样natmap ip和端口更新后修改map文件就可以实现动态跳转。
需要配置一个脚本用于监控map文件修改后自动reload nginx的配置
脚本如下
```
#!/bin/sh

# 初始配置文件的校验和
initial_checksum=$(find /root/docker/nginx/ -type f -name '*.map' -exec cksum {} \; | sort | cksum)


# 监视目录和文件变化
inotifywait -e modify,move,create,delete -mr --timefmt '%d/%m/%y %H:%M:%S' --format '%T' \
  /root/docker/nginx/ |
  while read date time; do
    new_checksum=$(find /root/docker/nginx/ -type f -name '*.map' -exec cksum {} \; | sort | cksum)

    if [ "$new_checksum" != "$initial_checksum" ]; then
      echo "At ${time} on ${date}, configuration file update detected."
      initial_checksum=$new_checksum
      /usr/sbin/nginx -s reload
    fi
  done

```

# NATMAP的脚本
NATMAP更新后会调用脚本
脚本内容
```
#!/bin/sh
outter_ip=$1
outter_port=$2
in4p=$3
inner_port=$4
protocol=$5
time=$(date "+%Y.%m.%d %H:%M:%S")

if [ $inner_port == 8099 ]; then
        echo "$time emby change to $1:$2" >>/root/docker/natmap/out.log
        echo "/emby http://$1:$2;" > /mnt/dsm/docker/xj-root/docker/nginx/emby.map
fi
if [ $4 == 8096 ]; then
        echo "$time jellyfin change to $1:$2" >>/root/docker/natmap/out.log
        echo "/jellyfin http://$1:$2;" > /mnt/dsm/docker/xj-root/docker/nginx/jellyfin.map
fi
if [ $4 == 9022 ]; then
        echo "$time iptv change to $1:$2" >>/root/docker/natmap/out.log
        echo "/iptv http://$1:$2;" > /mnt/dsm/docker/xj-root/docker/nginx/iptv.map
fi
if [ $4 == 1234 ]; then
        echo "$time speed change to $1:$2" >>/root/docker/natmap/out.log
        echo "/speed http://$1:$2;" >> /mnt/dsm/docker/xj-root/docker/nginx/redirect.map
fi

```
这里通过判断端口号识别是哪个服务，然后把对应的map文件修改。
需要事先把nginx服务器的文件挂载到运行NATMAP的机器上

总体上就是NATMAP更新后 调用脚本 修改 Nginx服务器的map文件。
Nginx服务器监控到map文件更新后 reload配置。

