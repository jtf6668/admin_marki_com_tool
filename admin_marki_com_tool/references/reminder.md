# 催费模块

本模块包含所有催费相关功能。

## 已实现功能

- 发送全小区微信缴费提醒
- **单个房屋短信催缴** ✅ 已实现
- **生成单个房屋催缴链接** ✅ 已实现
- **生成催缴工单** ✅ 已实现

## 规划中的功能

- 向欠费账期大于N个月的所有房屋进行短信催缴
- 向欠费金额大于N元的所有房屋进行短信催缴
- 生成单个房屋的纸质催缴通知单
- 创建电话催缴记录
- 自动拨打电话催缴

## 可用命令

| 命令 | 说明 | 参数 |
|------|------|------|
| `send_sms_reminder` | 单个房屋短信催缴（推荐，智能匹配） | `收费系统名称 小区名称 房屋关键词` |
| `confirm_sms_reminder` | 确认短信催缴发送处理 | `yes/no/序号` |
| `send_single_house_sms_reminder` | 单个房屋短信催缴（ID模式，备用） | `小区ID 房屋ID 业主ID逗号分隔 账单ID逗号分隔` |
| `send_wechat_reminder` | 全小区微信缴费提醒（智能匹配） | `收费系统名称 小区名称` |
| `send_community_wechat_reminder` | 通过小区ID发送微信缴费提醒 | `小区ID` |
| `generate_collection_url` | 生成房屋所有欠费账单的催缴链接（一步完成） | `收费系统名称 小区名称 房屋关键词` |
| `generate_charge_work_order` | 生成催缴工单（推荐，智能匹配，两步完成） | `收费系统名称 小区名称 房屋关键词` |
| `confirm_charge_work_order` | 确认选择代办人，生成催缴工单 | `序号` |

## 处理流程 - 单个房屋短信催缴

### 第一步：查询待发送信息
```bash
python3 main.py send_sms_reminder <收费系统名称> <小区名称> <房屋关键词>
```

系统会：
1. 匹配小区
2. 匹配房屋（支持精确路径匹配如`1栋/1单元/101`，也支持模糊搜索）
3. 查询该房屋的欠费信息
4. 提取业主ID列表和账单ID列表
5. 输出待确认信息供用户确认

**示例输出：**
```
找到小区：XXX花园
已选择房屋：1栋/1单元/101

### 待发送短信催缴信息

**小区**: XXX花园
**房屋**: 1栋/1单元/101
**欠费账单数**: 3 条
**业主列表**: 张三, 李四

请确认是否发送短信催缴？
- 运行命令 `confirm_sms_reminder yes` 发送给全部业主
- 运行命令 `confirm_sms_reminder <序号>`（如`confirm_sms_reminder 1`或`confirm_sms_reminder 1,2`）只发送给指定业主
- 运行命令 `confirm_sms_reminder no` 取消
```

### 第二步：用户确认发送
根据你的选择运行对应的确认命令：

**发送给全部业主：**
```bash
python3 main.py confirm_sms_reminder yes
```

**只发送给第一个业主：**
```bash
python3 main.py confirm_sms_reminder 1
```

**只发送给指定序号的业主：**
```bash
python3 main.py confirm_sms_reminder 1,2
```

**取消发送：**
```bash
python3 main.py confirm_sms_reminder no
```

### 第三步：发送结果

**发送成功示例输出：**
```
✓ 短信催缴发送成功！

**小区**: XXX花园
**房屋**: 1栋/1单元/101
**接收业主**: 张三, 李四
**账单数量**: 3
```

**发送失败会输出错误信息，详情可查看日志。**

## API 说明

### 发送短信接口
- **端点**: `{CHARGE_API_BASE_URL}/mkg/api/v2/Charge/sendMessage`
- **方法**: POST
- **Payload 格式**:
```json
{
    "sendType": 2,
    "templateId": -1,
    "uids": [12345, 67890],
    "assetType": 1,
    "assetId": 12345,
    "ids": [11111, 22222],
    "communityID": 123
}
```

- **字段说明**:
  - `sendType`: 2 = 短信发送
  - `templateId`: -1 = 使用默认模板
  - `uids`: 业主ID列表
  - `assetType`: 1 = 房屋
  - `assetId`: 房屋ID
  - `ids`: 账单ID列表
  - `communityID`: 小区ID

## 使用示例

完整流程示例：
```bash
# 第一步：查询并获取待确认信息
python3 main.py send_sms_reminder "我的收费系统" "XXX花园" "1栋/1单元/101"

# 第二步：确认发送给全部业主
python3 main.py confirm_sms_reminder yes
```

## 处理流程 - 生成催缴工单

### 第一步：查询待生成工单信息
```bash
python3 main.py generate_charge_work_order <收费系统名称> <小区名称> <房屋关键词>
```

系统会：
1. 匹配收费系统 → 获取绑定的团队ID
2. 匹配小区
3. 匹配房屋（支持精确路径匹配如`1栋/1单元/101`，也支持模糊搜索）
4. 查询该房屋的欠费信息
5. 检查当前用户是否在团队中
6. 添加支付通知
7. 生成催缴链接
8. 获取团队成员列表
9. 输出成员列表供用户选择

### 第二步：选择代办人生成工单
根据成员列表输出，选择指定序号的代办人：

**选择单个代办人：**
```bash
python3 main.py confirm_charge_work_order 1
```

**选择多个代办人：**
```bash
python3 main.py confirm_charge_work_order 1,2
```

### 输出示例（第一步）：
```
找到小区：XXX花园
已选择房屋：1栋/1单元/101
正在获取团队信息...
已绑定团队ID: 12345
正在检查用户团队权限...
正在生成催缴链接...
正在添加支付通知...
正在获取团队成员列表...

### 请选择代办人

**小区**: XXX花园
**房屋**: 1栋/1单元/101
**欠费账单数**: 3 条

请选择指定序号的团队成员作为代办人：

  1. 张三 (13800138000) - 用户ID: 12345
  2. 李四 (13900139000) - 用户ID: 12346

请运行命令确认选择：
  python3 main.py confirm_charge_work_order <序号>
示例：python3 main.py confirm_charge_work_order 1
支持多选：python3 main.py confirm_charge_work_order 1,2
```

### 输出示例（第二步）：
```
正在生成催缴工单...

✅ 催缴工单生成成功！

**小区**: XXX花园
**房屋**: 1栋/1单元/101
**欠费账单数**: 3 条
**指定代办人**: 张三 (13800138000)
**团队ID**: 12345
**支付通知ID**: 78901
**工单ID**: 123456
```

## 完整流程示例 - 生成催缴工单
```bash
# 第一步：查询并获取团队成员列表
python3 main.py generate_charge_work_order "我的收费系统" "XXX花园" "1栋/1单元/101"

# 第二步：确认选择第一个成员作为代办人生成工单
python3 main.py confirm_charge_work_order 1
```
