package tech.beskar.baid.intelijplugin.ui

import com.intellij.openapi.editor.Editor
import com.intellij.openapi.editor.EditorCustomElementRenderer
import com.intellij.openapi.editor.Inlay
import com.intellij.openapi.editor.markup.TextAttributes
import java.awt.Color
import java.awt.Font
import java.awt.Graphics
import java.awt.Rectangle
import tech.beskar.baid.intelijplugin.service.DiffHunk // Keep for future use with hunk data

class DiffActionInlayRenderer(
    // Pass the hunk for context, though not fully used for actions in this step
    private val hunk: DiffHunk, 
    private val onAccept: (hunk: DiffHunk) -> Unit,
    private val onReject: (hunk: DiffHunk) -> Unit
) : EditorCustomElementRenderer {

    private val acceptText = "[Accept]"
    private val rejectText = "[Reject]"
    private val spacing = 10
    private var acceptBounds: Rectangle? = null
    private var rejectBounds: Rectangle? = null

    private fun getFont(editor: Editor): Font = editor.colorsScheme.getFont(com.intellij.openapi.editor.colors.EditorFontType.PLAIN)
    
    override fun calcWidthInPixels(inlay: Inlay<*>): Int {
        val fontMetrics = inlay.editor.contentComponent.getFontMetrics(getFont(inlay.editor))
        val acceptWidth = fontMetrics.stringWidth(acceptText)
        val rejectWidth = fontMetrics.stringWidth(rejectText)
        return acceptWidth + rejectWidth + spacing * 3 // spacing before, between, after
    }

    override fun paint(inlay: Inlay<*>, g: Graphics, targetRegion: Rectangle, textAttributes: TextAttributes) {
        val editor = inlay.editor
        val font = getFont(editor)
        val fontMetrics = editor.contentComponent.getFontMetrics(font)
        
        g.font = font
        val ascent = fontMetrics.ascent

        var currentX = targetRegion.x + spacing
        
        // Draw "Accept" button
        val acceptWidth = fontMetrics.stringWidth(acceptText)
        // Define bounds relative to targetRegion.x, targetRegion.y for hit testing later
        acceptBounds = Rectangle(currentX - targetRegion.x, 0, acceptWidth + spacing, targetRegion.height)
        g.color = Color.GREEN.darker() // Example color
        // g.fillRect(currentX, targetRegion.y, acceptWidth + spacing, targetRegion.height) // Optional background
        g.color = editor.colorsScheme.defaultForeground
        g.drawString(acceptText, currentX + spacing / 2, targetRegion.y + ascent)
        currentX += acceptWidth + spacing

        // Draw "Reject" button
        val rejectWidth = fontMetrics.stringWidth(rejectText)
        // Define bounds relative to targetRegion.x, targetRegion.y
        rejectBounds = Rectangle(currentX - targetRegion.x, 0, rejectWidth + spacing, targetRegion.height)
        g.color = Color.RED.darker() // Example color
        // g.fillRect(currentX, targetRegion.y, rejectWidth + spacing, targetRegion.height) // Optional background
        g.color = editor.colorsScheme.defaultForeground
        g.drawString(rejectText, currentX + spacing / 2, targetRegion.y + ascent)
    }

    // This method will be called by InlineDiffDisplayManager's mouse listener
    fun handleClick(editor: Editor, clickRelativeToInlayX: Int, clickRelativeToInlayY: Int) {
        // clickX, clickY are now relative to the inlay's own coordinate space (targetRegion in paint)
        acceptBounds?.let {
            if (it.contains(clickRelativeToInlayX, clickRelativeToInlayY)) {
                onAccept(hunk)
                return@handleClick
            }
        }
        rejectBounds?.let {
            if (it.contains(clickRelativeToInlayX, clickRelativeToInlayY)) {
                onReject(hunk)
                return@handleClick
            }
        }
    }
}
