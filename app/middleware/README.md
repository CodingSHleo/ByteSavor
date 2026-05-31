# middleware - 中间件

| 文件 | 干什么的 |
|------|---------|
| auth.py | 身份认证。`get_current_user` 强制校验 token（比如查个人资料），`get_optional_user` 可选的（比如推荐菜谱，登录不登录都能用） |
