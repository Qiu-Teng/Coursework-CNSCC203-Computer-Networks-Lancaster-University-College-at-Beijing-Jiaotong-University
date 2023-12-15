lucbjtu（北交威）计算机科学与技术 23-24 CNSCC203 计算机网络 大作业。基本的功能都实现了，有需要附加分的可以额外加功能。

运行方法
ICMPPing.py，Traceroute.py：直接运行即可，注意关闭VPN，使用default value的话一路回车就可以

WebServsr.py：，运行后选择8000号端口。注意需要先下载wget并把其添加到系统变量，win+r输入cmd回车，输入如下3条wget指令即可测试GET、DELETE、PUT方法：

wget http://127.0.0.1:8000/test1.html


wget --method=DELETE http://127.0.0.1:8000/sample.html



wget --method=PUT --header="Content-Type: text/html" --body-file="F:/sample.html" http://127.0.0.1:8000/sample.html -O - 

第四问代理服务器proxyserver.py，
使用两次如下wget命令（第一次无缓存，从目标服务器获取资源，第二次从代理服务器获取资源，测试和debug可以下载wireshark，注意选择loopback而不是WLAN，使用ip.addr == 127.0.0.1 && tcp.port == 8000，这个过滤器条件来抓包）

wget www.baidu.com -e use_proxy=on -e http_proxy=127.0.0.1:8000


