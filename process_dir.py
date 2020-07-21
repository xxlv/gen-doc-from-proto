#!/usr/bin/python
# -*- coding: utf-8 -*-


import os
import re
import sys
from datetime import datetime

reload(sys)
sys.setdefaultencoding('utf-8')

MD_PATH = "out/md"
T_PATH = "./out/dir.md"
TEMPLATE = "./dir_template.txt"
OUT_ALL = "./out/all.md"


def _process_mds():
    r = []
    # loop
    file_list = os.listdir(MD_PATH)
    for filename in file_list:
        filepath = os.path.join(MD_PATH, filename)
        if os.path.isfile(filepath):
            with open(filepath, "r") as f:
                r.extend(_process_md(f.read()))

    return r


def _process_md(str_md):
    str_md = str(str_md).decode("utf-8")
    l = []
    p_order = re.compile(r"####\s(\d+\.\d+)")
    p_desc = re.compile(ur'描述：\*\*\n\n-\s([\u4e00-\u9fa5]*.*)\n\n')
    p_api = re.compile(ur'请求API：\*\*\n-\s(.*)\n\n')
    p_service = re.compile(ur'服务：\*\*\n-\s(.*)\n\n')

    desc = p_desc.findall(str_md)
    order = p_order.findall(str_md)
    api = p_api.findall(str_md)
    service = p_service.findall(str_md)

    for i in range(len(desc)):
        if service.__len__() > i:
            ser = service[i]
        else:
            ser = ""
        l.append({"api": api[i] + "", "desc": desc[i], "order": (order[i]), "service": ser})

    return l


def _compile_with_template(l, t):
    template = _load_simple_file(t)
    s = ""
    for i in l:
        service = " - "
        if i.has_key("service"):
            service = i.get("service").encode("utf-8")
        s += "|{}|{}|{}|{}|\n".format(_warp_with_href_mark(i["order"].encode("utf-8"), i["order"].encode("utf-8")),
                                      service,
                                      i["api"].encode("utf-8"),
                                      i["desc"].encode("utf-8"))

    return template.replace("${dirLoopParams}", s)


def _warp_with_href_mark(s, order):
    return "[{}](#{})".format(s, str(order).replace(".", ""))


def _load_simple_file(path):
    with open(path, "r") as f:
        s = f.read()
    return s


def _merge_md_with_dir():
    d = _load_simple_file(T_PATH)
    file_list = os.listdir(MD_PATH)
    for filename in file_list:
        filepath = os.path.join(MD_PATH, filename)
        if os.path.isfile(filepath):
            d += _load_simple_file(filepath)

    return d


def process_dir():
    print "Process dir"
    with open(T_PATH, "w+") as f:
        l = _process_mds()
        l = sorted(l, key=lambda e: float(e.__getitem__('order')), reverse=False)
        dt = datetime.now()

        data = _compile_with_template(l, TEMPLATE)
        now_date = dt.strftime("%Y-%m-%d %H:%M:%S")
        data = """Total:**{}**\t更新时间:**{}**\n\n|序号|服务|接口|接口摘要|\n|:---- |:-----|:----- |----- |""".format(len(l),
                                                                                                         now_date) + data
        f.write(data)

    with open(OUT_ALL, "w+") as f:
        f.write(_merge_md_with_dir())


if __name__ == "__main__":
    process_dir()
