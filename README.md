# JMC Connected Vehicle Quality Lab

[![Vehicle API Tests](https://github.com/uuu523/jmc-vehicle-control-testing/actions/workflows/pytest.yml/badge.svg)](https://github.com/uuu523/jmc-vehicle-control-testing/actions/workflows/pytest.yml)
![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)
![Coverage](https://img.shields.io/badge/core%20coverage-100%25-brightgreen)
![License](https://img.shields.io/badge/license-MIT-blue)

面向智能网联软件质量、测试流程与工具链岗位的学习项目。项目模拟车控客户端、云端 FastAPI、MQTT Broker 和 T-BOX 之间的远程解锁链路。

> 本项目只连接本地模拟服务，不连接真实车辆。控制密码、车辆状态和 T-BOX 均为教学实现。

## 项目亮点

- 构建 HTTP → MQTT → T-BOX → MQTT Result 的异步远程控制闭环
- 使用 `command_id` 处理 QoS 1 重复投递及指令冲突
- 覆盖超时、响应丢失、车辆离线、非法消息和密码锁定等故障场景
- 62 条自动化测试，8 个核心受测模块语句覆盖率 100%
- GitHub Actions 自动回归、90% 覆盖率门禁及 HTML/XML 报告制品

## 完整调用链

```text
客户端 POST /vehicles/JMC-001/commands/unlock
                    │
                    ▼
           FastAPI 返回 202 Accepted
           CommandStore 记录 pending
                    │
                    ▼ QoS 1
       vehicle/JMC-001/command
                    │
                    ▼
             T-BOX 模拟器执行解锁
                    │
                    ▼ QoS 1
        vehicle/JMC-001/result
                    │
                    ▼
       云端把状态更新为 success/failed
                    │
                    ▼
          GET /commands/{command_id}
```

## 技术栈

- Python 3.13、pytest、pytest-cov、pytest-html
- FastAPI、Uvicorn、HTTPX TestClient
- Eclipse Mosquitto、Paho MQTT、Docker Compose
- Git、GitHub Actions、覆盖率门禁和测试报告制品

## 模块职责

| 文件 | 职责 |
| --- | --- |
| `vehicle_control.py` | V1 密码校验、车辆状态和远程解锁业务 |
| `vehicle_api.py` | V1 同步 HTTP API、状态码、日志和超时处理 |
| `tbox_logic.py` | T-BOX 指令校验、解锁执行、幂等和冲突检测 |
| `command_store.py` | 云端指令的 `pending → success/failed` 状态管理 |
| `cloud_api.py` | V2 异步 API，接受指令并返回 `202` |
| `mqtt_publisher.py` | 把云端指令发布到车辆 command Topic |
| `mqtt_result_consumer.py` | 校验 T-BOX result 并更新指令状态 |
| `cloud_mqtt.py` | MQTT 连接、结果订阅及生命周期管理 |
| `cloud_runtime.py` | 组装 FastAPI、CommandStore 和 MQTT 的运行入口 |
| `scripts/tbox_simulator.py` | 模拟车载 T-BOX |

## 首次安装

在项目根目录打开 PowerShell：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install `
    --index-url https://pypi.org/simple `
    -r requirements.txt
```

启动本地 MQTT Broker：

```powershell
docker compose up -d
docker compose ps
```

## 运行完整系统

准备三个 PowerShell 终端，路径都切换到项目根目录。

终端一：启动 T-BOX 模拟器。

```powershell
.\.venv\Scripts\python.exe -m scripts.tbox_simulator
```

终端二：启动云端 API。启动时会连接 MQTT 并订阅 `vehicle/+/result`。

```powershell
.\.venv\Scripts\python.exe -m uvicorn `
    cloud_runtime:app `
    --host 127.0.0.1 `
    --port 8000
```

浏览器接口文档：<http://127.0.0.1:8000/docs>

终端三：发送解锁请求。

```powershell
$command = Invoke-RestMethod `
    -Method Post `
    -Uri "http://127.0.0.1:8000/vehicles/JMC-001/commands/unlock"

$command
```

响应中的状态最初是 `pending`。使用返回的 `command_id` 查询最终结果：

```powershell
Invoke-RestMethod `
    -Method Get `
    -Uri "http://127.0.0.1:8000/commands/$($command.command_id)"
```

正常结果应为：

```text
status      : success
door_locked : False
```

## 自动化测试

```powershell
.\.venv\Scripts\python.exe -m pytest -v `
    --cov=vehicle_control `
    --cov=vehicle_api `
    --cov=tbox_logic `
    --cov=command_store `
    --cov=cloud_api `
    --cov=mqtt_publisher `
    --cov=mqtt_result_consumer `
    --cov=cloud_mqtt `
    --cov-report=term-missing
```

生成 HTML 报告：

```powershell
.\.venv\Scripts\python.exe -m pytest `
    --html=reports/test-report.html `
    --self-contained-html
```

## 已覆盖的质量场景

- 六位数字密码的有效、无效等价类和边界值
- 用户未登录、车辆离线、车辆不存在、密码错误和连续输错锁定
- HTTP `200/202/400/404/409/422/503/504` 状态语义
- Request ID 日志关联，日志不记录明文密码
- T-BOX 请求超时、响应丢失和最终状态确认
- MQTT QoS 1、发布失败、确认超时和订阅失败
- 重复 `command_id` 幂等处理
- 相同 `command_id` 对应不同动作时拒绝执行
- MQTT 非法 JSON、未知指令和不匹配结果拒绝处理
- 指令状态不会被迟到的重复结果覆盖
- GitHub Actions 自动测试、覆盖率门禁和 HTML/XML 报告

## 学习时必须弄懂

1. **分层测试**：业务函数、HTTP API、MQTT 组件和完整链路分别测试，失败时才能快速定位。
2. **202 的含义**：只表示云端接受了请求，不表示车辆已经执行成功。
3. **异步状态机**：指令先是 `pending`，收到 T-BOX 结果后才进入 `success` 或 `failed`。
4. **QoS 1 与幂等**：QoS 1 是“至少一次”，可能重复投递，必须用 `command_id` 去重。
5. **Topic 设计**：云端发布 `vehicle/{id}/command`，T-BOX 返回 `vehicle/{id}/result`。
6. **测试替身**：单元测试用 Fake Client 隔离网络；真实 Broker 留给集成测试和手工验证。
7. **超时不是失败结论**：云端没及时收到响应，不代表车辆一定没有执行，需查询最终状态。
8. **可观测性**：Request ID、command ID、结构化日志和结果状态是排查链路问题的依据。
9. **CI 门禁**：每次提交自动运行回归测试，测试失败或覆盖率低于阈值时阻止合并。

## 当前边界与后续升级

- CommandStore 和 T-BOX 去重记录目前位于内存，进程重启会丢失；可升级为 SQLite/PostgreSQL/Redis。
- 本地 Mosquitto 为学习方便允许匿名连接；生产环境必须配置账号、ACL 和 TLS。
- 当前只模拟单车解锁；后续可增加上锁、鸣笛、车辆心跳、离线重连和多车辆并发。
- 当前项目不包含真实 CAN/UDS 通信；可以在下一阶段加入 CAN 信号和诊断服务测试。
