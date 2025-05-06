package tech.beskar.baid.intelijplugin.util

import com.intellij.util.ui.JBUI

/**
 * Utility functions for UI-related operations
 */

/**
 * Calculate dynamic message width based on available space
 * @return The calculated width in pixels
 */
fun getMessageWidth(): Int {
    // Use a reasonable default width that works well for code blocks
    val defaultWidth = JBUI.scale(200)
    
    // Use 80% of default width for better fit, with min and max constraints
    return defaultWidth.coerceAtLeast(JBUI.scale(200)).coerceAtMost(JBUI.scale(500))
}
