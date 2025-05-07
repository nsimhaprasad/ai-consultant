package tech.beskar.baid.intelijplugin.ui

import com.intellij.ui.components.JBLabel
import com.intellij.ui.components.JBPanel
import com.intellij.ui.components.panels.VerticalLayout
import org.fife.ui.rsyntaxtextarea.RSyntaxTextArea
import org.fife.ui.rsyntaxtextarea.SyntaxConstants
import org.fife.ui.rtextarea.RTextScrollPane
import tech.beskar.baid.intelijplugin.model.Block
import tech.beskar.baid.intelijplugin.model.Parameters
import tech.beskar.baid.intelijplugin.util.getMessageWidth
import java.awt.Dimension
import java.awt.datatransfer.StringSelection
import java.awt.FlowLayout
import java.awt.BorderLayout
import javax.swing.JButton
import javax.swing.JComponent
import com.intellij.openapi.ide.CopyPasteManager
import com.intellij.icons.AllIcons

/**
 * Renders parsed content blocks into Swing components.
 */
object ContentRenderer {
    fun renderHeading(block: Block.Heading): JComponent {
        val content = block.content
        val label = JBLabel(content)
        val font = when (block.level) {
            1 -> label.font.deriveFont(label.font.style or java.awt.Font.BOLD, 22f)
            2 -> label.font.deriveFont(label.font.style or java.awt.Font.BOLD, 18f)
            3 -> label.font.deriveFont(label.font.style or java.awt.Font.BOLD, 16f)
            else -> label.font.deriveFont(label.font.style, 14f)
        }
        label.font = font
        label.border = getMessageWidth().let { com.intellij.util.ui.JBUI.Borders.empty(6) }
        println("Heading content: $content")
        return label
    }

    fun renderParagraph(block: Block.Paragraph): JComponent {
        val html = "<html><div style='width:${getMessageWidth()}px;'>${block.content}</div></html>"
        val label = JBLabel(html)
        label.border = getMessageWidth().let { com.intellij.util.ui.JBUI.Borders.empty(4) }
        return label
    }

    fun renderCode(block: Block.Code): JComponent {
        val style = when (block.language.lowercase()) {
            "kotlin" -> SyntaxConstants.SYNTAX_STYLE_KOTLIN
            "java" -> SyntaxConstants.SYNTAX_STYLE_JAVA
            "javascript", "js" -> SyntaxConstants.SYNTAX_STYLE_JAVASCRIPT
            "xml", "html" -> SyntaxConstants.SYNTAX_STYLE_XML
            "python" -> SyntaxConstants.SYNTAX_STYLE_PYTHON
            "ruby" -> SyntaxConstants.SYNTAX_STYLE_RUBY
            else -> SyntaxConstants.SYNTAX_STYLE_NONE
        }
        val textArea = RSyntaxTextArea().apply {
            syntaxEditingStyle = style
            text = block.content
            isEditable = false
            isCodeFoldingEnabled = true
            lineWrap = true
            wrapStyleWord = true
        }
        val scroll = RTextScrollPane(textArea)
        scroll.preferredSize = Dimension(getMessageWidth(), com.intellij.util.ui.JBUI.scale(200))
        // Wrap scroll and copy button in a panel
        val wrapper = JBPanel<JBPanel<*>>(BorderLayout()).apply {
            add(scroll, BorderLayout.CENTER)
        }
        // Copy button panel
        val copyBtn = JButton(AllIcons.Actions.Copy).apply {
            toolTipText = "Copy code"
            addActionListener { CopyPasteManager.getInstance().setContents(StringSelection(block.content)) }
            border = com.intellij.util.ui.JBUI.Borders.empty(2)
        }
        val btnPanel = JBPanel<JBPanel<*>>(FlowLayout(FlowLayout.RIGHT)).apply {
            isOpaque = false
            add(copyBtn)
        }
        wrapper.add(btnPanel, BorderLayout.NORTH)
        return wrapper
    }

    fun renderCommand(block: Block.Command): JComponent {
        val panel = JBPanel<JBPanel<*>>(VerticalLayout(4))
        when (val params = block.parameters) {
            is Parameters.CreateFileParams -> {
                val link = JBLabel("<html><a href=\"#\">Create file: ${params.path}</a></html>")
                link.cursor = java.awt.Cursor.getPredefinedCursor(java.awt.Cursor.HAND_CURSOR)
                panel.add(link)
            }

            is Parameters.ExecuteGradleParams -> {
                val cmd = listOf(params.command).plus(params.args).joinToString(" ")
                val btn = JButton("Run Gradle: $cmd")
                panel.add(btn)
            }
        }
        return panel
    }

    /**
     * Renders list blocks into a vertical panel with bullet or numbered items.
     */
    fun renderList(block: Block.ListBlock): JComponent {
        val panel = JBPanel<JBPanel<*>>(VerticalLayout(4))
        block.items.forEachIndexed { idx, item ->
            val prefix = if (block.ordered) "${idx + 1}. " else "\u2022 "
            val html = "<html><div style='width:${getMessageWidth()}px;'>$prefix${item.content}</div></html>"
            val label = JBLabel(html)
            label.border = getMessageWidth().let { com.intellij.util.ui.JBUI.Borders.empty(4) }
            panel.add(label)
        }
        return panel
    }

    fun renderCallout(block: Block.Callout): JComponent {
        val panel = JBPanel<JBPanel<*>>(VerticalLayout(4))
        val html = "<html><div style='width:${getMessageWidth()}px;'><b>${block.title}</b><br>${block.content}</div></html>"
        val label = JBLabel(html)
        label.border = getMessageWidth().let { com.intellij.util.ui.JBUI.Borders.empty(4) }
        panel.add(label)
        return panel
    }
}
