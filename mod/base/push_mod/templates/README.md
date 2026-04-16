# 告警模板目录

本目录存放内置告警任务的 JSON 模板文件。

## 添加新模板

### 1. 编写任务类

创建一个继承 `BaseTask` 的类，必须实现以下方法：

```python
from mod.base.push_mod.base_task import BaseTask
from typing import Union, Optional, Tuple

class MyAlertTask(BaseTask):
    def __init__(self):
        super().__init__()
        self.source_name = "my_alert"     # 告警来源标识
        self.template_name = "My Alert"   # 模板名称

    def check_task_data(self, task_data: dict) -> Union[dict, str]:
        """校验用户输入的告警参数，返回修正后的 dict 或错误字符串"""
        return task_data

    def get_keyword(self, task_data: dict) -> str:
        """返回唯一关键字，用于查询/执行任务"""
        return "my_keyword"

    def get_push_data(self, task_id: str, task_data: dict) -> Optional[dict]:
        """判断是否触发告警，触发返回包含 msg_list 的 dict，否则返回 None"""
        return {"msg_list": ["alert message"]}

    def filter_template(self, template: dict) -> Optional[dict]:
        """过滤模板（如依赖环境不存在则返回 None 隐藏该模板）"""
        return template

    def to_sms_msg(self, push_data: dict, push_public_data: dict) -> Tuple[str, dict]:
        """短信格式化，返回 (type, args)"""
        return '', {}
```

> 其他 `to_xxx_msg` 方法（钉钉/飞书/邮件/Telegram 等）由 `BaseTask` 提供默认实现，一般无需重写。

### 2. 创建 JSON 模板

新建文件 `<your_module>_push_template.json`，命名以 `_push_template.json` 结尾：

```json
[
  {
    "id": "999",
    "ver": "1",
    "used": true,
    "source": "my_alert",
    "title": "My Alert Title",
    "load_cls": {
      "load_type": "path",
      "cls_path": "mod.base.push_mod.your_module",
      "name": "MyAlertTask"
    },
    "template": {
      "field": [],
      "sorted": []
    },
    "default": {},
    "advanced_default": {
      "number_rule": {"day_num": 3}
    },
    "send_type_list": ["dingding", "feishu", "mail", "weixin", "webhook", "tg", "..."]
  }
]
```

### 字段说明

| 字段 | 说明                                             |
|------|------------------------------------------------|
| `id` | 唯一 ID（字符串），不要与已有模板冲突                           |
| `ver` | 版本号                                            |
| `used` | 是否启用                                           |
| `source` | 告警来源，与任务类的 `source_name` 对应                    |
| `title` | 模板显示名称                                         |
| `load_cls` | 类加载配置：`load_type` 为 `path`（模块路径）或 `func`（函数调用） |
| `template.field` | 前端表单字段定义                                       |
| `template.sorted` | 表单字段分组排序                                       |
| `default` | 表单默认值                                          |
| `advanced_default` | 高级设置默认值（频率/时间规则）                               |
| `send_type_list` | 支持的告警通道列表 ('ALL' 为全部, 增加通道后自动增加, 默认'ALL'即可)    | 

### 3. 放入本目录

将 JSON 文件放入此目录即可，`update_mod()` 自动扫描

### 4. 注意事项

- `id` 必须全局唯一
- `cls_path` 中的模块必须存在且可导入
- 任务类必须放在 `load_cls.cls_path` 指定的模块中
- 若模板依赖特定插件/环境，在 `filter_template` 中返回 `None` 可隐藏该模板

### # 注意: site_push.py 中带有多种类型的综合性告警, 多处硬编码引用, 因此不修改文件名.
