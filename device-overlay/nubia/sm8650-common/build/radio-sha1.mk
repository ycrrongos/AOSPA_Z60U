#
# AOSPA cerro: Lineage extract-utils writes
#   $(call add-radio-file-sha1-checked,radio/foo.img,<sha1>)
# into vendor/nubia/cerro/Android.mk. AOSPA has add-radio-file but not
# this wrapper (it lives in vendor/lineage). Must be included from
# BoardConfig so the define exists before that Android.mk is parsed.
# Do not put this in build/tasks/ — those load after Android.mk.
#

# $(call add-radio-file-sha1-checked,path,sha1)
define add-radio-file-sha1-checked
  $(eval path := $(LOCAL_PATH)/$(1))
  $(eval sha1 := $(shell sha1sum "$(path)" | cut -d" " -f 1))
  $(if $(filter $(sha1),$(2)),
    $(call add-radio-file,$(1)),
    $(error $(path) SHA1 mismatch ($(sha1) != $(2))))
endef
