package tech.beskar.baid.intelijplugin.ui

import com.intellij.diff.DiffContentFactory // Added import
import com.intellij.diff.DiffManager
import com.intellij.diff.requests.SimpleDiffRequest // Added import
import com.intellij.openapi.fileTypes.FileTypes // Added import
import com.intellij.openapi.project.Project
import com.intellij.openapi.ui.DialogWrapper
import com.intellij.openapi.vfs.LocalFileSystem // Added import
import tech.beskar.baid.intelijplugin.model.Block
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
        val contentFactory = DiffContentFactory.getInstance()

        // Try to get VirtualFile for better content representation if filename is not null
        var fileType = FileTypes.UNKNOWN // Use imported FileTypes
        originalCodeBlock.filename?.let { fname ->
            val file = java.io.File(project.basePath, fname) // Assuming filename is relative to project root
            LocalFileSystem.getInstance().findFileByIoFile(file)?.let { virtualFile ->
                fileType = virtualFile.fileType
            }
            // If you want to ensure the file is refreshed from disk:
            // LocalFileSystem.getInstance().refreshAndFindFileByIoFile(file)?.let { virtualFile -> ... }
        }

        val currentDiffContent = contentFactory.create(project, oldContent, fileType)
        val newDiffContent = contentFactory.create(project, originalCodeBlock.content, fileType)

        val diffRequest = SimpleDiffRequest(
            null, // Dialog title (already set on DialogWrapper)
            currentDiffContent,
            newDiffContent,
            "Current File Content",
            "Suggested Changes"
        )

        // `window` and `disposable` are available from DialogWrapper
        val diffPanel = DiffManager.getInstance().createRequestPanel(project, disposable, window)
        diffPanel.setRequest(diffRequest)

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
