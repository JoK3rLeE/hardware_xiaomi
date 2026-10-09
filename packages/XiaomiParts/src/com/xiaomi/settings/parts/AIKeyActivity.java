/*
 * SPDX-License-Identifier: Apache-2.0
 */
package com.xiaomi.settings.parts;

import android.os.Bundle;

import androidx.appcompat.app.AppCompatActivity;

public class AIKeyActivity extends AppCompatActivity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setTitle(R.string.xiaomi_parts_title);

        if (savedInstanceState == null) {
            getSupportFragmentManager().beginTransaction()
                    .replace(android.R.id.content, new AIKeySettingsFragment())
                    .commit();
        }
    }
}
