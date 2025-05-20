package tech.beskar.baid.intelijplugin.ui

import com.intellij.openapi.diff.DiffManager
import com.intellij.openapi.diff.DiffRequestFactory
import com.intellij.openapi.project.Project
import com.intellij.openapi.ui.DialogWrapper
import tech.beskar.baid.intelijplugin.model.Block // Added import
import tech.beskar.baid.intelijplugin.service.DiffService
import java.awt.BorderLayout // Added import
import javax.swing.JComponent
import javax.swing.JPanel

class DiffDialog(
    private val project: Project,
    private val diffService: DiffService,
    private val originalCodeBlock: Block.Code, // Changed
    private val oldContent: String,
    private val onApplyCallback: (appliedCodeBlock: Block.Code) -> Unit // Added
) : DialogWrapper(project) {

    init {
        title = "Review Changes: ${originalCodeBlock.filename!!}" // Use filename from block
        setOKButtonText("Accept") // Change OK button text
        setCancelButtonText("Reject") // Change Cancel button text
        init()
    }

    override fun createCenterPanel(): JComponent? {
        val diffRequest = DiffRequestFactory.getInstance().createSimpleDiffRequest(
            project,
            oldContent,
            originalCodeBlock.content, // This is the new content
            "Current File Content",
            "Suggested Changes"
        )

        // `window` and `disposable` are available from DialogWrapper
        val diffPanel = DiffManager.getInstance().createDiffPanel(window, project, disposable)
        diffPanel.setDiffRequest(diffRequest)

        val panel = JPanel(BorderLayout())
        panel.add(diffPanel.component, BorderLayout.CENTER)
        // Optional: Set preferred size for the dialog or diff panel
        // panel.preferredSize = Dimension(800, 600) // Example size
        return panel
    }

    // createActions() can remain as is, or be removed if we're relying on the default OK/Cancel actions
    // whose text we've already changed. For simplicity, let's keep it as is or remove it if not customizing actions further.
    // For this task, the button text change is sufficient.
    // If we keep createActions, the text change will apply to the actions returned by it.
    override fun createActions() = arrayOf(okAction, cancelAction)

    override fun doOKAction() { // "Accept"
        // The originalCodeBlock contains the filename and the new content.
        // Language and executable status are also in originalCodeBlock.
        diffService.applyChange(
            originalCodeBlock.filename!!,
            originalCodeBlock.content,
            onApplyCallback, // Pass the callback
            originalCodeBlock // Pass the block itself so callback gets it
        )
        super.doOKAction()
    }

    override fun doCancelAction() { // Will correspond to "Reject"
        diffService.rejectChange(originalCodeBlock.filename!!) // Use filename from block
        super.doCancelAction()
    }
}
