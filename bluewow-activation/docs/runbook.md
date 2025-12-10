# 部署与运行手册

## 本地开发
- 运行 `bash bluewow-activation/scripts/bootstrap.sh`
- 后端端口 `8088`，前端端口 `5173`
- 上传入口：打开 `http://localhost:5173/`，在“上传登录/激活名单”选择 `.csv` 或 `.xlsx`，点击“生成报告”。

## 云端部署
- 后端使用 Render 或 Railway，Docker 构建。
- 前端使用 Vercel 或 Cloudflare Pages。
- 配置环境变量：JWT_SECRET、FEISHU_*、ALLOWED_ORIGIN。
- 上传入口：访问你的 H5 域名，例如 `https://h5.your-domain/`。

## 飞书控制台
- 创建企业自建应用与权限配置。
- 设置事件回调与OAuth重定向。
- 加入域名白名单。
- 工作台入口打开H5上传页。

## 回滚
- 使用平台历史版本回滚。
- 恢复最近一次通过的镜像与构建。
