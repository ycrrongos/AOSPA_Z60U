# 0021 — 内核 PERL 用系统 perl（tools-lineage perl 要 libcrypt.so.1）

## 问题

```
PERLASM arch/arm64/crypto/sha256-core.S
perl: error while loading shared libraries: libcrypt.so.1: cannot open shared object file
GEN lib/oid_registry_data.c
perl: ... libcrypt.so.1 ...
```

0019 的 clang 已能编 `fixdep` / dtb。内核 `PATH` 把 `prebuilts/tools-lineage/linux-x86/bin` 放最前，里面的 `perl` 链 `libcrypt.so.1`。本机 Fedora 44 只有 `libcrypt.so.2`（libxcrypt，无 compat）。

## 决策

`KERNEL_MAKE_FLAGS += PERL=/usr/bin/perl` 只覆盖用 `$(PERL)` 的配方（perlasm）。`lib/Makefile` 的 `oid_registry` **写死** `perl`，仍走 PATH 里 tools-lineage 那份。

overlay `build/host-bin/perl` 转到 `/usr/bin/perl`，并插到 PATH 最前。**不要**再设 `PERL5LIB=prebuilts/tools-lineage/common/perl-base`（那是 perl 5.26 的 XS，和本机 5.42 会报 `Cwd.c does not match v5.42.0`）。不要在仓库里塞 `libcrypt.so.1`。

## 重放

```bash
bash scripts/apply-device-overlay.sh
```
