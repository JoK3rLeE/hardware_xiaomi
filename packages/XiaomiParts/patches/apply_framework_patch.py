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

# Anchor within interceptKeyBeforeQueueing, before global-key interception.
intercept_marker = "    interceptKeyBeforeQueueing(KeyEvent event, int policyFlags) {"
boot_marker = "        if (!mSystemBooted) {"
helper_marker = "    // There are several different flavors of"
if (src.count(intercept_marker) != 1 or src.count(boot_marker) != 1
        or src.count(helper_marker) != 1):
    raise SystemExit("Unexpected PhoneWindowManager layout; no files changed.")

intercept_start = src.index(intercept_marker)
boot_index = src.index(boot_marker, intercept_start)
if boot_index <= intercept_start:
    raise SystemExit("Could not locate boot guard inside interceptKeyBeforeQueueing.")

# This handler intentionally keys off the verified Linux scan code 689,
# independent of the Android keycode selected by the active .kl file.
scan_code_handler = """        // Xiaomi AI Key: Linux KEY_MACRO_RECORD_STOP, scan code 689.
        if (event.getScanCode() == 689) {
            final boolean aiKeyDown = event.getAction() == KeyEvent.ACTION_DOWN;
            if (aiKeyDown && event.getRepeatCount() == 0
                    && mSystemBooted
                    && (policyFlags & FLAG_INTERACTIVE) != 0
                    && (mKeyguardDelegate == null
                            || !mKeyguardDelegate.isShowing())) {
                handleXiaomiAiKey();
            }
            return 0;
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
src = src.replace(boot_marker, scan_code_handler + boot_marker, 1)
src = src.replace(helper_marker, handler + helper_marker, 1)
target.write_text(src)
print(f"Patched {target}; inspect the diff and build services/core.")
