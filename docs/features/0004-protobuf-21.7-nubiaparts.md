# 0004 — nubia vendor protobuf 21.7 + NubiaParts resources

## 问题

soong namespace / FM 分区修完后：

- `vendor/nubia/*/Android.bp`：`undefined module "libprotobuf-cpp-full-21.7"`，随后还有 `libprotobuf-cpp-lite-21.7`
- `device/nubia/sm8650-common/parts/Android.bp`：`undefined module "org.lineageos.settings.resources"`

## 决策

**protobuf**：Lineage 把它放在 `hardware/lineage/compat` 的预编译 `.so`（SONAME `libprotobuf-cpp-full-21.7.so` / `libprotobuf-cpp-lite-21.7.so`）。AOSPA 已有 `hardware/lineage/compat`，但只有 3.9.1 / v29 vendorcompat。**禁止**整仓覆盖 Lineage compat。从 229 Voltage 的 compat 只拷对应 `.so` 到 `prebuilts-cerro/libprotobuf-cpp-{full,lite}-21.7/`，apply 时装进 AOSPA compat 并追加模块。

不能做成 `libprotobuf-cpp-full` 的 soong 别名：blob 的 `DT_NEEDED` 要的是带版本的 SONAME。先过 soong 的只有 full 时，lite 会在下一轮报同样的 undefined。

**NubiaParts**：AOSPA 把同仓 `packages/resources/devicesettings` 的模块名改成了 `co.aospa.resources`。overlay `parts/Android.bp` 改 static_libs。NubiaParts 目前不在 `PRODUCT_PACKAGES`，但 Soong 仍会解析该 `android_app`。风扇/扳机是硬件相关，保留源码。

## 重放

```bash
bash scripts/apply-device-overlay.sh
```

`repo sync` 会还原 `hardware/lineage/compat`；必须再跑 apply。
