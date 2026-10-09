# Xiaomi Parts — AI key settings

This is a Settings extension for the Cepheus AI hardware key. It has no launcher
entry; the Settings app discovers it through the `com.android.settings.action.IA_SETTINGS`
extension action.

The preference writes these values to `Settings.System`:

- `xiaomi_ai_key_action`: `disabled`, `assistant`, `gemini`, `camera`, or `custom_app`
- `xiaomi_ai_key_custom_component`: flattened `ComponentName` selected for a custom app

The framework key handler must read these settings and execute the chosen action.
This UI alone does not intercept hardware input. No evdev polling, kernel change,
firmware change, or LineageParts change is used.
