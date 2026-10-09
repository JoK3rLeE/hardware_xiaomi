/*
 * SPDX-License-Identifier: Apache-2.0
 */
package com.xiaomi.settings.parts;

import android.os.Bundle;

import com.android.settingslib.collapsingtoolbar.CollapsingToolbarBaseActivity;
import com.android.settingslib.collapsingtoolbar.R;

public class AIKeyActivity extends CollapsingToolbarBaseActivity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        getSupportFragmentManager().beginTransaction()
                .replace(R.id.content_frame, new AIKeySettingsFragment(), "AIKeySettingsFragment")
                .commit();
    }
}
