# K8s Resource Analyzer

K8s集群项目及命名空间资源使用率统计分析工具

## 介绍

K8s Resource Analyzer 是一款专为Kubernetes集群设计的资源使用率统计分析工具。它能够自动从K8s集群和Prometheus获取资源配额和使用数据，帮助运维团队有效监控和分析多集群、多项目的资源使用情况。

## 核心特性

- 🚀 **多集群支持** - 同时管理多个K8s集群，统一查看资源配额和使用率
- 🎯 **精确同步** - 基于副本数去重的同步算法，完美支持滚动更新场景
- 📊 **智能计算** - 自动按项目汇总命名空间资源使用量，结合配额计算使用率
- ⏰ **定时任务** - 自动定时同步K8s配额和Prometheus数据，无需人工干预
- 📥 **批量操作** - 支持K8s集群、Prometheus配置的批量导入
- 📑 **灵活导出** - 多日期导出，标准Excel格式，10位小数精度

## 安装

```bash
pip install -r requirements.txt
```

## 运行

```bash
cd k8s-resource-analyzer
uvicorn app.main:app --reload --port 8000
# 或
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

访问 http://localhost:8000

## 功能

1. **项目配额管理** - 项目级CPU、内存配额配置，支持K8s同步、手动导入Excel、批量操作

2. **命名空间配额管理** - K8s命名空间级资源配额（CPU、内存、Pod、存储）管理，实时显示使用率

3. **多K8s集群支持** - 支持配置多个K8s集群，统一管理项目及命名空间配额

4. **Prometheus集成** - 配置多个Prometheus实例，自动采集容器资源使用数据

5. **准确数据同步** - 基于副本数去重的精确同步算法，适合滚动更新场景，解决新旧Pod交替导致的数据抖动问题

6. **日报上传** - Web界面拖拽上传，支持多文件批量处理，自动解析日期和内容

7. **报表查看** - 按日期筛选查看，支持颜色区分使用率高低（高≥80%、中≥50%、低<50%）

8. **Excel导出** - 选择多个日期导出，标准格式：主键/周期/CPU利用率/内存利用率，10位小数精度

9. **定时任务** - 自动定时同步K8s配额和Prometheus数据，可配置同步时间

## API

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | / | Web界面 |
| GET | /api/quotas | 获取项目配额列表 |
| POST | /api/quotas | 添加项目配额 |
| PUT | /api/quotas/{cloud_id} | 修改项目配额 |
| DELETE | /api/quotas/{cloud_id} | 删除项目配额 |
| POST | /api/quotas/import | Excel导入项目配额 |
| GET | /api/k8s/configs | 获取K8s集群配置列表 |
| POST | /api/k8s/configs | 添加K8s集群配置 |
| DELETE | /api/k8s/configs/{id} | 删除K8s集群配置 |
| POST | /api/k8s/sync | 同步命名空间配额 |
| POST | /api/k8s/sync-project-quota | 同步项目配额 |
| POST | /api/k8s/configs/import | 批量导入K8s集群配置 |
| GET | /api/k8s/quotas | 获取命名空间配额列表 |
| DELETE | /api/k8s/quotas/{cluster}/{namespace} | 删除命名空间配额 |
| POST | /api/k8s/quotas/import | 批量导入命名空间配额 |
| GET | /api/prometheus/configs | 获取Prometheus配置列表 |
| POST | /api/prometheus/configs | 添加Prometheus配置 |
| DELETE | /api/prometheus/configs/{id} | 删除Prometheus配置 |
| POST | /api/prometheus/sync | 同步Prometheus数据 |
| POST | /api/prometheus/import | 批量导入Prometheus配置 |
| GET | /api/scheduler/config | 获取定时任务配置 |
| POST | /api/scheduler/config | 更新定时任务配置 |
| POST | /api/reports/upload | 上传日报文件 |
| GET | /api/reports | 获取已上传日期列表 |
| GET | /api/reports/{date} | 获取指定日期报表 |
| GET | /api/reports/export?dates=... | 导出Excel |

## 模板下载

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | /api/templates/quota | 下载项目配额模板 |
| GET | /api/templates/report | 下载日报模板 |
| GET | /api/templates/namespace-quota | 下载命名空间配额模板 |
| GET | /api/templates/k8s-config | 下载K8s配置模板 |
| GET | /api/templates/prometheus-config | 下载Prometheus配置模板 |

## 效果图

<img width="2560" height="1271" alt="image" src="https://github.com/user-attachments/assets/281b3d9e-b222-4131-afbf-f4151415166e" />
<img width="2560" height="1271" alt="image" src="https://github.com/user-attachments/assets/0572a801-5b1d-4a76-a061-96b1c02a64f2" />
<img width="2560" height="1271" alt="image" src="https://github.com/user-attachments/assets/7456fe36-e19d-4bae-b398-208593aedd61" />
<img width="2560" height="1271" alt="image" src="https://github.com/user-attachments/assets/14818d84-b69b-4268-ad05-ecab513e033a" />
<img width="2560" height="1271" alt="image" src="https://github.com/user-attachments/assets/f19c88cb-647a-46f6-8e86-99da4933fc68" />
<img width="2560" height="1271" alt="image" src="https://github.com/user-attachments/assets/53a3248d-04d0-4d47-b7ea-0af734b9cf0b" />
<img width="2560" height="1271" alt="image" src="https://github.com/user-attachments/assets/6decc47c-ebe2-4b29-8df7-5936d1c95141" />
<img width="2560" height="1271" alt="image" src="https://github.com/user-attachments/assets/f74c9254-665f-406e-8b35-cfecc9554e30" />

## 技术栈

- **后端**: Python 3.10 + FastAPI
- **前端**: HTML + JavaScript + Bootstrap
- **数据处理**: openpyxl
- **API集成**: Kubernetes Client, Prometheus Client
- **开发工具**: OpenCode

## 文档

详细开发文档请查看 [开发文档](./docs/开发文档.md)

## GitHub

https://github.com/Linus-cat/k8s-resource-analyzer
