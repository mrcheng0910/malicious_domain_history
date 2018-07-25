### 研究内容 
长期探测域名的历史信息（DNS、WHOIS、IP WHOIS、端口、网页内容） 

多维度分析信息

### 常用数据库命令
```js
db.getCollection('domain_ttl').find({'data.ips':{'$not': {'$size': 0}}}).count(); //查询不为空的列表
db.getCollection('domain_ttl_new').find({'data.ips': {'$size': 0}}).count(); //查询为空的列表
db.getCollection('domain_ttl_new').remove({'data.ips': {'$size': 0}});  //查询列表为空的记录
```