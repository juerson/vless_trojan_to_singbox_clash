本代码的功能：将CF的CDN优选IP、反代IP或域名，批量写入CF vless / trojan 节点中，转换为sing-box或clash的配置文件。支持 [CloudflareSpeedTest](https://github.com/XIU2/CloudflareSpeedTest)、[Cloudflare-IP-SpeedTest](https://github.com/badafans/Cloudflare-IP-SpeedTest) 优选的`result.csv`文件，也支持一行一个IPv4、域名的`server.txt`文件。

## 一、安装依赖

```bash
pip install -r requirements.txt
```
Python版本：3.12（开发中使用的版本）

## 二、修改`Config.toml`

### 2.1 可选参数

```toml
[select_proxy]
select_proxy_index = 0
random_proxy_type = "vless"
```

**select_proxy_index**：选择后面哪个代理的参数？有效值范围：[0，len(proxies))。

**random_proxy_type**：选择后面哪些代理的参数？vless？还是trojan？可选值：vless、trojan，其它值无效。

使用注意：

1、**select_proxy_index**和**random_proxy_type**参数都设置，当**select_proxy_index**参数值无效，**random_proxy_type**才生效。

2、设置了**select_proxy_index**参数，使用指定的某个代理参数生成配置，可能无法使用，或长时间等待才能联通网络，特别是 [GUI.for.SingBox](https://github.com/GUI-for-Cores/GUI.for.SingBox) 频繁切换配置文件；`hiddify-next` 首次导入可能可以使用，后来配置文件频繁换多了，就不能使用。

### 2.2 必须参数

- 1、vless+ws+tls

```toml
[[proxies.vless]]
remarks_prefix = "Node.1"
uuid = "3cc20e49-3f9a-4b50-aea4-f2324ea0abbc"
host = "vless.pages.dev"
server_name = "vless.pages.dev"
path = "/?ed=2048"
random_ports = [443, 2053, 2083, 2087, 2096, 8443]
```

- 2、trojan+ws+tls

```toml
[[proxies.trojan]]
remarks_prefix = "Node.2"
password = "249b8566-26fd-4b49-9ffd-2ea961297722"
host = "trojan.pages.dev"
server_name = "trojan.pages.dev"
path = "/"
random_ports = [443, 2053, 2083, 2087, 2096, 8443]
```

**remarks_prefix**：用于标识节点的名称(也称别名的前缀)，可以根据自己的情况修改。

**random_ports**：随机从这里的数组/列表中选择一个值作为节点中的端口；格式：[443]、[443, 2053, 2083, 2087, 2096, 8443]。

温馨提示：

1、你创建多少个CF Workers/Pages隧道，都可以根据前面的velss/trojan格式在后面复制若干份并修改参数值，运行代码生成配置文件（统一管理）。

2、**`Config.toml`文件中的vless、trojan配置是乱写的，使用它们生成配置文件无法使用的。**

## 三、使用

1、准备数据：以 **result.csv** 或 **server.txt** 文件为输入数据。

​	A. 双击 **[1] 从IPv4 CIDR中随机选择一个IP进行延迟测试.bat** 脚本文件，获取最新的`result.csv`数据。

​	B. **删除result.csv**文件或**修改result.csv**文件为其它名，然后将IPv4地址、域名地址写入到`server.txt`文件（每行一个）。

2、运行Python代码：双击 **[2] 执行Python代码.bat** 脚本文件，生成**sing-box**和**clash**的文件夹，里面的文件就是您需要的。

3、【可选】WEB服务：双击 **[3] FileServer.exe** 程序，将本地文件转换为本地订阅链接，可以通过**"http://"**链接，订阅里面的文件内容。

傻瓜式操作：安装Python和Python依赖后，按照[1]、[2]、[3]前缀的文件先后顺序执行。
