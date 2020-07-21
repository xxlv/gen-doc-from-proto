# gen-doc-from-proto
Auto gen doc from proto file , base on comments 

# Dependency 
- protoc 
- protoc-gen-do see (https://github.com/pseudomuto/protoc-gen-do)
- python2.x

# How it work?

``` shell script
python process.py --scan path-to-proto --order 1
```

该自动扫描 path-to-proto 下的proto文件，并自动生成md文件，order代表生成文档的起始序列值.

# Scripts & Files

- log.txt 执行的命令log
- template.txt 每个服务生成的模版
- process_dir 将生成的md文件聚合成目录
- out/all.md 一次执行生成的包含目录的全部文档 md 格式