# 0022 — vendor Git LFS（NubiaCamera / radio）

## 问题

```
NubiaCamera signapk: java.util.zip.ZipException: zip END header not found
```

`vendor/nubia/cerro/proprietary/system/priv-app/NubiaCamera/NubiaCamera.apk` 实际是 Git LFS 指针（~134 字节 ASCII），不是 599MB APK。`radio/*.img` 和一份 camera bin 同样是指针。`repo sync` 默认不拉 LFS。

## 决策

`scripts/pull-vendor-lfs.sh`：对 `vendor/nubia/cerro` 和 `vendor/nubia/sm8650-common` 跑 `git lfs pull`（先 `source scripts/proxy-env.sh`）。挂进 `sync-calcite.sh`。不要把 599MB APK 拷进 overlay。

## 重放

```bash
source scripts/proxy-env.sh
bash scripts/pull-vendor-lfs.sh
```
