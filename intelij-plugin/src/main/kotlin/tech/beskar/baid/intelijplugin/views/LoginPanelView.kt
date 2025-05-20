package tech.beskar.baid.intelijplugin.views

import com.intellij.openapi.project.Project
import com.intellij.ui.JBColor
import com.intellij.ui.components.JBLabel
import com.intellij.ui.components.JBPanel
import com.intellij.util.ui.JBUI
import tech.beskar.baid.intelijplugin.controller.APIController
import tech.beskar.baid.intelijplugin.model.UserProfile
import java.awt.BorderLayout
import java.awt.FlowLayout
import java.awt.Font
import java.awt.GridBagLayout
import java.awt.event.ActionEvent
import java.util.function.Consumer
import javax.swing.JButton
import javax.swing.JPanel
import javax.swing.SwingConstants
import javax.swing.SwingUtilities


class LoginPanelView(private val project: Project, private val onLoginCallback: Consumer<UserProfile?>, private val onLoginFailure: Consumer<Throwable>) :
    JBPanel<LoginPanelView>(BorderLayout()) {
    private val apiController: APIController = APIController.getInstance()

    private var signInButton: JButton? = null
    private var statusLabel: JBLabel? = null
    private var loadingPanel: JPanel? = null

    init {
        initializeUI()
    }

    private fun initializeUI() {
        setBackground(JBColor.background())
        setBorder(JBUI.Borders.empty(16))


        // Create centered content panel
        val contentPanel = JBPanel<JBPanel<*>>(GridBagLayout())
        contentPanel.setOpaque(false)


        // Create login card
        val loginCard = createLoginCard()


        // Add login card to content panel
        contentPanel.add(loginCard)


        // Add content panel to main panel
        add(contentPanel, BorderLayout.CENTER)
    }

    private fun createLoginCard(): JBPanel<JBPanel<*>> {
        val card = JBPanel<JBPanel<*>>(BorderLayout(0, JBUI.scale(20)))
        card.setOpaque(false)
        card.setBorder(JBUI.Borders.empty(JBUI.scale(24)))


        // Create logo panel
        val logoPanel = JBPanel<JBPanel<*>>(FlowLayout(FlowLayout.CENTER))
        logoPanel.setOpaque(false)


        // Add Baid logo (placeholder)
        val logoLabel = JBLabel("Welcome to Baid")
        logoLabel.setFont(Font(logoLabel.getFont().getName(), Font.BOLD, JBUI.scale(36)))
        logoLabel.setForeground(JBColor.foreground())
        logoPanel.add(logoLabel)


        // Create message panel
        val messagePanel = JBPanel<JBPanel<*>>(BorderLayout())
        messagePanel.setOpaque(false)


        // Add welcome message
        val welcomeLabel = JBLabel(
            "<html><div style='text-align: center;'>" +
                    "Sign in to start transforming ideas into outcomes, instantly." +
                    "</div></html>",
            SwingConstants.CENTER
        )
        welcomeLabel.setFont(Font(welcomeLabel.getFont().getName(), Font.PLAIN, JBUI.scale(14)))
        welcomeLabel.setForeground(JBColor.foreground())
        messagePanel.add(welcomeLabel, BorderLayout.CENTER)


        // Create button panel
        val buttonPanel = JBPanel<JBPanel<*>>(FlowLayout(FlowLayout.CENTER))
        buttonPanel.setOpaque(false)


        // Add sign-in button
        signInButton = JButton("Sign in with Google")
        signInButton!!.addActionListener { e: ActionEvent? -> startSignIn() }
        buttonPanel.add(signInButton)


        // Create status panel
        val statusPanel = JBPanel<JBPanel<*>>(FlowLayout(FlowLayout.CENTER))
        statusPanel.setOpaque(false)


        // Add status label
        statusLabel = JBLabel("")
        statusLabel!!.setForeground(JBColor.RED)
        statusPanel.add(statusLabel)


        // Create loading panel
        loadingPanel = JPanel(FlowLayout(FlowLayout.CENTER))
        loadingPanel!!.setOpaque(false)
        loadingPanel!!.isVisible = false


        // Add loading spinner (placeholder)
        val loadingLabel = JBLabel("Signing in...")
        loadingPanel!!.add(loadingLabel)


        // Add all panels to card
        card.add(logoPanel, BorderLayout.NORTH)
        card.add(messagePanel, BorderLayout.CENTER)

        val southPanel = JBPanel<JBPanel<*>>(BorderLayout())
        southPanel.setOpaque(false)
        southPanel.add(buttonPanel, BorderLayout.NORTH)
        southPanel.add(statusPanel, BorderLayout.CENTER)
        southPanel.add(loadingPanel!!, BorderLayout.SOUTH)

        card.add(southPanel, BorderLayout.SOUTH)

        return card
    }

    private fun startSignIn() {
        // Show loading state
        setSigningIn(true)


        // Start sign in
        apiController.signIn(project, { userProfile: UserProfile? ->
            // Success
            setSigningIn(false)

            // Notify callback
            onLoginCallback.accept(userProfile)
        }, { error: Throwable? ->
            // Error
            setSigningIn(false)
            error?.let { onLoginFailure.accept(it) }
        })
    }

    private fun setSigningIn(isSigningIn: Boolean) {
        SwingUtilities.invokeLater {
            signInButton!!.setEnabled(!isSigningIn)
            loadingPanel!!.setVisible(isSigningIn)
            statusLabel!!.setText("")
            revalidate()
            repaint()
        }
    }

    fun setErrorMessage(message: String?) {
        SwingUtilities.invokeLater {
            statusLabel!!.setText(message)
            setSigningIn(false)
        }
    }
}