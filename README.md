# SwimDiary Production Ready

这是面向正式上线的 SwimDiary Web 生产版代码包，已经补齐了以下生产级能力：

- 移动端优先的分步式 SwimDiary Web 界面
- 用户分流：爱好者 / 进阶训练者 / 备赛用户 / 减脂用户
- 周计划优先，支持 4 / 6 / 8 周周期计划
- CSS 计算与 A1-A2 / EN1-EN3 / SP1-SP3 强度体系
- 训练反馈与持续跟踪看板
- Word / PDF 导出
- PostgreSQL 生产数据库支持
- Cloudflare R2 对象存储支持（截图 / 导出文件）
- Stripe Checkout + Webhook + Customer Portal
- Render 部署文件（Dockerfile / Procfile / render.yaml）

## 一、你还需要准备什么

正式上线前，你还需要自己准备这几个账号 / 资源：

1. GitHub 仓库（用于部署源码）
2. Render 账号（Web Service + PostgreSQL）
3. Stripe 账号（产品、价格、Webhook、Customer Portal）
4. Cloudflare 账号（R2 对象存储）
5. 自己的域名（建议）

## 二、本地运行

```bash
python -m pip install -r requirements.txt
python init_db.py
python app.py
```

浏览器打开：

```text
http://127.0.0.1:5050
```

## 三、本地测试版配置建议

如果你本地只是先跑功能，不接生产资源：
- 不填 `DATABASE_URL` 时默认使用 SQLite
- 不填 R2 时默认用本地文件目录
- 不填 Stripe 时支付入口会提示未配置

## 四、生产环境必须配置的环境变量

至少这些必须填：

- `APP_ENV=production`
- `SECRET_KEY`
- `BASE_URL`
- `DATABASE_URL`
- `STRIPE_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `STRIPE_PRICE_MONTHLY`
- `STRIPE_PRICE_YEARLY`
- `STORAGE_BACKEND=r2`
- `R2_ACCESS_KEY_ID`
- `R2_SECRET_ACCESS_KEY`
- `R2_BUCKET`
- `R2_ENDPOINT`

参考 `.env.example`。

## 五、Render 上线流程（推荐）

### 1）准备 GitHub 仓库
把整个项目推到 GitHub。

### 2）创建 Render Postgres
在 Render 后台创建 PostgreSQL 数据库。

### 3）创建 Render Web Service
连接 GitHub 仓库，选择本项目。

### 4）填环境变量
把 `.env.example` 里的生产变量都填到 Render。

### 5）首次部署
Render 会根据 `Dockerfile` 启动应用。

### 6）初始化数据库
部署成功后执行一次：

```bash
python init_db.py
```

### 7）配置 Stripe Webhook
Stripe Dashboard 中把 Webhook 地址指向：

```text
https://你的域名/api/billing/web/webhook
```

建议订阅这些事件：
- `checkout.session.completed`
- `customer.subscription.created`
- `customer.subscription.updated`
- `customer.subscription.deleted`
- `invoice.paid`
- `invoice.payment_failed`

### 8）绑定自定义域名
在 Render 中绑定你的域名，并配置 DNS。

## 六、Cloudflare R2 配置

### 要做的事
1. 创建一个 bucket，例如：`swimdiary-prod`
2. 创建 R2 API Token
3. 拿到：
   - Access Key ID
   - Secret Access Key
   - Endpoint
4. 填入环境变量

当前代码会把：
- 手表截图
- 导出文件
上传到 R2；如果你没配 R2，则退回本地目录（不建议生产这样用）。

## 七、Stripe 配置

### 你需要做的
1. 创建两个产品价格：月卡 / 年卡
2. 记录对应 `price_id`
3. 在 Dashboard 配置 Customer Portal
4. 在 Dashboard 配置 Webhook

当前代码已经支持：
- Checkout Session
- Webhook 订阅状态同步
- Customer Portal 跳转

## 八、生产注意事项

1. 生产环境务必关闭 `ALLOW_DEV_VIP`
2. 生产环境不要使用 SQLite
3. 生产环境不要把上传文件存在本地
4. 先用 Stripe 测试模式完整跑通一遍，再切到正式模式
5. `SECRET_KEY` 必须换成随机强密钥

## 九、当前边界

这版已经是可直接上线的生产版骨架，但有两个现实边界：

1. **手表截图分析**当前仍是“上传截图 + 用户补充关键指标”的稳妥模式，不是完全自动 OCR。
2. **数据库迁移**当前使用 `init_db.py` 做首发表结构创建，后续如果你频繁改表，建议再引入 Alembic / Flask-Migrate。

## 十、建议你的上线顺序

1. 本地跑通
2. Stripe 测试模式跑通支付
3. Render 测试环境部署
4. 绑定 R2
5. 绑定正式域名
6. 切正式 Stripe 密钥
7. 小范围邀请用户试用
8. 再正式公开
