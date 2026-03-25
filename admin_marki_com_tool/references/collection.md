# 收款模块

本模块包含所有收款相关功能。

## 已实现功能

- **对指定房屋特定时间范围的账单进行收款** ✅ 已实现
  - 支持自然时间范围理解（"本月" → 自动转换为当月1日到今天）
  - 只支持现金支付
  - 支持用户选择部分账单收款

## 规划中的功能

- 物业费优惠减免
- 违约金减免
- 预存款充值
- 收取装修押金
- 生成缴费收据
- 退款/撤回缴费

---

## 可用命令

| 命令 | 说明 | 参数 |
|------|------|------|
| `collect_payment` | 对特定房屋指定时间范围的账单进行收款（推荐，智能匹配） | `收费系统名称 小区名称 房屋关键词 [开始日期 结束日期] [支付方式]` |
| `confirm_payment` | 确认收款，处理用户选择 | `yes/no/序号` |

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
5. 输出待收款账单列表供用户确认

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
# 对1栋/1单元/101的本月账单进行现金收款
python3 main.py collect_payment "收费系统" "XXX花园" "1栋/1单元/101" "2026-03-01" "2026-03-31" "现金"

# 确认收取全部账单
python3 main.py confirm_payment yes
```
