# JMC Vehicle Control Testing

[![Vehicle API Tests](https://github.com/uuu523/jmc-vehicle-control-testing/actions/workflows/pytest.yml/badge.svg)](https://github.com/uuu523/jmc-vehicle-control-testing/actions/workflows/pytest.yml)

一个面向智能网联汽车软件质量岗位的自动化测试练习项目。

项目使用 Python、pytest 和 FastAPI，模拟车控 App 向云端发送远程解锁请求，并测试密码校验、车辆状态、异常处理、日志追踪、网络超时和状态确认等场景。

> 本项目是软件测试学习项目，车辆、T-BOX 和通信过程均为代码模拟，不连接真实车辆。

## 技术栈

- Python 3.13
- pytest
- FastAPI
- HTTPX TestClient
- pytest-html
- Git
- GitHub Actions

## 已实现的测试场景

### 密码校验

- 正确的六位数字密码
- 密码过短或过长
- 密码包含非数字字符
- 密码为空或缺失
- 格式正确但业务密码错误

### 远程解锁

- 正常解锁
- 用户未登录
- 车辆离线
- 车辆不存在
- 连续五次密码错误后锁定控制功能
- 锁定后输入正确密码仍不能解锁

### API测试

- `200`：解锁成功
- `400`：业务密码错误
- `404`：车辆不存在
- `409`：车辆离线
- `422`：请求参数格式错误
- `504`：车端响应超时

### 稳定性与可观测性

- 使用 Request ID 关联请求日志与响应日志
- 日志中不记录明文控制密码
- 使用 monkeypatch 模拟 T-BOX 超时
- 模拟车辆已执行命令但响应丢失
- 超时后查询车辆状态，确认最终执行结果
- 生成 pytest HTML 测试报告
- GitHub Actions 自动运行测试并保存报告

## 简化架构

```text
车控客户端
    │ HTTP请求
    ▼
FastAPI车控接口
    │
    ├── 参数格式校验
    ├── Request ID与日志
    ├── 业务状态码转换
    │
    ▼
车辆控制服务
    │
    ├── 登录及在线状态检查
    ├── 密码错误次数与锁定
    └── 模拟T-BOX通信及故障