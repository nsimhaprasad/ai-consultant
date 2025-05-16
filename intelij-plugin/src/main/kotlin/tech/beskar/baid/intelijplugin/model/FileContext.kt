package tech.beskar.baid.intelijplugin.model

import com.intellij.openapi.fileEditor.FileEditorManager
import com.intellij.openapi.project.Project
import org.json.JSONObject


class FileContext
(
    val fileContent: String?, val filePath: String?, val fileName: String?, val isOpen: Boolean
) {
    fun toJson(): JSONObject {
        val json = JSONObject()
        json.put("file_content", fileContent)
        json.put("file_path", filePath)
        json.put("file_name", fileName)
        json.put("is_open", isOpen)
        return json
    }

    companion object {
        fun fromCurrentEditor(project: Project): FileContext {
            // Get the currently open file from the editor
            val fileEditorManager =
                FileEditorManager.getInstance(project)
            val editor = fileEditorManager.selectedTextEditor
            val virtualFile =
                if (fileEditorManager.selectedFiles.size > 0) fileEditorManager.selectedFiles[0] else null

            // Get file content and metadata
            val fileText =
                editor?.document?.text ?: "No file open."
            val filePath = virtualFile?.path ?: "No file path available"
            val fileName = virtualFile?.name ?: "No file name available"
            val isOpen = editor != null

            return FileContext(fileText, filePath, fileName, isOpen)
        }
    }
}