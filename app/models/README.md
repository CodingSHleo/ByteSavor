# models - 数据库表结构

| 文件 | 对应的表 | 干什么的 |
|------|---------|---------|
| `__init__.py` | users / profiles / nutrition_logs / feedback | 用户系统四张表 |
| recipe.py | recipes | 菜谱表，目前用 JSON 存食材列表和标签（后期如果数据量大可以拆成独立表） |

表会在服务启动时自动创建，种子数据（10 道菜谱）也会同时导入。
