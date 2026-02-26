# K8s Resource Analyzer

K8s集群项目及命名空间资源使用率统计分析工具

## 安装

```bash
pip install -r requirements.txt
```

## 运行

```bash
cd k8s-resource-analyzer
uvicorn app.main:app --reload --port 8000 或者
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

访问 http://localhost:8000

## 功能

1. **配额管理**: 
   - Excel导入配额（云序号+项目名称为唯一键）
   - 删除配额

2. **日报上传**: 
   - Web界面上传多个日报文件
   - 文件名格式: `Day_report_YYYY-MM-DD`
   - 文件内容格式: `项目名称;命名空间;CPU使用量(核);内存使用量(bytes)`

3. **报表查看**: 
   - 按日期查看各项目CPU/内存使用率

4. **导出**: 
   - 选择日期范围导出Excel报告
   - 导出格式: 云序号、日期(Y/M/D)、CPU使用率%、内存使用率%
   
5. **数据同步（可定时）**: 
   - 接入k8s集群，同步项目及命名空间配额
   - 接入prometheus，同步容器进一天峰值总量，汇总计算项目资源使用率
     
## API

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | / | Web界面 |
| GET | /api/quotas | 获取配额列表 |
| POST | /api/quotas | 添加配额 |
| PUT | /api/quotas/{cloud_id} | 修改配额 |
| DELETE | /api/quotas/{cloud_id} | 删除配额 |
| POST | /api/quotas/import | Excel导入配额 |
| POST | /api/reports/upload | 上传日报文件 |
| GET | /api/reports | 获取已上传日期列表 |
| GET | /api/reports/{date} | 获取指定日期报表 |
| GET | /api/reports/export?dates=... | 导出Excel |
