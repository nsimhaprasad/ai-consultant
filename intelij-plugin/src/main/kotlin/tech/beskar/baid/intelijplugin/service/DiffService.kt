package tech.beskar.baid.intelijplugin.service

import com.intellij.openapi.application.ApplicationManager // Ensure this import is present
import com.intellij.openapi.diagnostic.Logger
import com.intellij.openapi.project.Project
import tech.beskar.baid.intelijplugin.model.Block // Ensure this import is present
import tech.beskar.baid.intelijplugin.ui.DiffDialog // Ensure this import is present
import java.io.File // Ensure this import is present
import java.nio.charset.StandardCharsets // Ensure this import is present

class DiffService(private val project: Project) {

    private val logger = Logger.getInstance(DiffService::class.java)

    fun showDiff(
        originalCodeBlock: Block.Code, // Changed
        oldContent: String,
        onApplyCallback: (appliedCodeBlock: Block.Code) -> Unit // Added
    ) {
        // filename and newContent are now inside originalCodeBlock
        val filename = originalCodeBlock.filename!!
        // val newContent = originalCodeBlock.content // Not directly needed by showDiff, but good to be aware

        logger.info("DiffService: showDiff called for filename: $filename")
        ApplicationManager.getApplication().invokeLater {
            val dialog = DiffDialog(
                project,
                this, // DiffService instance
                originalCodeBlock, // Pass the whole block
                oldContent,
                onApplyCallback // Pass the callback
            )
            dialog.show()
        }
    }

    fun applyChange(
        filename: String,
        newContent: String,
        onApplyCallback: (appliedCodeBlock: Block.Code) -> Unit,
        codeBlockToApply: Block.Code
    ) {
        logger.info("DiffService: applyChange called for filename: $filename")
        try {
            val file = File(project.basePath, filename)
            file.parentFile?.mkdirs()
            file.writeText(newContent, StandardCharsets.UTF_8)
            logger.info("Successfully applied changes to $filename")

            // Call the callback to notify the caller (e.g., ChatController)
            onApplyCallback(codeBlockToApply)

        } catch (e: Exception) {
            logger.error("Error applying changes to $filename: ${e.message}", e)
            // Optionally, notify user of error
        }
    }

    fun rejectChange(filename: String) {
        logger.info("DiffService: rejectChange called for filename: $filename. No changes were made.")
    }
}
