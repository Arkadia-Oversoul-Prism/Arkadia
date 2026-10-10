package com.arkadia.console

import org.junit.Assert.assertEquals
import org.junit.Test

class CaptureRecoveryPolicyTest {
    @Test
    fun syncingRecordBecomesRetryableAndCountsInterruptedAttempt() {
        val result = recoverInterruptedSyncState(
            syncState = CaptureSyncState.SYNCING,
            retryCount = 2,
            lastError = null
        )

        assertEquals(CaptureSyncState.RETRYABLE_FAILURE, result.syncState)
        assertEquals(3, result.retryCount)
        assertEquals(INTERRUPTED_CAPTURE_RECOVERY_MESSAGE, result.lastError)
    }

    @Test
    fun statesOtherThanSyncingRemainUnchanged() {
        val states = listOf(
            CaptureSyncState.PENDING_SYNC,
            CaptureSyncState.SYNCED,
            CaptureSyncState.CONFLICT,
            CaptureSyncState.RETRYABLE_FAILURE
        )

        states.forEach { state ->
            val original = CaptureRecoveryDecision(state, 4, "existing detail")
            val recovered = recoverInterruptedSyncState(
                syncState = original.syncState,
                retryCount = original.retryCount,
                lastError = original.lastError
            )
            assertEquals(original, recovered)
        }
    }

    @Test
    fun recoveryIsIdempotent() {
        val first = recoverInterruptedSyncState(CaptureSyncState.SYNCING, 0, null)
        val second = recoverInterruptedSyncState(
            first.syncState,
            first.retryCount,
            first.lastError
        )

        assertEquals(first, second)
    }
}
