#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Patch PhoneWindowManager for Xiaomi AI key (Linux scan code 689)."""
from pathlib import Path

target = Path("frameworks/base/services/core/java/com/android/server/policy/PhoneWindowManager.java")
if not target.is_file():
    raise SystemExit(f"Run from the Android source root; missing {target}")
src = target.read_text()
if "handleXiaomiAiKey()" in src:
    raise SystemExit("AI key handler already exists; refusing to patch twice.")

case_marker = "        // If the key would be handled globally, just return the result, don't worry about special"
helper_marker = "    // There are several different flavors of"
if src.count(case_marker) != 1 or src.count(helper_marker) != 1:
    raise SystemExit("Unexpected PhoneWindowManager layout; no files changed.")

# Match the physical Linux scan code directly. Its Android keycode depends on
# the device's active .kl mapping, which is being corrected separately.
scan_code_handler = """        // Xiaomi AI Key: Linux KEY_MACRO_RECORD_STOP, scan code 689.
        if (event.getScanCode() == 689) {
            result &= ~ACTION_PASS_TO_USER;
            if (down && event.getRepeatCount() == 0 && interactive && !keyguardActive) {
                handleXiaomiAiKey();
            }
            return result;
        }

"""
handler = """    private void handleXiaomiAiKey() {
        final ContentResolver resolver = mContext.getContentResolver();
        final String action = Settings.System.getStringForUser(
                resolver, "xiaomi_ai_key_action", UserHandle.USER_CURRENT);
        if (action == null || "disabled".equals(action)) return;

        if ("assistant".equals(action)) {
            launchAssistAction(null, INVALID_INPUT_DEVICE_ID, SystemClock.uptimeMillis(),
                    AssistUtils.INVOCATION_TYPE_UNKNOWN);
            return;
        }

        final Intent intent;
        if ("gemini".equals(action)) {
            intent = new Intent(Intent.ACTION_MAIN);
            intent.addCategory(Intent.CATEGORY_LAUNCHER);
            intent.setPackage("com.google.android.apps.bard");
            if (mContext.getPackageManager().resolveActivityAsUser(
                    intent, 0, UserHandle.USER_CURRENT) == null) {
                launchAssistAction(null, INVALID_INPUT_DEVICE_ID, SystemClock.uptimeMillis(),
                        AssistUtils.INVOCATION_TYPE_UNKNOWN);
                return;
            }
        } else if ("camera".equals(action)) {
            intent = new Intent(MediaStore.INTENT_ACTION_STILL_IMAGE_CAMERA);
        } else if ("custom_app".equals(action)) {
            final String flattened = Settings.System.getStringForUser(
                    resolver, "xiaomi_ai_key_custom_component", UserHandle.USER_CURRENT);
            final ComponentName component = ComponentName.unflattenFromString(flattened);
            if (component == null) return;
            intent = new Intent(Intent.ACTION_MAIN);
            intent.addCategory(Intent.CATEGORY_LAUNCHER);
            intent.setComponent(component);
            if (mContext.getPackageManager().resolveActivityAsUser(
                    intent, 0, UserHandle.USER_CURRENT) == null) return;
        } else {
            Slog.w(TAG, "Unknown Xiaomi AI key action: " + action);
            return;
        }

        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_RESET_TASK_IF_NEEDED);
        try {
            startActivityAsUser(intent, UserHandle.CURRENT_OR_SELF);
        } catch (ActivityNotFoundException e) {
            Slog.w(TAG, "Unable to launch Xiaomi AI key action: " + action, e);
        }
    }

"""
src = src.replace(case_marker, scan_code_handler + case_marker, 1)
src = src.replace(helper_marker, handler + helper_marker, 1)
target.write_text(src)
print(f"Patched {target}; inspect the diff and build services/core.")
