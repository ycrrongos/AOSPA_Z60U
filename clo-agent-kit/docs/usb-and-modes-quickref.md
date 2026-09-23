# Cerro USB / 刷机模式速查

## ID 表

| ID / 现象 | 含义 | 能否刷机 |
|-----------|------|----------|
| `05c6:9008` | Qualcomm EDL | ✅ `edl.py` |
| `18d1:d00d` | fastboot USB | ✅ 需 `fastboot devices` 有应答 |
| `19d2:0112` | ZTE MemoryDump | ❌ 非 EDL；强制关机再进 9008 |
| `1d6b:0104` | gadget / ACM | Linux 串口登录 |
| 解锁后立刻黑屏 | ABL 已交权 | 正常（无屏时无 logo） |

## 进 9008

长按电源关机 → **Vol+ 与 Vol− 同时按住**插 USB → `lsusb | grep 9008`

## 双槽口诀

刷 `boot_{a,b}`、`vendor_boot_{a,b}`（原厂），擦 `dtbo_{a,b}`。  
判定以 ACM/本枪标记为准，不能只看「最后能进系统」。

## AVB-off

刷自编 boot 前必须关 AVB：`pmos-flash/vbmeta.img` + `vbmeta_system.img` 写 **a/b 双槽**。  
或 `fastboot --disable-verity --disable-verification flash vbmeta* …`

## Firehose

**只用 v1**：`nubia_sm8650_eng/prog_ufs_firehose_sm8650_v1_ddr.elf`  
**勿用 v2**（平板用，Z60 Ultra 可能砖）。
