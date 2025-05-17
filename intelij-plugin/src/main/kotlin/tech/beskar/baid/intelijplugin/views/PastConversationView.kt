package tech.beskar.baid.intelijplugin.views

import com.intellij.icons.AllIcons
import com.intellij.openapi.project.Project
import com.intellij.ui.JBColor
import com.intellij.ui.components.JBLabel
import com.intellij.ui.components.JBPanel
import com.intellij.ui.components.JBScrollPane
import com.intellij.ui.components.panels.VerticalLayout
import com.intellij.util.ui.JBUI
import tech.beskar.baid.intelijplugin.controller.APIController
import tech.beskar.baid.intelijplugin.model.ChatSession
import tech.beskar.baid.intelijplugin.model.SessionPreview
import java.awt.BorderLayout
import java.awt.Cursor
import java.awt.Font
import java.awt.event.ActionEvent
import java.awt.event.MouseAdapter
import java.awt.event.MouseEvent
import java.util.function.Consumer
import javax.swing.*
import javax.swing.border.Border
import javax.swing.border.CompoundBorder


class PastConversationsView(private val project: Project?, private val onSessionSelected: Consumer<ChatSession?>) :
    JBPanel<PastConversationsView>(BorderLayout()) {
    private val apiController: APIController = APIController.getInstance()

    private var conversationsPanel: JBPanel<JBPanel<*>?>? = null
    private var statusLabel: JBLabel? = null
    private var backButton: JButton? = null

    init {

        initializeUI()
    }

    private fun initializeUI() {
        setBackground(JBColor.background())


        // Create header panel
        val headerPanel = createHeaderPanel()
        add(headerPanel, BorderLayout.NORTH)


        // Create conversations panel
        conversationsPanel = JBPanel<JBPanel<*>?>(VerticalLayout(JBUI.scale(0)))
        conversationsPanel!!.setBackground(JBColor.background())


        // Add initial status
        statusLabel = JBLabel("Loading conversations...", SwingConstants.CENTER)
        statusLabel!!.setForeground(JBColor.foreground().darker())
        statusLabel!!.setBorder(JBUI.Borders.empty(JBUI.scale(24)))
        conversationsPanel!!.add(statusLabel)


        // Create scroll pane
        val scrollPane = JBScrollPane(conversationsPanel)
        scrollPane.setBorder(JBUI.Borders.empty())
        scrollPane.getVerticalScrollBar().setUnitIncrement(16)


        // Add scroll pane to main panel
        add(scrollPane, BorderLayout.CENTER)
    }

    private fun createHeaderPanel(): JBPanel<JBPanel<*>?> {
        val headerPanel = JBPanel<JBPanel<*>?>(BorderLayout())
        headerPanel.setBackground(JBColor.background())
        headerPanel.setBorder(JBUI.Borders.empty(JBUI.scale(16)))


//        // Add back button
//        backButton = JButton("Back to Chat")
//        backButton!!.setIcon(AllIcons.General.ArrowLeft)
//        backButton!!.setContentAreaFilled(false)
//        backButton!!.setBorderPainted(false)
//        backButton!!.setFocusPainted(false)


        // Add title
        val titleLabel = JBLabel("Past Conversations")
        titleLabel.setFont(Font(titleLabel.getFont().getName(), Font.BOLD, JBUI.scale(16)))
        titleLabel.setForeground(JBColor.foreground())

//        headerPanel.add(backButton!!, BorderLayout.WEST)
        headerPanel.add(titleLabel, BorderLayout.CENTER)

        return headerPanel
    }

//    fun setBackAction(action: Runnable) {
//        backButton!!.addActionListener { e: ActionEvent? -> action.run() }
//    }

    fun loadConversations() {
        // Show loading status
        SwingUtilities.invokeLater {
            conversationsPanel!!.removeAll()
            statusLabel = JBLabel("Loading conversations...", SwingConstants.CENTER)
            statusLabel!!.setForeground(JBColor.foreground().darker())
            statusLabel!!.setBorder(JBUI.Borders.empty(JBUI.scale(24)))
            conversationsPanel!!.add(statusLabel)
            conversationsPanel!!.revalidate()
            conversationsPanel!!.repaint()
        }


        // Load conversations
        apiController.loadPastConversations(
            { sessions: MutableList<SessionPreview>? -> this.displayConversations(sessions) },
            { error: Throwable? -> this.handleLoadError(error!!) }
        )
    }

    private fun displayConversations(sessions: MutableList<SessionPreview>?) {
        SwingUtilities.invokeLater {
            // Clear panel
            conversationsPanel!!.removeAll()

            if (sessions.isNullOrEmpty()) {
                // Show empty state
                statusLabel = JBLabel("No past conversations found", SwingConstants.CENTER)
                statusLabel!!.setForeground(JBColor.foreground().darker())
                statusLabel!!.setBorder(JBUI.Borders.empty(JBUI.scale(24)))
                conversationsPanel!!.add(statusLabel)
            } else {
                // Add subtitle
                val subtitleLabel = JBLabel("Select a conversation to continue", SwingConstants.LEFT)
                subtitleLabel.setFont(Font(subtitleLabel.getFont().getName(), Font.PLAIN, JBUI.scale(12)))
                subtitleLabel.setForeground(JBColor.foreground().darker())
                subtitleLabel.setBorder(JBUI.Borders.empty(JBUI.scale(8), JBUI.scale(16)))
                conversationsPanel!!.add(subtitleLabel)


                // Add each session
                for (session in sessions) {
                    val sessionPanel = createSessionPanel(session)
                    conversationsPanel!!.add(sessionPanel)
                }
            }

            conversationsPanel!!.revalidate()
            conversationsPanel!!.repaint()
        }
    }

    private fun createSessionPanel(session: SessionPreview): JPanel {
        val panel = JPanel(BorderLayout())
        panel.setBackground(JBColor.background())


        // Create border with bottom line
        val lineBorder: Border = BorderFactory.createMatteBorder(0, 0, 1, 0, JBColor.border())
        val paddingBorder: Border = JBUI.Borders.empty(JBUI.scale(12), JBUI.scale(16))
        panel.setBorder(CompoundBorder(lineBorder, paddingBorder))


        // Add cursor change on hover
        panel.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR))


        // Add preview text
        val previewLabel = JLabel(session.previewText)
        previewLabel.setForeground(JBColor.foreground())
        panel.add(previewLabel, BorderLayout.CENTER)


        // Add date label
        val dateLabel = JLabel(session.formattedLastUsedDate)
        dateLabel.setForeground(JBColor.foreground().darker())
        dateLabel.setFont(Font(dateLabel.getFont().getName(), Font.PLAIN, dateLabel.getFont().getSize() - 1))
        dateLabel.setBorder(JBUI.Borders.emptyTop(JBUI.scale(4)))
        panel.add(dateLabel, BorderLayout.SOUTH)


        // Add click handler
        panel.addMouseListener(object : MouseAdapter() {
            override fun mouseClicked(e: MouseEvent?) {
                loadSession(session.sessionId)
            }

            override fun mouseEntered(e: MouseEvent?) {
                panel.setBackground(JBColor.background().brighter())
            }

            override fun mouseExited(e: MouseEvent?) {
                panel.setBackground(JBColor.background())
            }
        })

        return panel
    }

    private fun handleLoadError(error: Throwable) {
        SwingUtilities.invokeLater {
            conversationsPanel!!.removeAll()
            // Show error message
            var message = "Error loading conversations: " + error.message
            if (error.message != null && (error.message!!.contains("401") ||
                        error.message!!.contains("403"))
            ) {
                message = "Please sign in to view your conversations"
            }

            statusLabel = JBLabel(message, SwingConstants.CENTER)
            statusLabel!!.setForeground(JBColor.RED)
            statusLabel!!.setBorder(JBUI.Borders.empty(JBUI.scale(24)))
            conversationsPanel!!.add(statusLabel)

            conversationsPanel!!.revalidate()
            conversationsPanel!!.repaint()
        }
    }

    private fun loadSession(sessionId: String?) {
        // Show loading state
        SwingUtilities.invokeLater {
            conversationsPanel!!.removeAll()
            statusLabel = JBLabel("Loading conversation...", SwingConstants.CENTER)
            statusLabel!!.setForeground(JBColor.foreground().darker())
            statusLabel!!.setBorder(JBUI.Borders.empty(JBUI.scale(24)))
            conversationsPanel!!.add(statusLabel)
            conversationsPanel!!.revalidate()
            conversationsPanel!!.repaint()
        }


        // Load session
        apiController.loadConversation(
            sessionId,
            { session: ChatSession? ->
                onSessionSelected?.accept(session)
            },
            { error: Throwable? -> this.handleLoadError(error!!) }
        )
    }
}