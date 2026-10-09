/*
 * SPDX-License-Identifier: Apache-2.0
 */
package com.xiaomi.settings.parts;

import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.content.pm.ResolveInfo;
import android.os.Bundle;
import android.provider.Settings;
import android.text.TextUtils;
import android.widget.Toast;

import androidx.appcompat.app.AlertDialog;
import androidx.preference.ListPreference;
import androidx.preference.Preference;

import com.android.settingslib.widget.SettingsBasePreferenceFragment;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;

public class AIKeySettingsFragment extends SettingsBasePreferenceFragment {
    static final String KEY_ACTION = "xiaomi_ai_key_action";
    static final String KEY_CUSTOM_COMPONENT = "xiaomi_ai_key_custom_component";

    private ListPreference mActionPreference;
    private Preference mCustomAppPreference;

    @Override
    public void onCreatePreferences(Bundle savedInstanceState, String rootKey) {
        setPreferencesFromResource(R.xml.ai_key_settings, rootKey);

        mActionPreference = findPreference("ai_key_action");
        mCustomAppPreference = findPreference("ai_key_custom_app");

        if (mActionPreference == null || mCustomAppPreference == null) {
            throw new IllegalStateException("AI key preferences are missing from XML");
        }

        // Settings.System is the source of truth; do not persist these values
        // into the fragment's private SharedPreferences.
        mActionPreference.setPersistent(false);
        mCustomAppPreference.setPersistent(false);

        mActionPreference.setOnPreferenceChangeListener((preference, newValue) -> {
            final String action = String.valueOf(newValue);
            if ("custom_app".equals(action)) {
                pickCustomApp();
                return false;
            }

            if (Settings.System.putString(
                    requireContext().getContentResolver(), KEY_ACTION, action)) {
                mActionPreference.setValue(action);
            } else {
                Toast.makeText(requireContext(),
                        R.string.ai_key_settings_save_failed, Toast.LENGTH_SHORT).show();
            }
            updateSummaries();
            return false;
        });

        mCustomAppPreference.setOnPreferenceClickListener(preference -> {
            pickCustomApp();
            return true;
        });

        updateSummaries();
    }

    @Override
    public void onResume() {
        super.onResume();
        updateSummaries();
    }

    private void updateSummaries() {
        if (mActionPreference == null || getContext() == null) {
            return;
        }

        final Context context = requireContext();
        String action = Settings.System.getString(
                context.getContentResolver(), KEY_ACTION);
        if (TextUtils.isEmpty(action)) {
            action = "disabled";
        }
        if (action.startsWith("app:")) {
            action = "custom_app";
        }
        if (!"disabled".equals(action) && !"assistant".equals(action)
                && !"gemini".equals(action) && !"camera".equals(action)
                && !"custom_app".equals(action)) {
            action = "disabled";
        }
        mActionPreference.setValue(action);

        if ("custom_app".equals(action)) {
            String flattened = Settings.System.getString(
                    context.getContentResolver(), KEY_CUSTOM_COMPONENT);
            String label = getCustomAppLabel(flattened);
            mCustomAppPreference.setSummary(TextUtils.isEmpty(label)
                    ? getString(R.string.ai_key_custom_app_summary) : label);
        } else {
            mCustomAppPreference.setSummary(R.string.ai_key_custom_app_summary);
        }
    }

    private String getCustomAppLabel(String flattened) {
        if (TextUtils.isEmpty(flattened)) {
            return null;
        }
        try {
            ComponentName component = ComponentName.unflattenFromString(flattened);
            if (component == null) {
                return null;
            }
            PackageManager pm = requireContext().getPackageManager();
            return pm.getActivityInfo(component, 0).loadLabel(pm).toString();
        } catch (PackageManager.NameNotFoundException e) {
            return null;
        }
    }

    private void pickCustomApp() {
        final Context context = requireContext();
        final Intent launchIntent = new Intent(Intent.ACTION_MAIN);
        launchIntent.addCategory(Intent.CATEGORY_LAUNCHER);

        final PackageManager pm = context.getPackageManager();
        final List<ResolveInfo> apps = new ArrayList<>(
                pm.queryIntentActivities(launchIntent, 0));
        Collections.sort(apps, Comparator.comparing(
                info -> info.loadLabel(pm).toString(),
                String.CASE_INSENSITIVE_ORDER));

        if (apps.isEmpty()) {
            Toast.makeText(context, R.string.ai_key_custom_app_none, Toast.LENGTH_SHORT).show();
            return;
        }

        final CharSequence[] labels = new CharSequence[apps.size()];
        for (int i = 0; i < apps.size(); i++) {
            labels[i] = apps.get(i).loadLabel(pm);
        }

        new AlertDialog.Builder(context)
                .setTitle(R.string.ai_key_custom_app_dialog)
                .setItems(labels, (dialog, which) -> {
                    ResolveInfo selected = apps.get(which);
                    ComponentName component = new ComponentName(
                            selected.activityInfo.packageName, selected.activityInfo.name);
                    boolean componentSaved = Settings.System.putString(
                            context.getContentResolver(),
                            KEY_CUSTOM_COMPONENT, component.flattenToString());
                    boolean actionSaved = componentSaved && Settings.System.putString(
                            context.getContentResolver(), KEY_ACTION, "custom_app");
                    if (!actionSaved) {
                        Toast.makeText(context, R.string.ai_key_settings_save_failed,
                                Toast.LENGTH_SHORT).show();
                    }
                    updateSummaries();
                })
                .setNegativeButton(android.R.string.cancel, null)
                .show();
    }
}
