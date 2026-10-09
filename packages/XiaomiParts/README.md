# Xiaomi Parts — AI key settings

This is a Settings extension for the Cepheus AI hardware key. It has no launcher
entry; the custom ROM Settings app discovers it through the
`com.android.settings.action.IA_SETTINGS` extension action in the System category.

The preference writes these values to `Settings.System`:

- `xiaomi_ai_key_action`: `disabled`, `assistant`, `gemini`, `camera`, or `custom_app`
- `xiaomi_ai_key_custom_component`: flattened `ComponentName` selected for a custom app

## Framework integration

The Settings page stores the selection; Android's input policy must consume
Android keycode 338 and launch the chosen action. From the Android source root,
run:

```sh
python3 hardware/xiaomi/packages/XiaomiParts/patches/apply_framework_patch.py
git diff -- frameworks/base/services/core/java/com/android/server/policy/PhoneWindowManager.java
```

Review the diff before building. The script uses source markers verified against
LineageOS `lineage-23.2` and aborts if the expected layout is not found. It
consumes the key and launches actions only when the display is interactive and
the keyguard is not showing. Gemini falls back to the configured default
assistant if the Gemini launcher activity is unavailable.

No kernel or firmware changes, `/dev/input/event*` polling, or LineageParts
modifications are used. The framework patch still needs to be applied, built,
and tested on-device; it has not been compiled in this environment.

## Input mapping note

Linux keycode 689 is defined upstream as `KEY_MACRO_RECORD_STOP`. Cepheus
reuses that Linux code for its physical AI button and maps it device-specifically
to Android keycode 338 (`AI`) in `gpio-keys.kl`. Keep this mapping out of
generic AOSP key layouts; other Linux input devices may legitimately use 689
for macro recording.
