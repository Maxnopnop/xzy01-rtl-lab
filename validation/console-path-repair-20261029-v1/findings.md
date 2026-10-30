# 证据

原审计：request251、reservation255可写，transport-response262抛FileNotFoundError errno2，result250可写；原请求可能已发，UNKNOWN不变。根v3响应写入发生于send_once之后，异常未保留阶段/响应。GUI异常事件仅弹窗，不刷新package.rows。
