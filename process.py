#!/usr/bin/python3
# -*- coding:utf-8-*-


import json
import os
import argparse
import sys
import process_dir
import toml

# --------------------------------------------------------------------------------------------------
# 将proto文件转化成md
# 如 python process.py --order 1 --scan
# 将扫描path-to-proto 下所有 *Service.proto 的文件并根据注释生成md文档
# --------------------------------------------------------------------------------------------------
TARGET_PROTO_SUFFIX = "Service.proto"
OUT = "./out/out.md"  # default out file
TEMPLATE = "template.txt"
JSON_FILE = "./out/data.json"  # default json file
LOG = "./log.txt"
OUT_PATH = "./out/md"
CONFIG_PATH = "./config.toml"

global_config = toml.load(CONFIG_PATH)


def _load_simple_file(path):
    with open(path, "r") as f:
        s = f.read()
    return s


def load_template():
    return _load_simple_file(TEMPLATE)


def _to_dict_message(messages):
    message_dict = {}
    for message in messages:
        message_dict[message['name']] = message
    return message_dict


def _get_message_dict(files):
    messages_dict = {}
    for f in files:
        messages_dict.update(_to_dict_message(f['messages']))
    return messages_dict


def gen_doc(package, json_file, out_file, order):
    template = load_template()
    index = 0
    all_json_str = _load_simple_file(json_file)
    all_json_object = json.loads(all_json_str)
    files = all_json_object['files']
    api_doc = ""
    messages_dict = _get_message_dict(files)
    for f in files:
        for methods in f['services']:
            for method in methods['methods']:
                index += 1
                api_doc += build_md_from_json_with_template(methods['fullName'], method, messages_dict, template,
                                                            package,
                                                            "{}.{}".format(order, index)) + "\r\n\r\n"
    write_to(api_doc, out_file, "w+")
    print "create new file {} successful!".format(out_file)


def build_md_from_json_with_template(fullName, method, messages_dict, template, package, order):
    try:
        dep = 4
        desc = method['description'].encode("utf-8")
        method_name = method['name'].encode("utf-8")
        in_p = messages_dict[method['requestType']]
        resp_type = method['responseType']
        if messages_dict.has_key(resp_type):
            out_p = messages_dict.get(resp_type)
        else:
            out_p = None

        template = template.replace("${method.description}", desc)
        template = template.replace("${method.name}", method_name)
        template = template.replace("${package}", package)
        template = template.replace("${ReqLoopParams}", _build_params_str(in_p, messages_dict))
        template = template.replace("${RespLoopParams}", _build_params_str(out_p, messages_dict))
        template = template.replace("${method.fullName}", "{} {}".format(desc, method_name))
        template = template.replace("${service.name}", "{}/{}".format(str(fullName).split("proto.")[1], method_name))
        template = template.replace("${jsonOfResponse}", "{}".format(_build_json(out_p, messages_dict, dep)))
        template = template.replace("${order}", "{}".format(order))
        template = template.replace("${order_without_dot}", "{}".format(order.replace(".", "")))

        return template
    except Exception as e:
        print "compiling template failed Err:[{}]".format(e.message)
        return ""


def _get_space(count):
    s = ""
    for i in range(count):
        s += " "
    return s


def _build_json(p, messages_dict, dep):
    j = "{\r\n\r\n"
    for field in p['fields']:
        if messages_dict.has_key(field['type']) and messages_dict[field['type']]['name'] != p['name']:

            j += "{}{}:{}    \r\n".format(_get_space(dep), field['name'].encode("utf-8"),
                                          "{}  ".format(
                                              _build_json(messages_dict[field['type']], messages_dict, dep + 4)))

        else:
            j += "{}{}:{}    \r\n".format(_get_space(dep), field['name'].encode("utf-8"),
                                          "{} ".format(field['type'].encode("utf-8")) + field[
                                              'description'].encode("utf-8"))

    j += "\r\n    }\r\n\r\n"

    return j


def _build_params_str(p, messages_dict):
    if p is None:
        return ""
    params = p['fields']
    p_str = ""
    for param in params:
        if str(param['fullType'].encode("utf-8")).__contains__("."):
            pass
        p_str += "|{}|{}|{}| \r\n".format(param['name'].encode("utf-8"),
                                          "{} ".format(param['label'].encode("utf-8")) + param['type'].encode(
                                              "utf-8"),
                                          param['description'].encode("utf-8"))
    return p_str


def write_to(p_str, path, mode="w+"):
    with open(path, mode) as f:
        f.write(p_str)


def _compile_and_write_proto_to_json(proto, proto_path, json_file):
    """
     protoc --doc_out=../out --proto_path path --doc_opt=json,Data.json Data.proto
    :param proto:
    :param json_file:
    :return:
    """
    if proto_path is None:
        proto_path = "/".join(proto.split("/")[:-1])

    proto = proto.replace(",", " ")
    json_file = json_file.replace(",", "-")
    cmd = """
    protoc --doc_out=./out --proto_path {} --doc_opt=json,{} {}
    """.format(proto_path, json_file, proto)
    signal = os.system(cmd)

    if signal != 0:
        proto_path = "/".join(proto.split("/")[:-2])
        print "received signal {} failed ,try {}".format(signal, proto_path)
        cmd = """
        protoc --doc_out=./out --proto_path {} --doc_opt=json,{} {}
        """.format(proto_path, json_file, proto)
        signal = os.system(cmd)
    print "{}".format(cmd)

    print "signal is {}".format(signal)
    return json_file


def build_with_proto(proto_path_or_file, package_name, json_file_gen, out_file, order_nu, proto_base_path):
    if package_name is None:
        package_name = "rpc"

    if json_file_gen is None:
        json_file_gen = JSON_FILE
    if proto_path_or_file is None:
        raise Exception("proto file not exists")
    if out_file is None:
        out_file = OUT
    if json_file_gen is None:
        raise Exception("you need provide a valid json file ,please check proto generator ")

    _compile_and_write_proto_to_json(proto_path_or_file, proto_base_path, json_file_gen)

    gen_doc(package_name, json_file_gen, out_file, order_nu)


def _clean_md_dir():
    for file in os.listdir(OUT_PATH):
        current_file = os.path.join(OUT_PATH, file)
        os.remove(current_file)
        print "clean file {}".format(current_file)


def _check_dependency():
    import subprocess
    try:
        p = subprocess.Popen(["protoc", "--version"], stdout=subprocess.PIPE)
        out = p.stdout.read()
    except Exception as e:
        out = ""
    if not out.__contains__("libprotoc 3.11.3"):
        print "--------------------------------------------------------------------------------------------------------"
        print "miss required dependency protoc , use shell ``` brew install protoc ``` install the dependency first"
        print "plugin: More information see wiki https://github.com/pseudomuto/protoc-gen-doc"
        print "--------------------------------------------------------------------------------------------------------"
        sys.exit(-1)


def _check_is_valid(proto):
    if str(proto.split("/")[-1]).endswith(TARGET_PROTO_SUFFIX):
        return True
    return False


def _get_package(base, proto):
    ignore_keys = "ignore_package_names"
    ignore_key = "ignore_package_name"

    if base is None or len(base) <= 0:
        base = str(proto.split("src/")[0].split("/")[-2]).replace("-proto", "")
        if global_config.has_key(ignore_keys):
            for c in global_config[ignore_keys]:
                if dict(c).has_key(ignore_key):
                    base = base.replace(c[ignore_key], "")

    base = base.split("-")[0]
    proto_list = proto.split("/")
    p = proto_list[-1].replace(global_config['ignore_proto']['ignore_proto_suffix'], "")

    return "{}.{}".format(_get_name(base), str(p[0]).lower() + p[1:])


def _get_name(name):
    print name
    for t in global_config['rewrite_name']:
        if dict(t).has_key('source_name') and t['source_name'] == name:
            return t['target_name']
    return name


if __name__ == "__main__":

    _clean_md_dir()
    _check_dependency()
    # ------------------------------------------------------------------------------------------------------------------
    parser = argparse.ArgumentParser(description='Generate api doc from proto file')
    parser.add_argument('--proto', help='proto file path', required=False)
    parser.add_argument('--package', help='package name , api prefix ', default=None)
    parser.add_argument('--out', help='out file name', default=None)
    parser.add_argument('--json_file', help='gen json file name', default=None)
    parser.add_argument('--order', help='gen order, gen api title like 1.1', default=1)
    parser.add_argument('--proto_base_path', help='the proto base path, default current file dir')
    parser.add_argument('--scan', help='specify scan path')

    args = parser.parse_args()
    _proto = args.proto
    out = args.out
    scan = args.scan
    json_file = args.json_file
    order = args.order
    package = args.package
    proto_base_path = args.proto_base_path

    # process files of specify dir
    protos = []
    if scan is not None:
        for file in os.listdir(scan):
            current_file = os.path.join(scan, file)
            protos.append(current_file)
    else:
        protos = [_proto]

    final_protos = []
    for p in protos:
        if _check_is_valid(p):
            final_protos.append(p)

    #  batch gen
    for proto in final_protos:
        final_package = _get_package(package, proto)
        # create log record
        cmd = "python process.py --proto {} --package {} --order {}".format(proto, final_package, order)
        if proto_base_path is not None:
            cmd += "  --proto_base_path {}".format(proto_base_path)
        cmd += "\n"
        print "--------------------------------------------------------------------------------------------------------"
        print cmd
        print "--------------------------------------------------------------------------------------------------------"

        out = "./out/md/" + "-".join(proto.split("/")[1:]) + "_{}.md".format(order)
        out = out.replace("*", "all")
        out = out.lower()

        if json_file is None:
            json_file = "./out/" + "-".join(proto.split("/")[1:]) + ".json"
            json_file = json_file.replace("*", "all")
            json_file = json_file.replace(",", "")
            json_file = json_file.lower()
        # --------------------------------------------------------------------------------------------------------------
        build_with_proto(proto, final_package, json_file, out, order, proto_base_path)
        # log
        write_to(cmd, LOG, "a+")
        order = int(order) + 1

    process_dir.process_dir()
