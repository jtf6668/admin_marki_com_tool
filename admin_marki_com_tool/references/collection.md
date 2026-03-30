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

## 规划中的功能

- 违约金减免
- 预存款充值
  - 收取装修押金                                                                                                                                    
- 生成缴费收据

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
