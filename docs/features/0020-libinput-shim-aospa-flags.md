# 0020 — libinput_shim 对齐 AOSPA `int32_t` MotionEvent flags

## 问题

```
hardware/lineage/compat/libinput/Input.cpp:22:
error: no member named 'MotionFlag' in namespace 'android'
```

0007 从 229 Voltage 拷的 shim 把旧 ABI 转到 `ftl::Flags<android::MotionFlag>`。那是 Lineage 24 / Voltage 的 `MotionEvent::initialize`。AOSPA calcite 仍是：

```
void MotionEvent::initialize(..., int32_t flags, int32_t edgeFlags, ...);
```

没有 `android::MotionFlag`。

## 决策

`prebuilts-cerro/libinput_shim/Input.cpp`：删掉 Flags 那一档；旧的 `int displayId` 符号转到 AOSPA 现有的 `LogicalDisplayId` + `int32_t flags`（只声明、不定义，避免和 `libinput` 撞符号）。不要整仓覆盖 `frameworks/native`。

## 重放

```bash
bash scripts/apply-device-overlay.sh
```
