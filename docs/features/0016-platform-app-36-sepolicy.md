# 0016 — 去掉 recovery 没有的 `platform_app_36`

## 问题

```
recovery_sepolicy.cil: unknown type platform_app_36
allow platform_app_36 hal_camera_default:binder { call transfer };
```

0015 的 `hal_lineage_touch_default` 过了之后，checkpolicy 编到 `sepolicy/vendor/platform_app.te`。

## 决策

Plasma 给 NubiaCamera（API 36）加了显式 `platform_app_36` 规则。那是 Treble 冻结映射类型，只出现在 **vendor** 对 plat 的 compat 策略里；**recovery** 是一份单体策略，只有 `platform_app`。

overlay 同一文件里已经有等价的 `platform_app` binder / service_manager / `vendor_zte_prop`。删掉 Plasma 那四行，不要在 overlay 里 `type platform_app_36`（会和真正的 vendor mapping 撞）。

## 重放

```bash
bash scripts/apply-device-overlay.sh
```
