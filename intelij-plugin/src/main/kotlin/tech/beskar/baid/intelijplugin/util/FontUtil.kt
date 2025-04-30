package tech.beskar.baid.intelijplugin.util

import com.intellij.ui.scale.JBUIScale
import java.awt.Font
import java.io.InputStream
import com.intellij.util.ui.UIUtil
import java.awt.GraphicsEnvironment

object FontUtil {
    fun getLabelFont(isBold: Boolean = false, size: Float = 14f): Font {
        val fontPath = if (isBold) "/fonts/DMSans/DMSans-Bold.ttf" else "/fonts/DMSans/DMSans-Regular.ttf"
        return try {
            val fontStream = javaClass.getResourceAsStream(fontPath)
            if (fontStream != null) {
                val font = Font.createFont(Font.TRUETYPE_FONT, fontStream)
                val scaledFont = font.deriveFont(JBUIScale.scale(size))
                GraphicsEnvironment.getLocalGraphicsEnvironment().registerFont(font)
                scaledFont
            } else {
                if (isBold) {
                    UIUtil.getLabelFont().deriveFont(Font.BOLD, JBUIScale.scale(size))
                } else {
                    UIUtil.getLabelFont().deriveFont(JBUIScale.scale(size))
                }
            }
        } catch (e: Exception) {
            UIUtil.getLabelFont()
        }
    }

    fun getTitleFont(): Font {
        return getLabelFont(size = 36f, isBold = true)
    }

    fun getSubTitleFont(): Font {
        return getLabelFont(size = 18f, isBold = false)
    }

    fun getBodyFont(): Font {
        return getLabelFont(size = 14f, isBold = false)
    }
}
