# 收款模块

本模块包含所有收款相关功能。

## 已实现功能

- **对指定房屋特定时间范围的账单进行收款** ✅ 已实现
  - 支持自然时间范围理解（"本月" → 自动转换为当月1日到今天）
  - 支持按收费项目筛选（物业费、水费、电费等）
  - 支持现金、微信、支付宝多种支付方式
  - 支持用户选择部分账单收款

- **对已收款账单进行退款/撤回缴费** ✅ 已实现
  - 支持查询指定时间范围内已支付可退款账单
  - 支持按收费项目筛选
  - 支持用户选择部分账单退款
  - 只允许退款 `canRevoke=1` 标记的可退款账单

- **对指定账单进行优惠减免** ✅ 已实现
  - 支持对指定房屋某段时间某种费用的未付账单进行优惠减免
  - 支持固定金额减免
  - 自动检查是否有支付中订单（支付中不能优惠）
  - 支持用户选择部分账单进行优惠

- **设置违约金（违约金清零）** ✅ 已实现
  - 支持对指定房屋某段时间某种费用的账单设置违约金（通常用于清零）
  - 支持设置任意金额，默认值为 0（即清零）
  - 自动检查是否有支付中订单（支付中不能操作）
  - 支持用户选择部分账单进行处理

- **收取押金（装修押金、水电押金等）** ✅ 已实现
  - 支持对指定房屋收取各种类型的押金
  - 智能匹配已有押金项目，未找到时自动创建新项目
  - 支持现金、微信、支付宝多种支付方式
  - 两步确认模式，遵循统一交互规范

- **预存款充值** ✅ 已实现
  - 支持对指定房屋的指定类型预存款进行充值
  - 模糊匹配预存款账户类型
  - 支持现金、微信、支付宝多种支付方式
  - 两步确认模式，充值成功后显示余额变化

- **生成缴费收据** ✅ 已实现
  - 支持查询指定房屋最近缴费记录（默认最近24小时，适合"刚刚缴费"场景）
  - 可指定自定义时间范围
  - 区分已生成/未生成收据状态
  - 支持选择多条记录批量生成
  - 自动异步轮询生成结果，最终返回可直接访问的收据图片链接
  - 对已生成收据提供降级链接直接访问

## 规划中的功能

---

## 可用命令

| 命令 | 说明 | 参数 |
|------|------|------|
| `collect_payment` | 对特定房屋指定时间范围的账单进行收款（推荐，智能匹配） | `收费系统名称 小区名称 房屋关键词 [开始日期 结束日期] [收费项目] [支付方式]` |
| `confirm_payment` | 确认收款，处理用户选择 | `yes/no/序号` |
| `list_refundable_bills` | 查询指定房屋已缴可退款账单（推荐，智能匹配，两步完成） | `收费系统名称 小区名称 房屋关键词 [开始日期 结束日期] [收费项目]` |
| `confirm_refund` | 确认退款，处理用户选择 | `yes/no/序号` |
| `list_revocable_bills` | 查询指定房屋已缴可撤回账单（推荐，智能匹配，两步完成） | `收费系统名称 小区名称 房屋关键词 [开始日期 结束日期] [收费项目]` |
| `confirm_revoke` | 确认撤回已缴账单，处理用户选择 | `yes/no/序号` |
| `discount_bills` | 查询待优惠账单（推荐，智能匹配，两步完成） | `收费系统名称 小区名称 房屋关键词 [开始日期 结束日期] [收费项目] 优惠金额` |
| `confirm_discount` | 确认优惠，处理用户选择 | `yes/no/序号` |
| `clear_late_money` | 查询待处理账单，设置违约金（默认清零，推荐，智能匹配，两步完成） | `收费系统名称 小区名称 房屋关键词 [开始日期 结束日期] [收费项目] [设置金额]` |
| `confirm_clear_late_money` | 确认设置违约金，处理用户选择 | `yes/no/序号` |
| `collect_cash_pledge` | 收取押金（装修押金、水电押金等，推荐，智能匹配，两步完成） | `收费系统名称 小区名称 房屋关键词 押金名称 金额 [支付方式]` |
| `confirm_collect_cash_pledge` | 确认收取押金，处理用户选择 | `yes/no` |
| `recharge_deposit` | 预存款充值（水电费预存款、物业费预存款等，推荐，智能匹配，两步完成） | `收费系统名称 小区名称 房屋关键词 预存款类型 充值金额 [支付方式]` |
| `confirm_recharge_deposit` | 确认预存款充值，执行充值 | `yes/no` |
| `generate_receipt` | 生成缴费收据（查询最近缴费记录，默认最近24小时，推荐，智能匹配，两步完成） | `收费系统名称 小区名称 房屋关键词 [开始日期] [结束日期]` |
| `confirm_generate_receipt` | 确认生成收据，输出收据链接 | `yes/no/序号` |

---

## 支付方式映射

| 中文名称 | payType编码 |
|---------|---------|
| 现金 | 2 |
| 微信 | 1 |
| 支付宝 | 3 |
| 默认 | 2 (现金) |

AI自动映射用户输入的中文名称到对应编码。

---

## 处理流程 - 对指定房屋特定时间范围收款

### 第一步：查询待收款账单
```bash
python3 main.py collect_payment <收费系统名称> <小区名称> <房屋关键词> <开始日期> <结束日期> <支付方式>
```

系统会：
1. 匹配收费系统
2. 匹配小区
3. 匹配房屋（支持精确路径匹配如`1栋/1单元/101`，也支持模糊搜索）
4. 查询该房屋在指定时间范围内的未付账单
5. 输出待收款账单详情列表供用户确认

**示例输出：**
```
找到收费系统：XXX收费系统
找到小区：XXX花园
已选择房屋：1栋/1单元/101

### 待收款账单信息

**小区**: XXX花园
**房屋**: 1栋/1单元/101
**时间范围**: 2026-03-01 至 2026-03-25
**支付方式**: 现金
**待收款账单数**: 2 条
**总金额**: ¥ 258.00

账单列表:
1. 2026年03月 物业管理费 - ¥ 158.00
2. 2026年03月 公摊水费 - ¥ 100.00

请确认是否进行收款？
- 运行命令 `confirm_payment yes` 收取全部账单
- 运行命令 `confirm_payment <序号>`（如`confirm_payment 1`或`confirm_payment 1,2`）只收取指定账单
- 运行命令 `confirm_payment no` 取消
```

---

### 第二步：用户确认收款
根据你的选择运行对应的确认命令：

**收取全部账单：**
```bash
python3 main.py confirm_payment yes
```

**只收取第一个账单：**
```bash
python3 main.py confirm_payment 1
```

**取消：**
```bash
python3 main.py confirm_payment no
```

---

### 第三步：收款结果

**收款成功示例输出：**
```
✓ 收款成功！

**小区**: XXX花园
**房屋**: 1栋/1单元/101
**支付方式**: 现金
**收款账单数**: 2 条
**总金额**: ¥ 258.00
**交易时间**: 2026-03-25 14:30:00
```

**收款失败会输出错误信息，详情可查看日志。**

---

## API 说明

### 查询未付账单接口
- **端点**: `{CHARGE_API_BASE_URL}/mkg/api/v2/Charge/getCashierDeskListByIndex`
- **方法**: POST
- **Payload 格式**:
```json
{
  "communityID": 10587,
  "assetType": 1,
  "assetId": 310870,
  "payStatus": 0,
  "index": "",
  "selectChargeItemList": [],
  "selectChargeItemAll": false,
  "generateStartTime": 1772294400,
  "generateEndTime": 1774972799,
  "dealLogId": 0,
  "categoryId": 0,
  "sortType": 1,
  "chargeItemVersion": 2,
  "chargeItemCategorys": []
}
```
- **字段说明**:
  - `communityID`: 小区ID
  - `assetType`: 资产类型（1 = 房屋）
  - `assetId`: 房屋ID
  - `payStatus`: 付款状态（0 = 未付）
  - `generateStartTime`: 开始时间戳
  - `generateEndTime`: 结束时间戳
  - `selectChargeItemList`: 按收费项目ID筛选，为空数组表示不筛选

### 确认收款接口
- **端点**: `{CHARGE_API_BASE_URL}/mkg/api/v2/Charge/addBillPayV2`
- **方法**: POST
- **Payload 格式**:
```json
{
  "communityID": 10587,
  "payType": 2,
  "payTime": 1774430950,
  "billInfos": [
    {
      "id": 1062654084,
      "version": 0
    }
  ],
  "assetType": 1,
  "amount": 12135,
  "assetId": 310870,
  "houseId": 310870,
  "depositCheck": {
    "depositPayAmount": 12135,
    "leftPayAmount": 0
  },
  "version": 3
}
```
- **字段说明**:
  - `communityID`: 小区ID
  - `payType`: 支付方式（1 = 微信，2 = 现金，3 = 支付宝）
  - `payTime`: 当前时间戳
  - `billInfos`: 选中的账单信息数组，每个包含 `id` 和 `version`
  - `assetType`: 资产类型（1 = 房屋）
  - `assetId`: 房屋ID
  - `amount`: 总收款金额（单位：分）
  - `houseId`: 房屋ID（同 assetId）

---

## 使用示例

完整流程示例：
```bash
# 对1栋/1单元/101的本月账单进行现金收款（全部收费项目）
python3 main.py collect_payment "收费系统" "XXX花园" "1栋/1单元/101" "2026-03-01" "2026-03-31" "现金"

# 确认收取全部账单
python3 main.py confirm_payment yes
```

带收费项目筛选的示例：
```bash
# 对1栋/1单元/101的本月物业费进行现金收款（默认本月）
python3 main.py collect_payment "收费系统" "XXX花园" "1栋/1单元/101" "物业费" "现金"

# 指定时间范围，只收水费，微信支付
python3 main.py collect_payment "收费系统" "XXX花园" "1栋/1单元/101" "2026-03-01" "2026-03-31" "水费" "微信"

# 默认本月，只收物业费，默认现金支付
python3 main.py collect_payment "收费系统" "XXX花园" "1栋/1单元/101" "物业费"

# 确认收取全部筛选后的账单
python3 main.py confirm_payment yes
```

### 收费项目匹配说明
系统会智能匹配收费项目：
1. **精确匹配**：优先匹配名称完全一致的项目
2. **模糊匹配**：按关键词查找包含关键词的项目
3. **多个匹配**：如果找到多个匹配会提示你更精确指定
4. **不指定**：不指定收费项目则返回所有项目的账单

---

## 处理流程 - 对已收款账单进行退款

### 第一步：查询可退款账单
```bash
python3 main.py list_refundable_bills <收费系统名称> <小区名称> <房屋关键词> [开始日期] [结束日期] [收费项目]
```

系统会：
1. 匹配收费系统
2. 匹配小区
3. 匹配房屋（支持精确路径匹配如`1栋/1单元/101`，也支持模糊搜索）
4. 查询该房屋在指定时间范围内的已支付且可退款账单
5. 输出可退款账单详情列表供用户确认

**示例输出：**
```
找到收费系统：XXX收费系统
找到小区：XXX花园
已选择房屋：1栋/1单元/101

### 可退款账单信息

**小区**: XXX花园
**房屋**: 1栋/1单元/101
**时间范围**: 2026-03-01 至 2026-03-27
**可退款账单数**: 2 条
**总金额**: ¥ 258.00

账单列表按月份分组：

---
#### 2026年03月

1. **物业管理费**
   - 实缴金额: ¥ 158.00
   - 支付方式: 现金
   - 缴费时间: 2026-03-25 14:30:00
   - 交易单号: 394620
   - 可退款: 是

2. **公摊水费**
   - 实缴金额: ¥ 100.00
   - 支付方式: 微信
   - 缴费时间: 2026-03-25 14:30:00
   - 交易单号: 394621
   - 可退款: 是

---

请确认是否进行退款？
- 运行命令 `confirm_refund yes` 退款全部账单
- 运行命令 `confirm_refund <序号>`（如`confirm_refund 1`或`confirm_refund 1,2`）只退款指定账单
- 运行命令 `confirm_refund no` 取消
```

---

### 第二步：用户确认退款
根据你的选择运行对应的确认命令：

**退款全部账单：**
```bash
python3 main.py confirm_refund yes
```

**只退款第一个账单：**
```bash
python3 main.py confirm_refund 1
```

**取消：**
```bash
python3 main.py confirm_refund no
```

---

### 第三步：退款结果

**退款成功示例输出：**
```
✓ 退款成功！

**小区**: XXX花园
**房屋**: 1栋/1单元/101
**退款账单数**: 2 条
**总金额**: ¥ 258.00
**退款时间**: 2026-03-27 15:30:00

退款账单明细：
1. 2026年03月 物业管理费 - ¥ 158.00
2. 2026年03月 公摊水费 - ¥ 100.00
```

**退款失败会输出错误信息，详情可查看日志。部分退款成功会同时展示成功账单和失败账单。**

---

## API 说明

### 查询未付账单接口
- **端点**: `{CHARGE_API_BASE_URL}/mkg/api/v2/Charge/getCashierDeskListByIndex`
- **方法**: POST
- **Payload 格式**:
```json
{
  "communityID": 10587,
  "assetType": 1,
  "assetId": 310870,
  "payStatus": 0,
  "index": "",
  "selectChargeItemList": [],
  "selectChargeItemAll": false,
  "generateStartTime": 1772294400,
  "generateEndTime": 1774972799,
  "dealLogId": 0,
  "categoryId": 0,
  "sortType": 1,
  "chargeItemVersion": 2,
  "chargeItemCategorys": []
}
```
- **字段说明**:
  - `communityID`: 小区ID
  - `assetType`: 资产类型（1 = 房屋）
  - `assetId`: 房屋ID
  - `payStatus`: 付款状态（0 = 未付）
  - `generateStartTime`: 开始时间戳
  - `generateEndTime`: 结束时间戳
  - `selectChargeItemList`: 按收费项目ID筛选，为空数组表示不筛选

### 查询可退款账单接口
- **端点**: `{CHARGE_API_BASE_URL}/mkg/api/v2/Charge/getCashierDeskListByIndex`
- **方法**: POST
- **关键参数**: `payStatus: 1`（1 表示已支付）
- **Payload 格式**:
```json
{
  "communityID": 10587,
  "assetType": 1,
  "assetId": 310869,
  "payStatus": 1,
  "index": "",
  "selectChargeItemList": [],
  "selectChargeItemAll": false,
  "dealLogId": 0,
  "categoryId": 0,
  "chargeItemVersion": 2,
  "chargeItemCategorys": []
}
```
- **字段说明**:
  - `communityID`: 小区ID
  - `assetType`: 资产类型（1 = 房屋）
  - `assetId`: 房屋ID
  - `payStatus`: 付款状态（1 = 已支付，可退款）
  - `selectChargeItemList`: 按收费项目ID筛选，为空数组表示不筛选

### 确认收款接口
- **端点**: `{CHARGE_API_BASE_URL}/mkg/api/v2/Charge/addBillPayV2`
- **方法**: POST
- **Payload 格式**:
```json
{
  "communityID": 10587,
  "payType": 2,
  "payTime": 1774430950,
  "billInfos": [
    {
      "id": 1062654084,
      "version": 0
    }
  ],
  "assetType": 1,
  "amount": 12135,
  "assetId": 310870,
  "houseId": 310870,
  "depositCheck": {
    "depositPayAmount": 12135,
    "leftPayAmount": 0
  },
  "version": 3
}
```
- **字段说明**:
  - `communityID`: 小区ID
  - `payType`: 支付方式（1 = 微信，2 = 现金，3 = 支付宝）
  - `payTime`: 当前时间戳
  - `billInfos`: 选中的账单信息数组，每个包含 `id` 和 `version`
  - `assetType`: 资产类型（1 = 房屋）
  - `assetId`: 房屋ID
  - `amount`: 总收款金额（单位：分）
  - `houseId`: 房屋ID（同 assetId）

### 执行退款接口
- **端点**: `{CHARGE_API_BASE_URL}/mkg/api/v2/Charge/refundByDealLog`
- **方法**: POST
- **Payload 格式**:
```json
{
  "communityID": 10587,
  "dealLogId": 394620,
  "billId": 1011959044
}
```
- **字段说明**:
  - `communityID`: 小区ID
  - `dealLogId`: 交易日志ID（从查询接口获取）
  - `billId`: 账单ID（从查询接口获取）

### 执行撤回接口（已缴账单撤回）
- **端点**: `{CHARGE_API_BASE_URL}/mkg/api/v2/Charge/modBill`
- **方法**: POST
- **Payload 格式**:
```json
{
  "id": 981828295,
  "payStatus": 4,
  "version": 5
}
```
- **字段说明**:
  - `id`: 账单ID（从查询接口获取）
  - `payStatus`: 付款状态（固定值 `4` 表示撤回）
  - `version`: 账单版本号（从查询接口获取）

---

## 使用示例

### 收款完整流程示例
```bash
# 对1栋/1单元/101的本月账单进行现金收款（全部收费项目）
python3 main.py collect_payment "收费系统" "XXX花园" "1栋/1单元/101" "2026-03-01" "2026-03-31" "现金"

# 确认收取全部账单
python3 main.py confirm_payment yes
```

带收费项目筛选的收款示例：
```bash
# 对1栋/1单元/101的本月物业费进行现金收款（默认本月）
python3 main.py collect_payment "收费系统" "XXX花园" "1栋/1单元/101" "物业费" "现金"

# 指定时间范围，只收水费，微信支付
python3 main.py collect_payment "收费系统" "XXX花园" "1栋/1单元/101" "2026-03-01" "2026-03-31" "水费" "微信"

# 默认本月，只收物业费，默认现金支付
python3 main.py collect_payment "收费系统" "XXX花园" "1栋/1单元/101" "物业费"

# 确认收取全部筛选后的账单
python3 main.py confirm_payment yes
```

### 退款完整流程示例
```bash
# 查询1栋/1单元/101本月所有可退款账单
python3 main.py list_refundable_bills "收费系统" "XXX花园" "1栋/1单元/101"

# 确认退款全部账单
python3 main.py confirm_refund yes
```

带收费项目筛选的退款示例：
```bash
# 查询1栋/1单元/101本月物业费可退款账单（默认本月）
python3 main.py list_refundable_bills "收费系统" "XXX花园" "1栋/1单元/101" "物业费"

# 指定时间范围查询可退款账单
python3 main.py list_refundable_bills "收费系统" "XXX花园" "1栋/1单元/101" "2026-03-01" "2026-03-31" "物业费"

# 只退款第一个账单
python3 main.py confirm_refund 1
```

---

## 处理流程 - 对指定账单进行优惠减免

### 第一步：查询待优惠账单
```bash
python3 main.py discount_bills <收费系统名称> <小区名称> <房屋关键词> [开始日期] [结束日期] [收费项目] <优惠金额>
```

系统会：
1. 匹配收费系统
2. 匹配小区
3. 匹配房屋（支持精确路径匹配如`1栋/1单元/101`，也支持模糊搜索）
4. 查询该房屋在指定时间范围内的未付账单
5. 检查是否有正在支付中的订单（有则禁止操作）
6. 输出待优惠账单详情列表供用户确认

**示例输出：**
```
找到收费系统：XXX收费系统
找到小区：XXX花园
已选择房屋：1栋/1单元/101

### 待优惠账单信息

**小区**: XXX花园
**房屋**: 1栋/1单元/101
**时间范围**: 2026-03-01 至 2026-03-30
**优惠总金额**: ¥ 50.00
**待优惠账单数**: 1 条
**账单总金额**: ¥ 158.00

账单列表:
1. 2026年03月 物业管理费 - ¥ 158.00

请确认是否进行优惠减免？
- 运行命令 `confirm_discount yes` 优惠全部账单
- 运行命令 `confirm_discount <序号>`（如`confirm_discount 1`或`confirm_discount 1,2`）只优惠指定账单
- 运行命令 `confirm_discount no` 取消
```

---

### 第二步：用户确认优惠
根据你的选择运行对应的确认命令：

**优惠全部账单：**
```bash
python3 main.py confirm_discount yes
```

**只优惠第一个账单：**
```bash
python3 main.py confirm_discount 1
```

**取消：**
```bash
python3 main.py confirm_discount no
```

---

### 第三步：优惠结果

**优惠成功示例输出：**
```
✓ 优惠减免成功！

**小区**: XXX花园
**房屋**: 1栋/1单元/101
**优惠账单数**: 1 条
**优惠总金额**: ¥ 50.00
**处理时间**: 2026-03-30 15:30:00

优惠账单明细：
1. 2026年03月 物业管理费 - 原金额 ¥ 158.00 - 优惠 ¥ 50.00
```

**优惠失败会输出错误信息，详情可查看日志。**

---

## API 说明 - 优惠减免

### 查询未付账单接口
同收款模块，使用 `getCashierDeskListByIndex`，`payStatus: 0`（未支付）

### 检查支付中订单接口
- **端点**: `{CHARGE_API_BASE_URL}/mkg/api/v2/Charge/checkInPayBill`
- **方法**: POST
- **Payload 格式**:
```json
{
  "selectList": [1071763211, 1071763188]
}
```
- **响应格式**:
```json
{
  "code": 0,
  "msg": "",
  "data": {
    "hasInPay": false
  }
}
```
- **字段说明**:
  - `selectList`: 待检查的账单ID列表
  - `hasInPay`: `true` 表示有订单正在支付中，不能进行优惠操作；`false` 表示可以继续

### 执行优惠减免接口
- **端点**: `{CHARGE_API_BASE_URL}/mkg/api/v2/Charge/modDiscountOrLateMoney`
- **方法**: POST
- **Payload 格式**:
```json
{
  "communityID": 10587,
  "billIdList": [1071763211],
  "discountType": 1,
  "discountRate": 0,
  "amount": 5000,
  "amountType": 1
}
```
- **字段说明**:
  - `communityID`: 小区ID
  - `billIdList`: 要优惠的账单ID列表
  - `discountType`: `1` 表示金额减免（固定值）
  - `discountRate`: 折扣率，金额减免时固定为 `0`
  - `amount`: 优惠总金额，单位：分（如 50元 = 5000）
  - `amountType`: `1` 表示按金额减免（固定值）

### 异步结果轮询接口
优惠接口是异步执行，返回 `keyCode` 后需要轮询获取最终结果：
- **端点**: `{CHARGE_API_BASE_URL}/api/v1/GetAsyncResult?keyCode={keyCode}&r={random}`
- **方法**: GET
- **说明**: `r` 参数是随机数，防止缓存
- **轮询策略**: 每 2 秒轮询一次，最多轮询 10 次（20秒超时）

---

## 使用示例 - 优惠减免

完整流程示例：
```bash
# 对1栋/1单元/101的26年3月份物业费优惠50元（完整格式）
python3 main.py discount_bills "收费系统" "XXX花园" "1栋/1单元/101" "2026-03-01" "2026-03-31" "物业费" 50

# 确认优惠全部账单
python3 main.py confirm_discount yes
```

默认本月格式（自动使用当月1日到今天）：
```bash
# 对1栋/1单元/101本月物业费优惠50元（默认本月）
python3 main.py discount_bills "收费系统" "XXX花园" "1栋/1单元/101" "物业费" 50
```

不指定收费项目（对该时间段所有未付账单优惠）：
```bash
# 对1栋/1单元/101本月所有未付账单总共优惠100元
python3 main.py discount_bills "收费系统" "XXX花园" "1栋/1单元/101" 100
```

---

## 处理流程 - 设置违约金（违约金清零）

### 第一步：查询待处理账单
```bash
python3 main.py clear_late_money <收费系统名称> <小区名称> <房屋关键词> [开始日期] [结束日期] [收费项目] [设置金额]
```

系统会：
1. 匹配收费系统
2. 匹配小区
3. 匹配房屋（支持精确路径匹配如`1栋/1单元/101`，也支持模糊搜索）
4. 查询该房屋在指定时间范围内的未付账单
5. 检查是否有正在支付中的订单（有则禁止操作）
6. 输出待处理账单详情列表供用户确认

**示例输出（清零）：**
```
找到收费系统：XXX收费系统
找到小区：XXX花园
已选择房屋：1栋/1单元/101

### 待处理账单信息

**小区**: XXX花园
**房屋**: 1栋/1单元/101
**时间范围**: 2026-03-01 至 2026-03-30
**设置违约金金额**: ¥ 0.00
**待处理账单数**: 2 条
**原总违约金**: ¥ 25.50

账单列表:
1. 2026年03月 物业管理费 - 本金 ¥ 158.00, 当前违约金 ¥ 15.00
2. 2026年02月 公摊水费 - 本金 ¥ 100.00, 当前违约金 ¥ 10.50

请确认是否进行操作？
- 运行命令 `confirm_clear_late_money yes` 将所有账单违约金清零
- 运行命令 `confirm_clear_late_money <序号>`（如`confirm_clear_late_money 1`或`confirm_clear_late_money 1,2`）只处理指定账单
- 运行命令 `confirm_clear_late_money no` 取消
```

---

### 第二步：用户确认
根据你的选择运行对应的确认命令：

**清零全部账单：**
```bash
python3 main.py confirm_clear_late_money yes
```

**只处理第一个账单：**
```bash
python3 main.py confirm_clear_late_money 1
```

**取消：**
```bash
python3 main.py confirm_clear_late_money no
```

---

### 第三步：处理结果

**清零成功示例输出：**
```
✓ 设置违约金成功！

**小区**: XXX花园
**房屋**: 1栋/1单元/101
**处理账单数**: 2 条
**设置金额**: ¥ 0.00
**处理时间**: 2026-03-30 16:00:00

处理账单明细：
1. 2026年03月 物业管理费 - 本金 ¥ 158.00, 原违约金 ¥ 15.00 → 已清零
2. 2026年02月 公摊水费 - 本金 ¥ 100.00, 原违约金 ¥ 10.50 → 已清零
```

**处理失败会输出错误信息，详情可查看日志。**

---

## API 说明 - 设置违约金

### 查询待处理账单接口
同优惠减免模块，使用 `getCashierDeskListByIndex`，`payStatus: 0`（未支付）

### 检查支付中订单接口
同优惠减免模块，使用 `checkInPayBill`

### 执行设置违约金接口
- **端点**: `{CHARGE_API_BASE_URL}/mkg/api/v2/Charge/asyncModDiscountOrLateMoney`
- **方法**: POST
- **Payload 格式**:
```json
{
  "communityID": 10587,
  "billIdList": [1044467861, 1043881218],
  "amount": 0,
  "amountType": 2
}
```
- **字段说明**:
  - `communityID`: 小区ID
  - `billIdList`: 要处理的账单ID列表
  - `amount`: 设置的违约金金额，单位：分（0 表示清零）
  - `amountType`: `2` 表示设置违约金（固定值）

### 异步结果轮询接口
同优惠减免模块，使用 `GetAsyncResult`，轮询策略也完全一致：
- 每 2 秒轮询一次
- 最多轮询 10 次（20秒超时）

---

## 使用示例 - 设置违约金

### 违约金清零完整流程示例：

**默认本月清零所有账单违约金：**
```bash
# 对1栋/1单元/101本月所有账单违约金清零（默认本月，默认金额0即清零）
python3 main.py clear_late_money "收费系统" "XXX花园" "1栋/1单元/101"

# 确认清零全部账单
python3 main.py confirm_clear_late_money yes
```

**清零指定收费项目：**
```bash
# 对1栋/1单元/101本月物业费违约金清零（默认本月，默认金额0）
python3 main.py clear_late_money "收费系统" "XXX花园" "1栋/1单元/101" "物业费"

# 确认清零
python3 main.py confirm_clear_late_money yes
```

**指定时间范围：**
```bash
# 对1栋/1单元/101在2026-01-01至2026-03-31期间的物业费违约金清零
python3 main.py clear_late_money "收费系统" "XXX花园" "1栋/1单元/101" "2026-01-01" "2026-03-31" "物业费"

# 确认清零
python3 main.py confirm_clear_late_money yes
```

**设置指定金额：**
```bash
# 对1栋/1单元/101本月物业费违约金设置为总共10元
python3 main.py clear_late_money "收费系统" "XXX花园" "1栋/1单元/101" "物业费" 10

# 确认设置
python3 main.py confirm_clear_late_money yes
```

---

## 处理流程 - 收取押金

### 第一步：查询匹配押金项目
```bash
python3 main.py collect_cash_pledge <收费系统名称> <小区名称> <房屋关键词> <押金名称> <金额> [支付方式]
```

系统会：
1. 匹配收费系统
2. 匹配小区
3. 匹配房屋（支持精确路径匹配如`1栋/1单元/101`，也支持模糊搜索）
4. 查询该小区已有押金项目列表
5. 智能匹配押金项目（精确优先，模糊次之）
6. 未找到匹配则提示需要创建新项目
7. 输出待确认信息供用户确认

**示例输出（已有押金项目）：**
```
找到收费系统：XXX收费系统
找到小区：XXX花园
已选择房屋：1栋/1单元/101

### 待收取押金信息

**小区**: XXX花园
**房屋**: 1栋/1单元/101
**押金项目**: 装修押金
**押金金额**: ¥ 1000.00
**支付方式**: 现金

请确认是否收取押金？
- 运行命令 `confirm_collect_cash_pledge yes` 确认收取
- 运行命令 `confirm_collect_cash_pledge no` 取消
```

**示例输出（需要创建新项目）：**
```
找到收费系统：XXX收费系统
找到小区：XXX花园
已选择房屋：1栋/1单元/101

### 待收取押金信息

**小区**: XXX花园
**房屋**: 1栋/1单元/101
**押金项目**: 临时押金
**押金金额**: ¥ 500.00
**支付方式**: 微信

⚠ 未找到押金项目 '临时押金'，需要创建新项目。

请确认是否收取押金？
- 运行命令 `confirm_collect_cash_pledge yes` 确认创建并收取
- 运行命令 `confirm_collect_cash_pledge no` 取消
```

---

### 第二步：用户确认收取
根据你的选择运行对应的确认命令：

**确认收取：**
```bash
python3 main.py confirm_collect_cash_pledge yes
```

**取消：**
```bash
python3 main.py confirm_collect_cash_pledge no
```

---

### 第三步：收取结果

**收取成功示例输出：**
```
✓ 收取押金成功！

**小区**: XXX花园
**房屋**: 1栋/1单元/101
**押金项目**: 装修押金
**押金金额**: ¥ 1000.00
**支付方式**: 现金
**收取时间**: 2026-03-30 16:30:00
```

**收取失败会输出错误信息，详情可查看日志。**

---

## API 说明 - 收取押金

### 查询押金项目接口
- **端点**: `{CHARGE_API_BASE_URL}/mkg/api/v2/Charge/queryCashPledgeItem`
- **方法**: POST
- **Payload 格式**:
```json
{
  "communityID": 10587,
  "pageIndex": 1,
  "pageSize": 100
}
```
- **字段说明**:
  - `communityID`: 小区ID
  - `pageIndex`: 页码
  - `pageSize`: 每页数量

### 创建押金项目接口
- **端点**: `{CHARGE_API_BASE_URL}/mkg/api/v2/Charge/addCashPledgeItem`
- **方法**: POST
- **Payload 格式**:
```json
{
  "communityID": 10587,
  "pledgeName": "装修押金",
  "amount": 100000
}
```
- **字段说明**:
  - `communityID`: 小区ID
  - `pledgeName`: 押金项目名称
  - `amount`: 押金金额，单位：分（1000元 = 100000）

### 收取押金接口
- **端点**: `{CHARGE_API_BASE_URL}/mkg/api/v2/Charge/addCashPledgeOrder`
- **方法**: POST
- **Payload 格式**:
```json
{
  "communityID": 10587,
  "assetType": 1,
  "assetId": 310932,
  "pledgeItemId": 481,
  "amount": 100000,
  "payType": 2,
  "payTime": 1774859865
}
```
- **字段说明**:
  - `communityID`: 小区ID
  - `assetType`: 资产类型（1 = 房屋）
  - `assetId`: 房屋ID
  - `pledgeItemId`: 押金项目ID
  - `amount`: 押金金额，单位：分
  - `payType`: 支付方式（1 = 微信，2 = 现金，3 = 支付宝）
  - `payTime`: 支付时间戳

---

## 使用示例 - 收取押金

完整流程示例（已有押金项目）：
```bash
# 对1栋/1单元/101收取1000元装修押金，现金支付
python3 main.py collect_cash_pledge "收费系统" "XXX花园" "1栋/1单元/101" "装修押金" 1000

# 确认收取
python3 main.py confirm_collect_cash_pledge yes
```

完整流程示例（创建新项目并收取）：
```bash
# 对1栋/1单元/101收取500元临时押金，微信支付
python3 main.py collect_cash_pledge "收费系统" "XXX花园" "1栋/1单元/101" "临时押金" 500 微信

# 确认创建并收取
python3 main.py confirm_collect_cash_pledge yes
```

取消操作示例：
```bash
# 第一步查询匹配
python3 main.py collect_cash_pledge "收费系统" "XXX花园" "1栋/1单元/101" "装修押金" 1000

# 取消操作
python3 main.py confirm_collect_cash_pledge no
```

---

## 处理流程 - 预存款充值

### 第一步：查询匹配预存款账户
```bash
python3 main.py recharge_deposit <收费系统名称> <小区名称> <房屋关键词> <预存款类型> <充值金额> [支付方式]
```

系统会：
1. 匹配收费系统
2. 匹配小区
3. 匹配房屋（支持精确路径匹配如`1栋/1单元/101`，也支持模糊搜索）
4. 查询该房屋下所有预存款账户
5. 智能模糊匹配预存款类型
6. 输出待确认充值信息

**示例输出（单个匹配）：**
```
找到收费系统：XXX收费系统
找到小区：XXX花园
已选择房屋：1栋/1单元/101

找到预存款账户，请确认以下充值信息：
----------------------------------------
小区：测试小区
房屋：1栋/1单元/101
预存款账户：水电费 (categoryID: 123)
当前余额：¥ 50.00
充值金额：¥ 100.00
支付方式：现金
----------------------------------------
请确认是否执行充值？
- 运行命令 `confirm_recharge_deposit yes` 确认充值
- 运行命令 `confirm_recharge_deposit no` 取消
```

**多个预存款匹配：**
```
找到多个匹配的预存款账户，请选择：
1. 水电费 (当前余额：¥ 50.00)
2. 物业费预存款 (当前余额：¥ 100.00)
请输入序号选择：
```

**未找到预存款：**
```
当前房屋未找到匹配的预存款账户：
小区：测试小区
房屋：1栋/1单元/101
搜索类型：水电费
现有预存款账户：
- 物业费预存款 (余额：¥ 100.00)
- 燃气费预存款 (余额：¥ 200.00)
请确认预存款类型名称是否正确，或先在系统中创建该类型预存款账户。
```

---

### 第二步：用户确认充值
根据你的选择运行对应的确认命令：

**确认充值：**
```bash
python3 main.py confirm_recharge_deposit yes
```

**取消：**
```bash
python3 main.py confirm_recharge_deposit no
```

---

### 第三步：充值结果

**充值成功示例输出：**
```
✓ 预存款充值成功！
----------------------------------------
小区：测试小区
房屋：1栋/1单元/101
预存款类型：水电费
充值金额：¥ 100.00
支付方式：现金
原余额：¥ 50.00
新余额：¥ 150.00
充值时间：2026-03-30 18:29:52
----------------------------------------
```

**充值失败会输出错误信息，详情可查看日志。**

---

## API 说明 - 预存款充值

### 查询预存款账户接口
- **端点**: `{CHARGE_API_BASE_URL}/mkg/api/v2/Charge/getHouseDepositAccount`
- **方法**: GET
- **URL 参数**:
```
communityId=10587&houseId=310866
```
- **字段说明**:
  - `communityId`: 小区ID
  - `houseId`: 房屋ID

### 执行充值接口
- **端点**: `{CHARGE_API_BASE_URL}/mkg/api/v2/Charge/rechargeDepositV2`
- **方法**: POST
- **Payload 格式**:
```json
{
  "houseID": 310866,
  "open": 0,
  "payType": 2,
  "payTime": 1774858615,
  "categoryId": 0,
  "money": 10000
}
```
- **字段说明**:
  - `houseID`: 房屋ID
  - `open`: 是否允许自动扣款，固定为 `0`
  - `payType`: 支付方式（1 = 微信，2 = 现金，3 = 支付宝）
  - `payTime`: 当前时间戳
  - `categoryId`: 预存款分类ID
  - `money`: 充值金额，单位：分（100元 = 10000）

---

## 使用示例 - 预存款充值

完整流程示例：
```bash
# 对1栋/1单元/101的水电费预存款充值100元，现金支付
python3 main.py recharge_deposit "收费系统" "XXX花园" "1栋/1单元/101" "水电费" 100

# 确认充值
python3 main.py confirm_recharge_deposit yes
```

指定支付方式示例：
```bash
# 对1栋/1单元/101的物业费预存款充值200元，微信支付
python3 main.py recharge_deposit "收费系统" "XXX花园" "1栋/1单元/101" "物业费" 200 微信

# 确认充值
python3 main.py confirm_recharge_deposit yes
```

取消操作示例：
```bash
# 第一步查询匹配
python3 main.py recharge_deposit "收费系统" "XXX花园" "1栋/1单元/101" "水电费" 100

# 取消操作
python3 main.py confirm_recharge_deposit no
```

---

## 处理流程 - 生成缴费收据

### 第一步：查询最近缴费记录
```bash
python3 main.py generate_receipt <收费系统名称> <小区名称> <房屋关键词> [开始日期] [结束日期]
```

系统会：
1. 匹配收费系统
2. 匹配小区
3. 匹配房屋（支持精确路径匹配如`1栋/1单元/101`，也支持模糊搜索）
4. 查询该房屋在指定时间范围内的缴费记录
   - 不指定时间 → 默认最近24小时（适合"刚刚缴费"场景）
   - 指定时间 → 使用用户指定的起止日期
5. 按支付时间倒序排序
6. 区分`receiptState`（1=未生成，2=已生成）
7. 输出缴费记录列表供用户选择

**示例输出：**
```
找到 3 条缴费记录，请选择要生成收据的记录:

**小区**: XXX花园
**房屋**: 1栋/1单元/101
**时间范围**: 2026-03-30 10:00:00 至 2026-03-31 10:00:00

缴费记录列表：
1. [2026-03-31 09:15] ¥ 158.00 - 现金 - 物业管理费 (未生成)
2. [2026-03-30 14:30] ¥ 100.00 - 微信 - 公摊水费 (已生成)
3. [2026-03-30 10:20] ¥ 1000.00 - 现金 - 装修押金 (未生成)

请确认生成哪些收据：
- 运行命令 `confirm_generate_receipt yes` 生成全部
- 运行命令 `confirm_generate_receipt 1` 只生成第1条
- 运行命令 `confirm_generate_receipt 1,2` 生成第1、2条
- 运行命令 `confirm_generate_receipt no` 取消
```

---

### 第二步：用户确认生成
根据你的选择运行对应的确认命令：

**生成全部记录：**
```bash
python3 main.py confirm_generate_receipt yes
```

**只生成第一条：**
```bash
python3 main.py confirm_generate_receipt 1
```

**生成第1和第3条：**
```bash
python3 main.py confirm_generate_receipt 1,3
```

**取消：**
```bash
python3 main.py confirm_generate_receipt no
```

---

### 第三步：生成结果

**生成成功示例输出：**
```
✓ 收据生成完成！

**小区**: XXX花园
**房屋**: 1栋/1单元/101
**处理记录数**: 3 条
**成功**: 3 条
**处理时间**: 2026-03-31 10:00:00

收据链接：

1. [2026-03-31 09:15] ¥ 158.00
   生成成功
   https://charge-api-test.markiapp.com/receipt/abc123.png

2. [2026-03-30 14:30] ¥ 100.00
   已生成（直接获取）
   https://charge-api-test.markiapp.com/print.html?mode=receipt&colResize=1&search=eyJjb21tdW5pdHlJRCI6IjEwNTg3IiwiaWQiOiIxMDYxMjM0NTYiLCJyZWNlaXB0SWQiOiIiLCJyZWNlaXB0Q250Ijp0cnVlfQ==

3. [2026-03-30 10:20] ¥ 1000.00
   生成成功
   https://charge-api-test.markiapp.com/receipt/def456.png

💡 提示：点击链接可直接打开收据。
```

**生成失败会输出错误信息，如果API生成失败会自动降级使用手动构造链接，依然可以访问。**

---

## API 说明 - 生成缴费收据

### 查询缴费记录接口
- **端点**: `{CHARGE_API_BASE_URL}/mkg/api/v2/Charge/getPayLogListV2`
- **方法**: GET
- **URL 参数**:
```
receiptId=&payInvoiceStatus=
&startTime={start_timestamp}
&endTime={end_timestamp}
&communityID={community_id}
&page=1&pageSize=20
&assetName=&assetType=1&assetID={house_id}
&id=&payeeUidList=&payChannelList=&opUIDList=&remark=
&version=2&r={random}
```
- **字段说明**:
  - `startTime`: 开始时间戳
  - `endTime`: 结束时间戳
  - `communityID`: 小区ID
  - `assetID`: 房屋ID
  - `r`: 随机数防缓存

### 提交生成收据接口
- **端点**: `{CHARGE_API_BASE_URL}/mkg/api/v2/Charge/addPayReceiptV3`
- **方法**: POST
- **Payload 格式**:
```json
{
  "communityID": 10587,
  "id": 106123456,
  "version": 1,
  "requireImg": false,
  "from": 1
}
```
- **字段说明**:
  - `communityID`: 小区ID
  - `id`: 支付记录ID
  - `version`: 支付记录版本号
  - `requireImg`: 是否要求立即返回图片，我们使用异步所以填`false`
  - `from`: 来源，固定填`1`

### 异步结果轮询接口
提交成功后返回`resultCode`，需要轮询获取最终结果：
- **端点**: `{CHARGE_API_BASE_URL}/api/v1/GetAsyncResult?keyCode={resultCode}&r={random}`
- **方法**: GET
- **说明**: `r` 参数是随机数，防止缓存
- **轮询策略**: 每 2 秒轮询一次，最多轮询 10 次（20秒超时）
- **成功响应**: `{"code": 0, "data": "https://example.com/receipt.png"}`

### 手动构造收据URL（降级方案）
当收据已经生成过，或API生成失败时，使用此方式构造可访问的收据链接：
```
https://{CHARGE_API_DOMAIN}/print.html?mode=receipt&colResize=1&search={BASE64_JSON}
```
其中 `BASE64_JSON` 是对以下JSON进行base64编码：
```json
{"communityID":"{community_id}","id":"{pay_record_id}","receiptId":"","receiptCnt":true}
```

---

## 使用示例 - 生成缴费收据

完整流程示例（默认最近24小时，适用于刚刚缴费的场景）：
```bash
# 查询1栋/1单元/101最近24小时的缴费记录
python3 main.py generate_receipt "收费系统" "XXX花园" "1栋/1单元/101"

# 生成全部收据
python3 main.py confirm_generate_receipt yes
```

指定日期范围示例：
```bash
# 查询2026年3月份所有缴费记录
python3 main.py generate_receipt "收费系统" "XXX花园" "1栋/1单元/101" "2026-03-01" "2026-03-31"

# 只生成第一条收据
python3 main.py confirm_generate_receipt 1
```

只生成特定几条示例：
```bash
# 查询最近24小时
python3 main.py generate_receipt "收费系统" "XXX花园" "1栋/1单元/101"

# 选择生成第1和第3条
python3 main.py confirm_generate_receipt 1,3
```
