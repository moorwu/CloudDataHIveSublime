CloudDataHiveSublime 御膳房Hive的开发提速插件
====================

# 目标
【忍不住吐槽】clouddata.taobao.com 御膳房的hive table操作采用web 表单操作，但由于屏幕分辨率，浏览器限制等原因使得操作过程异常繁琐，进而降低了开发效率。
如果建表后发现某个字段有个小错误，还得删除重新来一遍，噩梦~~ $#@@!@#$%^
考虑到我们通常建表所需要的操作，此插件提供两个主要功能：
- 通过基础表定义的说明的网页url生成该基础表的字段明细：[字段名] [字段类型] [字段描述]
- 通过DDL定义自动完成私有表自动建表工作

*注：此插件仅适用于sublime text 2 版本*

# 安装前准备
- 安装Chrome浏览
- 下载对应操作系统版本的chromedriver 
-- https://code.google.com/p/chromedriver/
- 将chromedriver拷贝或者软链到默认系统path里（注意由于sublime启动插件的空间读取系统信息时无法读取后期加入的path，所以一定要放入系统默认的执行path下，比如/var/sbin 等），以便后期可以被正常调用到

# 安装
- 进入sublime的插件存储路径，比如在Mac下，它在 /Users/moor/Library/Application Support/Sublime Text 2/Packages/ 下
- 执行 git clone https://github.com/moorwu/CloudDataHIveSublime.git
- 重新启动Sublime text 2

# 使用
## 更改配置文件
- 进入刚刚clone下的文件夹，打开CloudData-Taobao.sublime-settings.sample
- 修改your_username_here 为你的御膳房用户名
- 修改your_password_here 为你的御膳房密码
- 修改your_app_key_here 为你正在工作的御膳房appkey
- 修改CloudData-Taobao.sublime-settings.sample 文件名为 CloudData-Taobao.sublime-settings

## 取得基础表的字段描述
- 首先取得通过浏览器访问得到基础表的定义界面 例如 http://clouddata.taobao.com/manage/table_view.htm?spm=0.0.0.0.EaUgE9&ftid=1&typeId=2&tableId=37626
- 将url拷贝到ST2的编辑区
- 选中该Url
- 按下 Ctrl-d, 然后再迅速点击d
- 随后系统会启动chrome自动访问该url
- 稍后系统会将取回的字段定义替换Urlmark

## 根据DDL自动创建私有表
- 在Sublime Text 2 下新建一个编辑区域
- 输入类似于如下的DDL定义

```Sql
create table  pri_result.sales_analysis_general(
thedate bigint COMMENT '日期，粒度是天',
shop_id bigint COMMENT '店铺ID',
seller_id bigint COMMENT '卖家的userid',
alipay_trade_num bigint COMMENT '统计周期内，用户成功完成（支付宝）支付的子订单数（一笔订单，按照商品分拆为多个子订单）。',
alipay_auction_num bigint COMMENT '通过支付宝付款的商品总件数',
alipay_trade_amt double COMMENT '成功完成支付宝支付的金额(元)',
alipay_winner_num bigint COMMENT '成功拍下并完成支付宝付款的人数',
gmv_auction_num bigint COMMENT '商品被拍下的总件数',
gmv_trade_amt double COMMENT '统计周期内，用户成功拍下的金额（以宝贝商品标价做计算）。',
gmv_trade_num bigint COMMENT '统计周期内，用户成功拍下的子订单数（一笔订单，按照商品分拆为多个子订单）。',
gmv_winner_num bigint COMMENT '成功拍下的人数。所选时间段内同一用户拍下多笔订单会进行去重计算。',
same_day_trade_num bigint COMMENT '当日拍下且当日通过支付宝付款的子订单数',
same_day_trade_amt double COMMENT '当日拍下且当日通过支付宝付款的金额',
same_day_auction_num bigint COMMENT '当日拍下且当日通过支付宝付款的商品件数',
trade_repeat_num bigint COMMENT '成交回头客人数',
succ_trade_amt double COMMENT '买家已收货的金额',
succ_trade_num bigint COMMENT '交易成功笔数',
succ_auction_num bigint COMMENT '买家已收货并验收的商品数',
pv bigint COMMENT '页面被查看的次数。用户多次打开或刷新同一个页面，该指标值累加。',
uv bigint COMMENT '页面的独立访问人数。所选时间段内，同一访客多次访问会进行去重计算。',
ipv bigint COMMENT '统计周期内，宝贝页面被浏览的次数。',
iuv bigint COMMENT '统计周期内，浏览宝贝页的独立访客数。',
visit_repeat_num bigint COMMENT '浏览回头客人数'
)comment '用于存储分析商家的每日销售概览数据'
with dbproperties('db_style':'结果表', 'theme':'商家主题', 'second_theme':'商家销售分析','export_time':'30')
with index ('index_1':'shop_id','index_2':'seller_id')
```
- 选中完整的DDL定义
- 按下 Ctrl-d, 然后再迅速点击c
- 随后系统会启动chrome
- 稍后系统会自动操作chrome完成数据表的建立

### DDL的解释
DDL	整体建表时所使用的DDL基本延续Hive的模型，但为了方便index的定义，增加了with index语法
- db_style：用于指定此表是结果表还是临时表等，直接输入在页面看到的内容
- theme：商家主题抑或其他你能看到的主题
- second_theme: 在一级主题下对应的二级主题条目，按照网页上看到的而你又需要的条目填写
- export_time: 导出时间，按照你需要选择7，30或者90填写
