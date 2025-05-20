package tech.beskar.baid.intelijplugin

import com.intellij.openapi.project.Project
import com.intellij.ui.components.JBPanel
import tech.beskar.baid.intelijplugin.auth.GoogleAuthService
import tech.beskar.baid.intelijplugin.controller.*
import tech.beskar.baid.intelijplugin.service.AuthenticationService
import tech.beskar.baid.intelijplugin.service.BaidAPIService
import tech.beskar.baid.intelijplugin.service.IAuthenticationService
import tech.beskar.baid.intelijplugin.service.IBaidApiService
import tech.beskar.baid.intelijplugin.ui.toolwindow.BaidToolWindowView
import java.awt.BorderLayout

class BaidToolWindowPanelMVC(project: Project) : JBPanel<BaidToolWindowPanelMVC>(BorderLayout()) {

    private val view: BaidToolWindowView
    private val controller: BaidToolWindowController

    init {
        val googleAuthService = GoogleAuthService()
        val authenticationService: IAuthenticationService = AuthenticationService(googleAuthService)
        // BaidAPIService uses BaidConfiguration.getInstance() internally.
        val baidApiService: IBaidApiService = BaidAPIService()

        val authController: IAuthController = AuthController(authenticationService)
        val sessionController: ISessionController = SessionController(authController, baidApiService)
        val chatController: IChatController = ChatController(project, baidApiService, authController, sessionController)
        
        // APIController remains a concrete class for now as per previous subtask instructions.
        val apiController = APIController(authController, sessionController, chatController)

        view = BaidToolWindowView(project, authController, apiController, sessionController)
        controller = BaidToolWindowController(project, view, apiController, chatController, authController, sessionController)

        view.actions = controller
        add(view.contentPanel, BorderLayout.CENTER)

        // The BaidToolWindowController's 'init' block calls 'initialAuthCheck',
        // which triggers the initial authentication flow and UI setup.
    }
}