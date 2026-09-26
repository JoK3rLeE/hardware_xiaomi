# SPDX-License-Identifier: Apache-2.0

SOONG_CONFIG_NAMESPACES += xiaomi_touch
SOONG_CONFIG_xiaomi_touch += touchscreen

ifeq ($(TARGET_OTA_ASSERT_DEVICE),cepheus)
    SOONG_CONFIG_xiaomi_touch_touchscreen := fts521
else ifneq ($(filter raphael raphaelin,$(TARGET_OTA_ASSERT_DEVICE)),)
    SOONG_CONFIG_xiaomi_touch_touchscreen := goodix
endif
