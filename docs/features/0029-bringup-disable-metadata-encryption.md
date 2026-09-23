# 0029 — bringup：暂关 userdata metadata encryption

## 问题

卡努比亚第一屏。0027 ramoops 已生效（`vendor_boot` 内 DTB，`console_size=524288`），但夹具硬断电清 RAM。0028 bootdiag 写 `/metadata` 未出现 → 卡死多半在 **`post-fs` 之前**（常与首启 `/data` + wrappedkey metadata encryption / vold 相关）。

Voltage 同机 fstab 也用 `wrappedkey_v0`，能开机；AOSPA 上首启仍可能因 keymaster/TEE/ICE 路径不同挂死。

## 决策（临时）

`fstab.qcom` userdata **暂时去掉** `fileencryption=...wrappedkey_v0` 与 `metadata_encryption=...`，保留 `inlinecrypt` 挂载选项与其它 flag。原行留注释，修好后还原。

改完必须 **wipe metadata+userdata**（或 recovery factory reset），否则布局不一致。

## 重放

```bash
bash scripts/apply-device-overlay.sh
m vendorbootimage
# 注入/重编 vendor 使 /vendor/etc/fstab.qcom 一致（vendor_boot 里 first_stage fstab 必须同步）
fastboot flash vendor_boot vendor_boot.img
fastboot flash vendor vendor.img   # 或 vendor-bootdiag.img 流程
# recovery：Factory reset / format data
```

## 回滚

恢复注释中的 wrappedkey 行，删掉 bringup 行，再刷 vendor_boot+vendor 并 wipe。
