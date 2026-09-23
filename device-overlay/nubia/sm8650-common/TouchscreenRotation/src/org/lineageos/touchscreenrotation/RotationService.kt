/*
 * SPDX-FileCopyrightText: 2025 The LineageOS Project
 * SPDX-License-Identifier: Apache-2.0
 */

package org.lineageos.touchscreenrotation

import android.app.Service
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.os.IBinder
import android.os.Handler
import android.os.Looper
import android.util.Log
import android.view.Display
import android.view.Surface
import java.io.FileWriter
import java.io.IOException

class RotationService : Service() {
    private lateinit var rotationReceiver: BroadcastReceiver
    private var rotation = 0

    private lateinit var unlockReceiver: BroadcastReceiver
    private val recoveryHandler = Handler(Looper.getMainLooper())
    private val recoveryRunnable = Runnable { performTouchRecovery("delayed") }

    override fun onCreate() {
        super.onCreate()

        Log.i(TAG, "Service created")

        rotationReceiver =
            object : BroadcastReceiver() {
                override fun onReceive(context: Context, intent: Intent) {
                    val newRotation = getRotation(context)
                    if (newRotation != rotation) {
                        rotation = newRotation
                        writeRotation(newRotation)
                    }
                }
            }

        val filter = IntentFilter(Intent.ACTION_CONFIGURATION_CHANGED)
        registerReceiver(rotationReceiver, filter)

        val unlockFilter = IntentFilter(Intent.ACTION_USER_PRESENT)
        unlockReceiver =
            object : BroadcastReceiver() {
                override fun onReceive(context: Context, intent: Intent) {
                    if (Intent.ACTION_USER_PRESENT == intent.action) {
                        scheduleTouchRecovery("user_present")
                    }
                }
            }
        registerReceiver(unlockReceiver, unlockFilter)

        writeRotation(getRotation(this))
        rotation = getRotation(this)
    }

    private fun writeRotation(rotation: Int) {
        Log.i(TAG, "Write rotation: $rotation")
        try {
            FileWriter(ROTATION_PATH).use { writer -> writer.write(rotation.toString()) }
        } catch (e: IOException) {
            Log.e(TAG, "Failed to write to $ROTATION_PATH", e)
        }
    }

    override fun onDestroy() {
        unregisterReceiver(rotationReceiver)
        if (::unlockReceiver.isInitialized) {
            unregisterReceiver(unlockReceiver)
        }
        recoveryHandler.removeCallbacks(recoveryRunnable)
        Log.i(TAG, "Service destroyed")
        super.onDestroy()
    }

    override fun onBind(intent: Intent): IBinder? {
        return null
    }



    // PlasmaOS: unlock touch recovery
    private fun scheduleTouchRecovery(reason: String) {
        Log.i(TAG, "Scheduling touch recovery ($reason)")
        recoveryHandler.removeCallbacks(recoveryRunnable)
        recoveryHandler.postDelayed(recoveryRunnable, 300)
    }

    private fun performTouchRecovery(reason: String) {
        Log.i(TAG, "Touch recovery ($reason)")
        val currentRotation = getRotation(this)
        rotation = currentRotation
        writeRotation(currentRotation)
        toggleRateBoost()
        restartTouchHal()
    }

    private fun toggleRateBoost() {
        try {
            FileWriter(RATE_BOOST_PATH).use { writer -> writer.write("0") }
            recoveryHandler.postDelayed({
                try {
                    FileWriter(RATE_BOOST_PATH).use { writer -> writer.write("1") }
                } catch (e: Exception) {
                    Log.w(TAG, "Failed to re-enable $RATE_BOOST_PATH", e)
                }
            }, 50)
        } catch (e: Exception) {
            Log.w(TAG, "Failed to toggle $RATE_BOOST_PATH", e)
        }
    }

    private fun restartTouchHal() {
        try {
            Runtime.getRuntime()
                .exec(arrayOf("setprop", "ctl.restart", "vendor.touch-hal"))
                .waitFor()
        } catch (e: Exception) {
            Log.w(TAG, "Failed to restart vendor.touch-hal", e)
        }
    }

    companion object {
        private const val TAG = "RotationService"
        private const val ROTATION_PATH = "/sys/devices/platform/goodix_ts.0/rotation"
        private const val RATE_BOOST_PATH = "/sys/devices/platform/goodix_ts.0/rate_boost"

        @JvmStatic
        fun getRotation(context: Context): Int {
            val display =
                context.getSystemService(Context.DISPLAY_SERVICE)
                    as android.hardware.display.DisplayManager
            val rotation = display.getDisplay(Display.DEFAULT_DISPLAY).rotation

            return when (rotation) {
                Surface.ROTATION_0 -> 0
                Surface.ROTATION_90 -> 90
                Surface.ROTATION_180 -> 180
                else -> 270
            }
        }
    }
}
