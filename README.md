# insar-process
批量处理InSAR脚本

## 1. export_master_slave_file.py

用于导出干涉对文件，具有以下特点：

1. 可以指定间隔多少个 
2. 指定最大的时间间隔 
3. 自定义分隔符号

### todo

1. 命令行中指定参数
 
## 2. batch_tops.py

批量处理哨兵1号数据脚本，具有以下特点：

1. 干涉对文件
   1. 可以只生成干涉对文件 
   2. 可以只使用本地修改后的干涉对文件进行处理
   3. 可以直接生成并使用干涉对文件
2. 可以在处理InSAR影像前将数据拷贝到处理目录(处理后删除)
3. 可以将处理后的giant需要的文件复制到指定目录，并删除本地文件【todo】
4. 可以将同一时间的同一轨道的数据作为一个master或slave的数据，导出到要处理的xml文件【todo】

## 3. unzipall.py

批量减压本路径中的zip文件