package tech.beskar.baid.intelijplugin.ui

import com.intellij.openapi.application.ApplicationManager // Added import
import com.intellij.openapi.command.WriteCommandAction
import com.intellij.openapi.editor.Document
import com.intellij.openapi.editor.Editor
import com.intellij.openapi.editor.Inlay
import com.intellij.openapi.editor.event.DocumentEvent // Added import
import com.intellij.openapi.editor.event.DocumentListener // Added import
import com.intellij.openapi.editor.markup.HighlighterLayer
import com.intellij.openapi.editor.markup.HighlighterTargetArea
import com.intellij.openapi.editor.markup.RangeHighlighter
import com.intellij.openapi.editor.markup.TextAttributes
import com.intellij.openapi.project.Project
import com.intellij.openapi.diagnostic.Logger
import com.intellij.ui.awt.RelativePoint
import tech.beskar.baid.intelijplugin.service.DiffHunk
import tech.beskar.baid.intelijplugin.service.DiffHunkType
import tech.beskar.baid.intelijplugin.service.InlineDiffService // Added import
import java.awt.Color
import java.awt.event.MouseAdapter
import java.awt.event.MouseEvent

object DiffHighlightAttributes {
    val DELETED_LINE_ATTRIBUTES = TextAttributes().apply {
        backgroundColor = Color(0xFFE0E0) // Light red
    }

    val MODIFIED_LINE_ATTRIBUTES = TextAttributes().apply {
        backgroundColor = Color(0xE0E0FF) // Light blue
    }
}

class InlineDiffDisplayManager(private val project: Project) {

    private val logger = Logger.getInstance(InlineDiffDisplayManager::class.java)
    private val activeHighlighters = mutableMapOf<Editor, MutableList<RangeHighlighter>>()
    private val activeInlays = mutableMapOf<Editor, MutableList<Inlay<*>>>()
    private val inlayRenderers = mutableMapOf<Inlay<*>, DiffActionInlayRenderer>()
    private val editorMouseListeners = mutableMapOf<Editor, MouseAdapter>()
    private val editorHunks = mutableMapOf<Editor, MutableList<DiffHunk>>()
    private val documentListeners = mutableMapOf<Editor, DocumentListener>() // Added

    private fun ensureMouseListener(editor: Editor) {
        if (editorMouseListeners.containsKey(editor)) return

        val mouseListener = object : MouseAdapter() {
            override fun mouseClicked(e: MouseEvent) {
                // Ensure the event source is an Editor content component
                val editorFromEvent = if (e.component is Editor) e.component as Editor else editor 
                if (editorFromEvent != editor) { // Check if the event is from the editor we're interested in
                    // This check might be redundant if the listener is added to editor.contentComponent
                    // but good as a safeguard if added to editor itself.
                    // For simplicity, we assume editor.addEditorMouseListener handles this.
                }

                val visualPosition = editor.xyToVisualPosition(e.point)
                val lineStartOffset = editor.document.getLineStartOffset(visualPosition.line)
                val lineEndOffset = editor.document.getLineEndOffset(visualPosition.line)
                
                // Get block elements for the line. Consider only those that are DiffActionInlayRenderer.
                val inlaysOnLine = editor.inlayModel.getBlockElementsInRange(lineStartOffset, lineEndOffset)
                    .filter { it.renderer is DiffActionInlayRenderer }

                for (inlay in inlaysOnLine) {
                    val inlayBounds = inlay.bounds ?: continue // Screen bounds
                    val editorLocationOnScreen = editor.contentComponent.locationOnScreen
                    
                    // Convert click point to screen coordinates then to be relative to inlay's on-screen origin
                    val clickPointOnScreen = RelativePoint(e.component, e.point).screenPoint

                    // Check if the click is within the inlay's visual bounds on screen
                    if (inlayBounds.contains(clickPointOnScreen)) {
                         val renderer = inlay.renderer as DiffActionInlayRenderer
                        // Translate click to be relative to the inlay's own coordinate system (top-left of inlay)
                        val clickRelativeToInlayX = clickPointOnScreen.x - inlayBounds.x
                        val clickRelativeToInlayY = clickPointOnScreen.y - inlayBounds.y
                        
                        // The handleClick in renderer is designed for coordinates relative to its own painting region.
                        // The `inlayY` parameter in handleClick was simplified to 0.
                        renderer.handleClick(editor, clickRelativeToInlayX, clickRelativeToInlayY, 0)
                        e.consume() 
                        return 
                    }
                }
            }
        }
        editor.contentComponent.addMouseListener(mouseListener)
        editorMouseListeners[editor] = mouseListener
    }

    private fun setupDocumentListener(editor: Editor) {
        if (documentListeners.containsKey(editor)) return

        val documentListener = object : DocumentListener {
            override fun documentChanged(event: DocumentEvent) {
                logger.info("Document changed for editor: ${editor.virtualFile?.name}. Clearing diff markers.")
                ApplicationManager.getApplication().invokeLater {
                    clearDiffMarkers(editor)
                }
            }
        }
        editor.document.addDocumentListener(documentListener)
        documentListeners[editor] = documentListener
    }
    
    fun showInlineDiffs(editor: Editor, oldText: String, newText: String, inlineDiffService: InlineDiffService) {
        ApplicationManager.getApplication().invokeLater {
            val hunks = inlineDiffService.calculateLineDiffs(oldText, newText)
            if (hunks.isEmpty()) {
                clearDiffMarkers(editor)
            } else {
                applyDiffMarkers(editor, hunks)
            }
            setupDocumentListener(editor)
        }
    }

    fun applyDiffMarkers(editor: Editor, hunks: List<DiffHunk>) {
        // This method should be called on EDT, ensured by showInlineDiffs and apply/rejectHunk
        clearDiffMarkers(editor) 
        if (hunks.isEmpty()) {
            editorHunks.remove(editor) // Ensure it's removed if hunks are empty
            return
        }
        editorHunks[editor] = hunks.toMutableList()
        
        ensureMouseListener(editor) // Sets up mouse listener

        val document = editor.document
        val markupModel = editor.markupModel
        val currentHighlighters = activeHighlighters.getOrPut(editor) { mutableListOf() }
        val currentInlays = activeInlays.getOrPut(editor) { mutableListOf() }

        for (hunk in hunks) {
            val attributes = when (hunk.type) {
                DiffHunkType.DELETE -> DiffHighlightAttributes.DELETED_LINE_ATTRIBUTES
                DiffHunkType.CHANGE -> DiffHighlightAttributes.MODIFIED_LINE_ATTRIBUTES
                DiffHunkType.ADD -> null 
                DiffHunkType.EQUAL -> null
            }

            if (attributes != null) {
                if (hunk.oldStartLine < hunk.oldEndLine && hunk.oldStartLine < document.lineCount) {
                    try {
                        val startOffset = document.getLineStartOffset(hunk.oldStartLine)
                        val endLineForOffset = (hunk.oldStartLine + (hunk.oldEndLine - hunk.oldStartLine -1)).coerceAtMost(document.lineCount -1)
                        val endOffset = if (hunk.oldEndLine < document.lineCount) {
                            document.getLineStartOffset(hunk.oldEndLine) 
                        } else {
                            document.getLineEndOffset(endLineForOffset)
                        }
                        if (startOffset < endOffset) {
                            val highlighter = markupModel.addRangeHighlighter(
                                startOffset, endOffset, HighlighterLayer.FIRST - 1, attributes, HighlighterTargetArea.LINES_IN_RANGE
                            )
                            currentHighlighters.add(highlighter)
                        } else {
                             logger.warn("Skipping highlighter for hunk (startOffset ($startOffset) >= endOffset ($endOffset)): $hunk.")
                        }
                    } catch (e: IndexOutOfBoundsException) {
                        logger.error("Error calculating offsets for highlighter hunk: $hunk.", e)
                    }
                }
            }
        }

        // Iterate over the stored hunks for the current editor
        editorHunks[editor]?.forEach { hunk -> // Use stored hunks
            val attributes = when (hunk.type) {
                DiffHunkType.DELETE -> DiffHighlightAttributes.DELETED_LINE_ATTRIBUTES
                DiffHunkType.CHANGE -> DiffHighlightAttributes.MODIFIED_LINE_ATTRIBUTES
                DiffHunkType.ADD -> null 
                DiffHunkType.EQUAL -> null
            }

            if (attributes != null) {
                if (hunk.oldStartLine < hunk.oldEndLine && hunk.oldStartLine < document.lineCount) {
                    try {
                        val startOffset = document.getLineStartOffset(hunk.oldStartLine)
                        val endLineForOffset = (hunk.oldStartLine + (hunk.oldEndLine - hunk.oldStartLine -1)).coerceAtMost(document.lineCount -1)
                        val endOffset = if (hunk.oldEndLine < document.lineCount) {
                            document.getLineStartOffset(hunk.oldEndLine) 
                        } else {
                            document.getLineEndOffset(endLineForOffset)
                        }
                        if (startOffset < endOffset) {
                            val highlighter = markupModel.addRangeHighlighter(
                                startOffset, endOffset, HighlighterLayer.FIRST - 1, attributes, HighlighterTargetArea.LINES_IN_RANGE
                            )
                            currentHighlighters.add(highlighter)
                        } else {
                             logger.warn("Skipping highlighter for hunk (startOffset ($startOffset) >= endOffset ($endOffset)): $hunk.")
                        }
                    } catch (e: IndexOutOfBoundsException) {
                        logger.error("Error calculating offsets for highlighter hunk: $hunk.", e)
                    }
                }
            }
        }
        
        editorHunks[editor]?.forEach { hunk -> // Use stored hunks for creating inlays
            val renderer = DiffActionInlayRenderer(hunk,
                onAccept = { acceptedHunk -> 
                    this.applyHunk(editor, acceptedHunk) // Updated callback
                },
                onReject = { rejectedHunk ->
                    this.rejectHunk(editor, rejectedHunk) // Updated callback
                }
            )
            
            val line = when (hunk.type) {
                DiffHunkType.DELETE, DiffHunkType.CHANGE -> hunk.oldStartLine
                DiffHunkType.ADD -> hunk.oldStartLine // Corrected: ADD inlay is positioned relative to old text structure
                DiffHunkType.EQUAL -> -1
            }

            if (line != -1 && line < document.lineCount) {
                try {
                    val offset = document.getLineStartOffset(line)
                    val inlay = editor.inlayModel.addBlockElement(offset, true, true, 0, renderer)
                    inlay?.let { currentInlays.add(it); inlayRenderers[it] = renderer }
                } catch (e: IndexOutOfBoundsException) {
                    logger.error("Error calculating offset for inlay at line $line (hunk: $hunk).", e)
                }
            } else if (line != -1) {
                 logger.warn("Skipping inlay for hunk (line out of bounds): $hunk, line: $line.")
            }
        }
    }

    fun applyHunk(editor: Editor, hunkToApply: DiffHunk) {
        val document = editor.document
        WriteCommandAction.runWriteCommandAction(project) {
            try {
                when (hunkToApply.type) {
                    DiffHunkType.ADD -> {
                        val insertLine = hunkToApply.oldStartLine // Assumes oldStartLine is where ADD begins conceptually
                        val offset = if (insertLine >= document.lineCount) {
                            document.textLength 
                        } else if (insertLine < 0) { 0 }
                        else { document.getLineStartOffset(insertLine) }
                        val textToInsert = hunkToApply.newContentLines.joinToString("\n") + "\n"
                        document.insertString(offset, textToInsert)
                    }
                    DiffHunkType.DELETE -> {
                        val startOffset = document.getLineStartOffset(hunkToApply.oldStartLine)
                        val endLine = hunkToApply.oldEndLine
                        val endOffset = if (endLine >= document.lineCount) {
                                            document.textLength
                                        } else { document.getLineStartOffset(endLine) }
                        document.deleteString(startOffset, endOffset)
                    }
                    DiffHunkType.CHANGE -> {
                        val deleteStartOffset = document.getLineStartOffset(hunkToApply.oldStartLine)
                        val deleteEndLine = hunkToApply.oldEndLine
                        val deleteEndOffset = if (deleteEndLine >= document.lineCount) {
                                                document.textLength
                                            } else { document.getLineStartOffset(deleteEndLine) }
                        document.deleteString(deleteStartOffset, deleteEndOffset)
                        
                        val textToInsert = hunkToApply.newContentLines.joinToString("\n") + (if (deleteStartOffset < document.textLength) "\n" else "")
                        document.insertString(deleteStartOffset, textToInsert)
                    }
                    DiffHunkType.EQUAL -> { /* Do nothing */ }
                }
            } catch (e: Exception) {
                logger.error("Error applying hunk: ${hunkToApply.type}", e)
            }
        }
        editorHunks[editor]?.remove(hunkToApply)
        val currentHunks = editorHunks[editor]?.toList() // Create a stable copy for the lambda

        ApplicationManager.getApplication().invokeLater {
            if (currentHunks != null && currentHunks.isNotEmpty()) {
                applyDiffMarkers(editor, currentHunks)
            } else {
                clearDiffMarkers(editor) // This will also remove from editorHunks
            }
        }
    }

    fun rejectHunk(editor: Editor, hunkToReject: DiffHunk) {
        logger.info("Rejected hunk: ${hunkToReject.type} oldLines: ${hunkToReject.oldStartLine}-${hunkToReject.oldEndLine}")
        editorHunks[editor]?.remove(hunkToReject)
        val currentHunks = editorHunks[editor]?.toList() // Create a stable copy

        ApplicationManager.getApplication().invokeLater {
            if (currentHunks != null && currentHunks.isNotEmpty()) {
                 applyDiffMarkers(editor, currentHunks)
            } else {
                clearDiffMarkers(editor) // This will also remove from editorHunks
            }
        }
    }

    fun clearDiffMarkers(editor: Editor) {
        // This method should be callable from any thread, but it modifies UI elements,
        // so it should ensure its operations are on EDT if not already.
        // However, since it's called by documentChanged via invokeLater, and by applyDiffMarkers (which is on EDT),
        // and apply/rejectHunk also call it via invokeLater, it should be fine.
        
        activeHighlighters[editor]?.forEach { highlighter ->
            try { editor.markupModel.removeHighlighter(highlighter) } 
            catch (e: Exception) { logger.error("Error removing highlighter: ${e.message}", e) }
        }
        activeHighlighters.remove(editor)
        
        val editorInlaysToRemove = inlayRenderers.keys.filter { it.editor == editor }
        editorInlaysToRemove.forEach { inlayRenderers.remove(it) }

        activeInlays[editor]?.forEach { inlay ->
            try { inlay.dispose() } 
            catch (e: Exception) { logger.error("Error disposing inlay: ${e.message}", e) }
        }
        activeInlays.remove(editor)
        
        editorMouseListeners[editor]?.let { listener ->
            editor.contentComponent.removeMouseListener(listener)
        }
        editorMouseListeners.remove(editor)
        
        documentListeners[editor]?.let { listener ->
            editor.document.removeDocumentListener(listener)
        }
        documentListeners.remove(editor)
        
        editorHunks.remove(editor)

        logger.info("Cleared all markers (highlights, inlays, listeners, hunks, doc listener) for editor: ${editor.virtualFile?.name}")
    }
    
    fun clearAllDiffMarkers() {
        val editorsToClear = (activeHighlighters.keys + activeInlays.keys + editorMouseListeners.keys + editorHunks.keys + documentListeners.keys).distinct().toList()
        ApplicationManager.getApplication().invokeLater { // Ensure clearDiffMarkers is called on EDT
            editorsToClear.forEach { editor ->
                 clearDiffMarkers(editor)
            }
        }
        logger.info("Scheduled clearing of all markers from all managed editors.")
    }
}
