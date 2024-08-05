from collections import OrderedDict
import pandas as pd
import random
import toml
import yaml
import json
import copy
import glob
import os


def manage_output_directory(directory: str, filter_files: list):
    """检查当前路径中是否存在指定文件夹，不存在则创建，存在就检测json、yaml文件，有则删除文件"""
    if not os.path.exists(directory):
        os.makedirs(directory)
    else:
        files = glob.glob(os.path.join(directory, "*.json")) + glob.glob(
            os.path.join(directory, "*.yaml")
        )
        if files:
            # 过滤掉不要删除的文件
            filtered_files = [
                item
                for item in files
                if not any(item.endswith(fe) for fe in filter_files)
            ]
            for file in filtered_files:
                os.remove(file)


def read_toml_parameter_values(file_name: str) -> tuple:
    """读取toml文件中的数据"""
    try:
        # 读取config.toml文件内容(以字典的形式存储)
        with open(file_name, mode="r", encoding="utf-8") as f:
            data = toml.load(f)
            select_proxy: dict = data.get("select_proxy", dict())
            # 选中具体那个代理？全部代理的index值(从0开始)
            checked_proxy_index: int = select_proxy.get("select_proxy_index")
            # 在哪种协议的代理的基础上随机选择一个？
            random_proxy_type: str = select_proxy.get("random_proxy_type")

            proxies = data.get("proxies")
            # 获取全部的vless协议的配置参数
            all_vless_proxies: list = proxies.get("vless", [])
            # 获取全部trojan协议的配置参数
            all_trojan_proxies: list = proxies.get("trojan", [])
            # vless协议+trojan协议(全部配置参数)
            all_proxies: list = all_vless_proxies + all_trojan_proxies
    except FileNotFoundError:
        print(f"文件{file_name}找不到。")
        return (None, None, None, None, None)
    except toml.TomlDecodeError:
        print(f"文件{file_name}格式错误。")
        return (None, None, None, None, None)
    except Exception as e:
        print(f"文件{file_name}读取错误。")
        return (None, None, None, None, None)
    else:
        return (
            checked_proxy_index,
            random_proxy_type,
            all_vless_proxies,
            all_trojan_proxies,
            all_proxies,
        )


def read_csv_data(file_name: str) -> list:
    """读取csv文件中的数据"""
    try:
        df = pd.read_csv(file_name, encoding="utf-8")
        # 延迟
        min_delay = 0
        max_delay = 500
        # 丢包率
        loss = 0
        # 根据csv文件的不同标题，筛选数据
        if "丢包率" in df.columns and "已接收" in df.columns and "已发送" in df.columns:
            filtered_df = df[df["丢包率"].notna() & (df["丢包率"] == loss)]
        elif "TCP延迟(ms)" in df.columns and "数据中心" in df.columns:
            filtered_df = df[
                df["TCP延迟(ms)"].notna() & (min_delay < df["TCP延迟(ms)"] < max_delay)
            ]
        elif "网络延迟" in df.columns and "数据中心" in df.columns:
            df["网络延迟"] = df["网络延迟"].str.replace(" ms", "").astype(float)
            filtered_df = df[
                df["网络延迟"].notna() & (min_delay < df["网络延迟"] < max_delay)
            ]
        elif "平均延迟" in df.columns:
            df["平均延迟"] = df["平均延迟"].str.replace(" ms", "").astype(float)
            filtered_df = df[
                df["平均延迟"].notna() & (min_delay < df["平均延迟"] < max_delay)
            ]
        elif "国家代码" in df.columns and "数据中心" in df.columns:
            filtered_df = df[df["国家代码"].notna()]  # 检查列中的值是否不为空值
        else:
            # 第4列丢包率等于0.00
            filtered_df = df[df.iloc[:, 3].notna() & (df.iloc[:, 3] == loss)]
        data = filtered_df.iloc[:, 0].tolist()  # 获取第1列的数据，并转换为list
    except FileNotFoundError:
        print(f"错误：文件{file_name}不存在。")
        return []
    except PermissionError:
        print(f"错误：没有权限读取文件{file_name}。")
        return []
    except pd.errors.EmptyDataError:
        print(f"错误：文件{file_name}是空的。")
        return []
    except pd.errors.ParserError:
        print(f"错误：无法解析文件{file_name}。文件可能不是有效的CSV格式。")
        return []
    except UnicodeDecodeError:
        print(f"错误：文件{file_name}编码不是UTF-8或包含无法解码的字符。")
        return []
    except MemoryError:
        print("错误：文件太大，内存不足以处理。")
        return []
    except Exception as e:
        print(f"发生了意外错误：{str(e)}")
        return []
    else:
        return data


def read_server_file_data(file_name: str) -> list:
    """读取server.txt文件中的数据"""
    try:
        with open(file_name, mode="r", encoding="utf-8") as f:
            unique_lines = list(
                OrderedDict.fromkeys(line.strip() for line in f if line.strip() != "")
            )
    except FileNotFoundError:
        print(f"错误：文件{file_name}不存在。")
        return []
    except PermissionError:
        print(f"错误：没有权限读取文件{file_name}。")
        return []
    except UnicodeDecodeError:
        print(f"错误：文件{file_name}编码不是UTF-8或包含无法解码的字符。")
        return []
    except MemoryError:
        print("错误：文件太大，内存不足以处理。")
        return []
    except Exception as e:
        print(f"发生了意外错误：{str(e)}")
        return []
    else:
        return unique_lines


def match_proxy_type(
    all_proxy: str, all_vless_proxy: list, all_trojan_proxy: list, proxy_type: list
) -> list:
    """根据proxy_type来匹配不同list中的节点（选中vless的节点、trojan的节点，还是不区分vless和trojan的节点）"""
    match proxy_type:
        case None:
            return all_proxy
        case "vless":
            return all_vless_proxy
        case "trojan":
            return all_trojan_proxy
        case _:
            return all_proxy


def select_proxies_list(
    index: int,
    proxy_type: str,
    all_vless_proxy: list,
    all_trojan_proxy: list,
    all_proxy: list,
) -> list:
    """选中config.toml中全部代理？还是选中vless协议的代理？亦或者选中trojan协议的代理？"""
    match index:
        case None:
            return match_proxy_type(
                all_proxy, all_vless_proxy, all_trojan_proxy, proxy_type
            )
        case index if -1 < index < len(all_proxy):
            return [all_proxy[index]]  # 选中具体一个元素，需要套一层中括号转化为list
        case _:
            return match_proxy_type(
                all_proxy, all_vless_proxy, all_trojan_proxy, proxy_type
            )


def read_singbox_template(file_name: str) -> dict:
    """读取sing-box.json文件中的数据，并返回一个dict"""
    try:
        with open(file_name, mode="r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        print(f"错误：文件{file_name}不存在。")
        return dict()
    except json.JSONDecodeError:
        print(f"错误：文件{file_name}不是有效的 JSON 格式。")
        return dict()
    except PermissionError:
        print(f"错误：没有权限读取文件{file_name}。")
        return dict()
    except Exception as e:
        print(f"发生了意外错误：{str(e)}")
        return dict()
    else:
        return data


def read_clash_template(file_name: str) -> dict:
    """读取 YAML 文件并返回其内容"""
    try:
        with open(file_name, mode="r", encoding="utf-8") as file:
            data: dict = yaml.safe_load(file)
    except FileNotFoundError:
        print(f"错误：文件{file_name}不存在。")
        return dict()
    except yaml.YAMLError as yaml_err:
        print(f"错误：YAML 解析失败。{yaml_err}")
        return dict()
    except PermissionError:
        print(f"错误：没有权限读取文件{file_name}。")
        return dict()
    except Exception as e:
        print(f"发生了意外错误：{str(e)}")
        return dict()
    else:
        return data


def determining_proxy_type(data: dict) -> str:
    """判读选中的节点类型(vless？还是trojan?)"""
    match data:
        case {"password": password}:
            return "trojan"
        case {"uuid": uuid}:
            return "vless"
        case _:
            return ""


def build_singbox_node(
    proxy_type: str, tag: str, server: str, port: int, checked_proxy: dict
) -> dict:
    """根据节点的类型来构建节点信息"""
    fingerprint = [
        "chrome",
        "firefox",
        "safari",
        "edge",
        "random",
        "ios",
        "android",
        "random",
        "randomized",
    ]
    match proxy_type:
        case "vless":
            vless_node = {
                "type": "vless",
                "tag": tag,
                "server": server,
                "server_port": int(port),
                "uuid": checked_proxy.get("uuid"),
                "network": "tcp",  # 启用tcp的网络协议，这里只能走tcp的流量，不能走udp的流量
                "tls": {
                    "enabled": True,
                    "server_name": checked_proxy.get("server_name"),
                    "insecure": True,
                    "utls": {
                        "enabled": True,
                        "fingerprint": random.choice(fingerprint),
                    },
                },
                "transport": {
                    "type": "ws",
                    "path": checked_proxy.get("path"),
                    "headers": {"Host": checked_proxy.get("host")},
                    "early_data_header_name": "Sec-WebSocket-Protocol",
                },
            }
            return vless_node
        case "trojan":
            trojan_node = {
                "type": "trojan",
                "tag": tag,
                "server": server,
                "server_port": int(port),
                "password": checked_proxy.get("password"),
                "network": "tcp",  # 启用tcp的网络协议，这里只能走tcp的流量，不能走udp的流量
                "tls": {
                    "enabled": True,
                    "server_name": checked_proxy.get("server_name"),
                    "insecure": True,
                    "utls": {
                        "enabled": True,
                        "fingerprint": random.choice(fingerprint),
                    },
                },
                "transport": {
                    "type": "ws",
                    "path": checked_proxy.get("path"),
                    "headers": {"Host": checked_proxy.get("host")},
                    "early_data_header_name": "Sec-WebSocket-Protocol",
                },
            }
            return trojan_node
        case _:
            return {}


def build_clash_node(
    proxy_type: str, tag: str, server: str, port: int, checked_proxy: dict
) -> dict:
    """根据节点的类型来构建节点信息"""
    fingerprint = [
        "chrome",
        "firefox",
        "safari",
        "edge",
        "random",
        "ios",
        "android",
        "random",
        "randomized",
    ]
    match proxy_type:
        case "vless":
            vless_node = {
                "type": "vless",
                "name": tag,
                "server": server,
                "port": int(port),
                "uuid": checked_proxy.get("uuid"),
                "network": "ws",  # 注意不是tcp和upd，而是ws
                "tls": True,
                "udp": False,
                "servername": checked_proxy.get("server_name"),  # 跟sni字段效果一样
                "client-fingerprint": random.choice(fingerprint),
                "skip-cert-verify": True,  # 跳过证书验证
                "ws-opts": {
                    "path": checked_proxy.get("path", "/?ed=2048"),
                    "headers": {"Host": checked_proxy.get("host", "")},
                },
            }
            return vless_node
        case "trojan":
            trojan_node = {
                "type": "trojan",
                "name": tag,
                "server": server,
                "port": int(port),
                "password": checked_proxy.get("password"),
                "network": "ws",  # 注意不是tcp和upd，而是ws
                "tls": True,  # trojan 协议强制启用，不写也可以
                "udp": False,
                "sni": checked_proxy.get("server_name", ""),
                "client-fingerprint": random.choice(fingerprint),
                "skip-cert-verify": True,  # 跳过证书验证
                "ws-opts": {
                    "path": checked_proxy.get("path", "/"),
                    "headers": {"Host": checked_proxy.get("host", "")},
                },
            }
            return trojan_node
        case _:
            return dict()


def update_singbox_value(
    remarks_list: list, node_list: list, singbox_template: dict
) -> dict:
    """处理singbox的配置文件"""
    outside_outbounds = singbox_template.get("outbounds", None)
    if not isinstance(outside_outbounds, list):
        return {}
    for item in outside_outbounds:
        inside_outbounds = item.get("outbounds", None)
        if isinstance(inside_outbounds, list):
            inside_outbounds.extend(remarks_list)
            remove_value = r"{all}"
            if remove_value in inside_outbounds:
                inside_outbounds.remove(remove_value)
    outside_outbounds[2:2] = node_list
    return singbox_template


def update_clash_value(remarks_list, clash_proxies_nodes, clash_template):
    """处理clash的配置文件"""
    proxies = clash_template.get("proxies", [])
    proxies.extend(clash_proxies_nodes)
    # 读取代理组
    proxy_groups = clash_template.get("proxy-groups")
    for proxy_group in proxy_groups:
        proxy_names = proxy_group.get("proxies", [])
        if "s01" in proxy_names:
            proxy_names.extend(remarks_list)
            proxy_names.remove("s01")
    return clash_template


# 改变yaml文件的缩进格式
# 定义一个名为 MyDumper 的类，继承自 yaml.Dumper
class MyDumper(yaml.Dumper):

    # 重写 increase_indent 方法，用于增加缩进
    def increase_indent(self, flow=False, indentless=False):
        # 调用父类的 increase_indent 方法，但将 indentless 参数始终设为 False
        return super(MyDumper, self).increase_indent(flow, False)

    # 重写 represent_sequence 方法，用于表示 YAML 序列
    def represent_sequence(self, tag, sequence, flow_style=None):
        # 如果 sequence 是一个非空列表
        if isinstance(sequence, list) and len(sequence) > 0:
            # 将 default_flow_style 设置为 False，表示使用块状风格（非流风格）
            self.default_flow_style = False
            self.default_style = ""
        # 调用父类的 represent_sequence 方法
        return super(MyDumper, self).represent_sequence(
            tag, sequence, flow_style=flow_style
        )


def write_singbox_config_to_file(
    output_singbox_dir,
    singbox_template,
    index,
    singbox_proxies_nodes,
    remarks_list,
):
    if singbox_proxies_nodes:
        if singbox_template:
            # 使用sing-box的配置文件模板，替换关键位置的值
            singbox_dict = update_singbox_value(
                remarks_list, singbox_proxies_nodes, singbox_template
            )
            # 1. 使用外部的sing-box模板，并将结果转换为json字符串
            singbox_json_str: str = json.dumps(singbox_dict, indent=2)
        else:
            # 2. 不使用外部的sing-box模板，并将结果转换为json字符串
            singbox_json_str = json.dumps(
                {"outbounds": singbox_proxies_nodes}, indent=2
            )

            # 写入文件
        output_file: str = f"{output_singbox_dir}/sing-box-{index + 1:04}.json"
        with open(
            output_file,
            mode="w",
            encoding="utf-8",
        ) as f:
            f.write(singbox_json_str)
        print(f"已生成配置文件：{output_file}")
    else:
        print("没有可用的节点，无法生成sing-box配置文件")


def write_clash_config_to_file(
    output_clash_dir,
    clash_template,
    index,
    clash_proxies_nodes,
    remarks_list,
):
    if clash_proxies_nodes:
        clash_dict: dict = {"proxies": clash_proxies_nodes}
        if clash_template:
            # 使用clash的配置文件模板，修改模板相关的值
            clash_dict = update_clash_value(
                remarks_list, clash_proxies_nodes, clash_template
            )

        # 使用自定义的 Dumper 类生成 YAML 字符串，并将 list 的数据缩进为 2 个空格
        clash_yaml_str = yaml.dump(
            clash_dict,
            Dumper=MyDumper,
            default_flow_style=False,
            sort_keys=False,
            indent=2,
            allow_unicode=True,  # 处理Unicode字符（图标的字符）
        )
        # 写入文件
        output_file: str = f"{output_clash_dir}/clash-{index + 1:04}.yaml"
        with open(
            output_file,
            mode="w",
            encoding="utf-8",
        ) as f:
            f.write(clash_yaml_str)
        print(f"已生成配置文件：{output_file}")
    else:
        print("没有可用的节点，无法生成clash配置文件")


if __name__ == "__main__":
    # 相关的文件、文件夹路径
    config_file: str = "Config.toml"
    result_csv_file = "result.csv"
    server_file: str = "server.txt"
    output_singbox_dir: str = "sing-box"
    output_clash_dir: str = "clash"
    singbox_file = "template/sing-box.template.json"
    clash_file = "template/clash.template.yaml"

    # 管理输出文件夹的文件：如果文件夹不存在则创建，存在就删除里面所有json、yaml文件
    for dir_path in [output_singbox_dir, output_clash_dir]:
        manage_output_directory(dir_path, [singbox_file, clash_file])

    # 读取result.csv文件内容
    server_list = read_csv_data(result_csv_file)
    if not server_list:  #  检查列表是否为空
        # 读取server.txt文件内容
        server_list: list = read_server_file_data(server_file)

    # 读取Config.toml文件内容，并获取不同类型的代理信息
    (
        checked_proxy_index,
        random_proxy_type,
        all_vless_proxies,
        all_trojan_proxies,
        all_proxies,
    ) = read_toml_parameter_values(config_file)

    if all_proxies:
        # 选择那些代理？(vless？trojan？还是混合vless和trojan协议的?)
        checked_proxies: list = select_proxies_list(
            checked_proxy_index,
            random_proxy_type,
            all_vless_proxies,
            all_trojan_proxies,
            all_proxies,
        )

        singbox_template: dict = read_singbox_template(singbox_file)
        clash_template: dict = read_clash_template(clash_file)

        # 子列表的长度，也是输出文件中，每个文件最大存储的节点数
        n = 50
        # 拆分一个列表为若干子列表（也就是拆分成一个嵌套列表、二维列表）
        chunks: list = list(
            server_list[i : i + n] for i in range(0, len(server_list), n)
        )

        for index, chunk in enumerate(chunks):
            remarks_list = []  # 存储每个节点对应的tag，别名

            singbox_proxies_nodes = []  # 存储每个文件对应的sing-box节点信息
            clash_proxies_nodes = []  # 存储每个文件对应的clash节点信息

            for server in chunk:
                # 从checked_proxies列表中，随机选中一个
                checked_proxy: dict = random.choice(checked_proxies)

                remarks_prefix: str = checked_proxy.get("remarks_prefix", "")
                random_ports: list = checked_proxy.get(
                    "random_ports",
                    [443],
                )
                # 随机选择一个端口
                port = random.choice(random_ports)
                # 节点别名
                tag = f"{remarks_prefix} | {server}:{port}"

                # 判断选择代理，其类型是vless？还是trojan？
                proxy_type: str = determining_proxy_type(checked_proxy)

                # 根据proxy_type的类型，选择哪个代理信息来构建节点？
                singbox_node: dict = build_singbox_node(
                    proxy_type, tag, server, int(port), checked_proxy
                )
                clash_node = build_clash_node(
                    proxy_type, tag, server, int(port), checked_proxy
                )

                # 判断是否需要添加到sing-box的singbox_proxies_nodes列表中？
                if singbox_node:
                    singbox_proxies_nodes.append(singbox_node)
                else:
                    continue

                # 判断是否需要添加到clash的clash_proxies_nodes列表中？
                if clash_node:
                    clash_proxies_nodes.append(clash_node)
                else:
                    continue

                # 别名
                remarks_list.append(tag)

            # 手动改为空字典（不使用模板），可以控制是否使用模板来生成配置文件
            singbox_template = dict()
            # clash_template = dict()

            # 深拷贝配置的模板，防止修改数据被影响
            copied_singbox_template: dict = copy.deepcopy(singbox_template)
            copied_clash_template: dict = copy.deepcopy(clash_template)

            # 写入sing-box配置文件
            write_singbox_config_to_file(
                output_singbox_dir,
                copied_singbox_template,
                index,
                singbox_proxies_nodes,
                remarks_list,
            )

            # 写入clash配置文件
            write_clash_config_to_file(
                output_clash_dir,
                copied_clash_template,
                index,
                clash_proxies_nodes,
                remarks_list,
            )
