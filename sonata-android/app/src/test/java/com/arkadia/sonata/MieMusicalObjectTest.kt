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
        val json = objectModel("kept").toJson()
        assertTrue(json.contains("\"loop_decision\": \"kept\""))
        assertTrue(json.contains("\"parent_id\": \"parent-001\""))
        assertTrue(json.contains("\"transformation\": \"octave_up\""))
    }

    @Test
    fun reviseDecisionIsInspectable() {
        val json = objectModel("revised").toJson()
        assertTrue(json.contains("\"loop_decision\": \"revised\""))
    }

    @Test
    fun undecidedResultRemainsUndecided() {
        val json = objectModel(null).toJson()
        assertEquals(null, org.json.JSONObject(json).getJSONObject("provenance").optString("loop_decision", null))
    }
}
