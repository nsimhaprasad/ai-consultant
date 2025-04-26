package com.aiconsultant.intelijplugin

import com.intellij.openapi.project.Project
import com.intellij.util.io.HttpRequests
import java.awt.*
import javax.swing.*
import org.json.JSONObject

class AIConsultantToolWindowPanel(private val project: Project) : JPanel(BorderLayout()) {
    private val chatPanel = JPanel()
    private val chatScroll = JScrollPane(chatPanel)
    private val inputField = JTextField(30)
    private val consultButton = JButton("Consult")

    init {
        chatPanel.layout = BoxLayout(chatPanel, BoxLayout.Y_AXIS)
        chatPanel.background = Color(245, 245, 245)
        chatScroll.verticalScrollBar.unitIncrement = 16
        chatScroll.preferredSize = Dimension(350, 400)
        chatScroll.border = null

        val inputPanel = JPanel().apply {
            layout = BoxLayout(this, BoxLayout.X_AXIS)
            add(inputField)
            add(Box.createHorizontalStrut(8))
            consultButton.background = Color(33, 150, 243)
            consultButton.foreground = Color.WHITE
            consultButton.font = Font("Arial", Font.BOLD, 13)
            add(consultButton)
        }

        add(chatScroll, BorderLayout.CENTER)
        add(inputPanel, BorderLayout.SOUTH)

        consultButton.addActionListener {
            val userMessage = inputField.text.trim()
            if (userMessage.isNotEmpty()) {
                appendMessage(userMessage, isUser = true)
                inputField.text = ""
                consultWithAPI(userMessage)
            }
        }
    }

    private fun appendMessage(message: String, isUser: Boolean) {
        val bubble = JPanel().apply {
            layout = BorderLayout()
            background = if (isUser) Color(225, 245, 254) else Color(240, 240, 240)
            border = javax.swing.BorderFactory.createEmptyBorder(8, 12, 8, 12)
            alignmentX = if (isUser) Component.RIGHT_ALIGNMENT else Component.LEFT_ALIGNMENT
            add(JLabel("<html>${message.replace("\n", "<br>")}</html>").apply {
                font = Font("Arial", Font.PLAIN, 13)
            }, BorderLayout.CENTER)
            maximumSize = Dimension(300, Int.MAX_VALUE)
        }
        val wrapper = JPanel().apply {
            layout = BorderLayout()
            isOpaque = false
            add(bubble, if (isUser) BorderLayout.EAST else BorderLayout.WEST)
        }
        chatPanel.add(wrapper)
        chatPanel.add(Box.createVerticalStrut(6))
        SwingUtilities.invokeLater {
            chatPanel.revalidate()
            chatPanel.repaint()
            chatScroll.verticalScrollBar.value = chatScroll.verticalScrollBar.maximum
        }
    }

    private fun consultWithAPI(userPrompt: String) {
        val editor = com.intellij.openapi.fileEditor.FileEditorManager.getInstance(project).selectedTextEditor
        val document = editor?.document
        val fileText = document?.text ?: "No file open."
        appendMessage("Consulting... (API call in progress)", isUser = false)

        // Make API call to FastAPI backend
        val apiUrl = "http://localhost:8000/consult"
        val payload = JSONObject(mapOf(
            "prompt" to userPrompt,
            "file_content" to fileText
        )).toString()

        Thread {
            try {
                val response = HttpRequests
                    .post(apiUrl, "application/json")
                    .connectTimeout(10000)
                    .readTimeout(20000)
                    .tuner { connection -> /* headers */ }
                    .connect { request ->
                        request.write(payload)
                        request.getReader(null).readText()
                    }

                SwingUtilities.invokeLater {
                    appendMessage(response, isUser = false)
                }
            } catch (e: Exception) {
                SwingUtilities.invokeLater {
                    appendMessage("Error: ${e.localizedMessage}", isUser = false)
                }
            }
        }.start()
    }
}
