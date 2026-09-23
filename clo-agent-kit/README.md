# CLO Agent Kit — Nubia Z60 Ultra (cerro)

类原生 / CLO ROM 开发与刷机用的**便携工具包**（脚本 + EDL + 关 AVB 镜像 + 文档）。

## 快速开始

```bash
cd tools/edl-tools
./install-udev.sh      # 一次，需 sudo
./setup-edl-venv.sh    # 一次
source ./edl-env.sh
lsusb | grep 9008      # 确认 EDL
edl printgpt
```

**Agent 请先读**：[`AGENT-HANDOFF.md`](AGENT-HANDOFF.md)

## 含什么

- Qualcomm **9008** 刷机脚本（双槽 boot、AOSP fastbootd、监听刷机等）
- **bkerler/edl** 源码 + **SM8650 v1** firehose
- **AVB 关闭**用 `vbmeta.img` / `vbmeta_system.img`
- USB 判定、**舵机刷机夹**（STL + 固件/校准/进 9008）
- 硬件与 bootloader 评估摘要

## 不含什么

- ROM 编译产物、完整分区备份、Python venv（需 `setup-edl-venv.sh` 生成）

来源仓库：`LOA_Nubia_Z60U`（与 ArtistAOSP 刷机脚本同源，路径已尽量相对化）。
