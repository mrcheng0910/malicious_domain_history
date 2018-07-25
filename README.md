# 域名历史信息分析

## 研究目标
分析非法网站（赌博和色情）及其内外链特征

## 研究方法
分别从链接、WHOIS、IP等角度，对网页及其外链域名的情况进行分析，根据程序进行详细的分析研究。


## 目录介绍
* analyze_data ，使用Jupyter Notebook对已获取的数据进行分析展示
* process_data，处理基础数据，包括获取、整理、存储等


## 数据库
使用mongodb数据库



## 常用数据库命令
```js
db.getCollection('domain_ttl').find({'data.ips':{'$not': {'$size': 0}}}).count(); //查询不为空的列表
db.getCollection('domain_ttl_new').find({'data.ips': {'$size': 0}}).count(); //查询为空的列表
db.getCollection('domain_ttl_new').remove({'data.ips': {'$size': 0}});  //查询列表为空的记录
```