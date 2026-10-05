package com.arkadia.sonata

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class MieMusicalObjectTest {
    private fun objectModel(decision: String?) = MieMusicalObject(
        sourcePath = "/tmp/mie.wav",
        durationMs = 1000L,
        inputType = "melody_candidate",
        confidence = 0.9f,
        rms = 0.2f,
        zeroCrossingRate = 0.1f,
        detectedPitchHz = 440f,
        detectedMidi = 69f,
        parentId = "parent-001",
        transformation = "octave_up",
        loopDecision = decision
    )

    @Test
    fun keepDecisionIsRepresentedOnTheResultObject() {
        val result = objectModel("kept")
        assertEquals("kept", result.loopDecision)
        assertEquals("parent-001", result.parentId)
        assertEquals("octave_up", result.transformation)
    }

    @Test
    fun reviseDecisionIsRepresentedOnTheResultObject() {
        val result = objectModel("revised")
        assertEquals("revised", result.loopDecision)
        assertEquals("parent-001", result.parentId)
    }

    @Test
    fun undecidedResultRemainsUndecided() {
        assertNull(objectModel(null).loopDecision)
    }

    @Test
    fun cloneProvenanceAndNameSurviveJson() {
        val result = objectModel(null).copy(displayName = "Idea A", clonedFromId = "source-001")
        val json = result.toJson()
        assertEquals("Idea A", org.json.JSONObject(json).getJSONObject("provenance").getString("display_name"))
        assertEquals("source-001", org.json.JSONObject(json).getJSONObject("provenance").getString("cloned_from_id"))
    }

    @Test
    fun deletedObjectCarriesDeletionTimestamp() {
        val result = objectModel(null).copy(deletedAtEpochMs = 1234L)
        assertEquals(1234L, result.deletedAtEpochMs)
    }
}
