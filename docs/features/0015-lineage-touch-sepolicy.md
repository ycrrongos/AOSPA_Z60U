# 0015 — overlay 补 lineage_touch sepolicy（不要 inherit 整份 Lineage common）

## 问题

```
recovery_sepolicy.cil: unknown type hal_lineage_touch_default
allow hal_lineage_touch_default vendor_sysfs_touchpanel:dir { ... };
```

overlay 只有 `sepolicy/vendor/hal_lineage_touch_default.te` 的 `rw_dir_file(...)`，以及 `file_contexts` 把 `vendor.lineage.touch-service.nubia_sm8650` 标成 `hal_lineage_touch_default_exec`。类型定义在 Lineage `device/lineage/sepolicy/common/vendor/hal_lineage_touch_default.te`。

BoardConfig 只 include 了：

- `device/lineage/sepolicy/libperfmgr/sepolicy.mk`
- `device/qcom/sepolicy_vndr/SEPolicy.mk`

没有 `device/lineage/sepolicy/common/sepolicy.mk`。AOSPA 只带 `hal_lineage_health`，没有 `hal_lineage_touch`。

## 决策

**不要** inherit 整份 Lineage `common/sepolicy.mk`（public/private 会和 AOSPA 的 `hal_lineage_health` 属性、backuptool 等撞）。按 AOSPA `vendor/aospa/sepolicy` 的 health 写法，把 touch HAL 需要的属性/类型/service 放进 overlay：

| 路径 | 内容 |
|------|------|
| `sepolicy/public/attributes` | `hal_lineage_touch{,_client,_server}` |
| `sepolicy/vendor/hal_lineage_touch_default.te` | domain + exec + `init_daemon_domain` + sysfs |
| `sepolicy/vendor/hal_lineage_touch.te` | binder + `hal_attribute_service` |
| `sepolicy/vendor/service.te` | `hal_lineage_touch_service` |
| `sepolicy/vendor/service_contexts` | `vendor.lineage.touch.*` |
| `sepolicy/private/system_{server,app}.te` | `hal_client_domain` |

`BoardConfigCommon.mk` 增加 `SYSTEM_EXT_PUBLIC_SEPOLICY_DIRS += $(COMMON_PATH)/sepolicy/public`。

## 重放

```bash
bash scripts/apply-device-overlay.sh
```
