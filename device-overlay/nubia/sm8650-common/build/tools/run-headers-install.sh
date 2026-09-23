#!/usr/bin/env bash
# Run kernel headers_install + clean + audio UAPI stage for soong generated_kernel_includes.
# Avoids exporting KERNEL_MAKE_FLAGS through soong.variables (quotes break JSON).
set -euo pipefail

KERNEL_SRC="${1:?kernel src}"
OUT_DIR="${2:?headers out dir}"
ARCH="${3:?arch}"

TOP="$(pwd)"
HOST_TAG="${HOST_PREBUILT_TAG:-linux-x86}"

# Prefer Soong default clang (same as BoardConfigKernel / 0019).
CLANG_DIR=""
for c in \
  "$TOP/prebuilts/clang/host/$HOST_TAG"/clang-r* \
  "$TOP/prebuilts/clang/host/$HOST_TAG/clang-stable"
do
  if [[ -x "$c/bin/clang" ]]; then
    CLANG_DIR="$c"
    break
  fi
done
if [[ -z "$CLANG_DIR" ]]; then
  echo "run-headers-install: no clang under prebuilts/clang/host/$HOST_TAG" >&2
  exit 1
fi

MAKE="$TOP/prebuilts/build-tools/$HOST_TAG/bin/make"
[[ -x "$MAKE" ]] || MAKE=make

export PATH="$TOP/device/nubia/sm8650-common/build/host-bin:$TOP/prebuilts/tools-lineage/$HOST_TAG/bin:$CLANG_DIR/bin:$TOP/prebuilts/clang-tools/$HOST_TAG/bin:$PATH"
export BISON_PKGDATADIR="$TOP/prebuilts/build-tools/common/bison"
export HIP_PATH=none

SYSROOT="$TOP/prebuilts/gcc/linux-x86/host/x86_64-linux-glibc2.17-4.8/sysroot"
KBT="$TOP/prebuilts/kernel-build-tools/linux-x86"

HOSTCFLAGS="--sysroot=$SYSROOT -I$KBT/include"
HOSTLDFLAGS="--sysroot=$SYSROOT -Wl,-rpath,$KBT/lib64 -L $KBT/lib64 -fuse-ld=lld --rtlib=compiler-rt"

"$MAKE" -C "$KERNEL_SRC" O="$OUT_DIR" ARCH="$ARCH" \
  KBUILD_BUILD_USER=build-user \
  KBUILD_BUILD_HOST=build-host \
  HOSTAR="$CLANG_DIR/bin/llvm-ar" \
  HOSTCC="$CLANG_DIR/bin/clang" \
  HOSTLD="$CLANG_DIR/bin/ld.lld" \
  HOSTCXX="$CLANG_DIR/bin/clang++" \
  HOSTCFLAGS="$HOSTCFLAGS" \
  HOSTLDFLAGS="$HOSTLDFLAGS" \
  LD="$CLANG_DIR/bin/ld.lld" \
  AR="$CLANG_DIR/bin/llvm-ar" \
  LLVM=1 LLVM_IAS=1 \
  LEX="$TOP/prebuilts/build-tools/$HOST_TAG/bin/flex" \
  YACC="$TOP/prebuilts/build-tools/$HOST_TAG/bin/bison" \
  M4="$TOP/prebuilts/build-tools/$HOST_TAG/bin/m4" \
  LZ4="$KBT/bin/lz4" \
  PAHOLE="$KBT/bin/pahole" \
  LIBCLANG_PATH="$CLANG_DIR/lib" \
  PERL=/usr/bin/perl \
  headers_install

device/nubia/sm8650-common/build/tools/clean_headers.sh "$OUT_DIR"
device/nubia/sm8650-common/build/tools/stage-audio-kernel-uapi.sh "$OUT_DIR"
