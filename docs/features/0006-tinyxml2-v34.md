# 0006 — libtinyxml2-v34（nubia snapdragoncolor）

## 问题

soong：`libsnapdragoncolor-manager` 依赖 `libtinyxml2-v34`。
Lineage compat 在 `vndk/v34` 放这份预编译 `.so`。AOSPA 同仓 v34 只有 `libaudioroute-v34` / `libui-v34`。

## 决策

与 [0004](0004-protobuf-21.7-nubiaparts.md) 相同：**禁止**整仓覆盖 Lineage compat。从 229 Voltage 只拷 `arm`/`arm64` 的 `libtinyxml2-v34.so` 到 `prebuilts-cerro/libtinyxml2-v34/`，apply 时装进 AOSPA `hardware/lineage/compat/vndk/v34/` 并追加模块。

## 重放

```bash
bash scripts/apply-device-overlay.sh
```

`repo sync` 会还原 `hardware/lineage/compat`；必须再跑 apply。
