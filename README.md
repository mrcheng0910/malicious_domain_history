# 域名历史信息分析

## 研究目标
分析非法网站（赌博和色情）及其内外链特征

## 研究方法
分别从DNS、WHOIS、网页内容等角度，根据程序进行详细的分析研究。


## 目录介绍
* process_data，dns记录
* get_whois_new, 获取whois信息


## 数据库
使用mongodb数据库
注意：存在历史信息的数据结构，不存储与上次重复的数据


## 常用数据库命令
```js
db.getCollection('domain_ttl').find({'data.ips':{'$not': {'$size': 0}}}).count(); //查询不为空的列表
db.getCollection('domain_ttl_new').find({'data.ips': {'$size': 0}}).count(); //查询为空的列表
db.getCollection('domain_ttl_new').remove({'data.ips': {'$size': 0}});  //查询列表为空的记录
```

### 特殊域名
001697.com，连续四次探测，其记录都不一样
