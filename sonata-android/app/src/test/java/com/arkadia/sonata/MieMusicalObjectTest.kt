package com.arkadia.sonata

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
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
    fun keepDecisionIsInspectable() {
        val provenance = org.json.JSONObject(objectModel("kept").toJson()).getJSONObject("provenance")
        assertEquals("kept", provenance.getString("loop_decision"))
        assertEquals("parent-001", provenance.getString("parent_id"))
        assertEquals("octave_up", provenance.getString("transformation"))
    }

    @Test
    fun reviseDecisionIsInspectable() {
        val provenance = org.json.JSONObject(objectModel("revised").toJson()).getJSONObject("provenance")
        assertEquals("revised", provenance.getString("loop_decision"))
    }

    @Test
    fun undecidedResultRemainsUndecided() {
        val provenance = org.json.JSONObject(objectModel(null).toJson()).getJSONObject("provenance")
        assertTrue(!provenance.has("loop_decision"))
    }
}
