### 研究内容 
长期探测域名的历史信息（DNS、WHOIS、IP WHOIS、端口、网页内容） ,并且进行多维度分析信息


### 数据库
37服务器上mysql和mongodb数据库，数据库名称皆是：malicious_domain_history


### 文件和目录介绍

1. analysis_data目录
    * 功能：分析数据
2. get_whois_new目录
    * 功能：获取域名WHOIS信息
3. process_data目录: 处理数据
    * **cdn_finder** 目录用于发现CDN服务
    * **ip_location** 目录用于IP的地理位置定位
    * **old_mongo_code** 目录用于原来域名DNS记录探测，存入到mongo中，弃用
    * **raw_data** 目录，存放一些文件数据，忘记做什么了
    * **data_base.py** MySQL数据库基础操作
    * **fetch_mal_domain_dns.py** 批量获取域名DNS记录功能
    * **ip2location.py** IP地理位置定位功能
    * **merge_data.py** 对DNS记录进行预处理，包括删除单次探测空白和合并连续相同的数据
    * **mysql_config.py** 目标数据库配置
    * **obtaining_dns.py** 获取域名DNS记录
    * **system.conf** 系统配置文件，包括递归服务器地址、数据库存储地址和超时时间
    * **system_parameter.py** 读取系统配置文件
    
4. whois_code目录
    * 功能：处理域名WHOIS信息


### 常用数据库命令
```js
db.getCollection('domain_ttl').find({'data.ips':{'$not': {'$size': 0}}}).count(); //查询不为空的列表
db.getCollection('domain_ttl_new').find({'data.ips': {'$size': 0}}).count(); //查询为空的列表
db.getCollection('domain_ttl_new').remove({'data.ips': {'$size': 0}});  //查询列表为空的记录
```