package com.arkadia.console

/**
 * Pure recovery policy for queue records left in SYNCING when the app process
 * stopped before it persisted a terminal reconciliation result.
 *
 * The backend capture endpoint is idempotent for the authenticated subject and
 * stable capture ID, so RETRYABLE_FAILURE can safely replay the same capture.
 */
internal const val INTERRUPTED_CAPTURE_RECOVERY_MESSAGE =
    "Recovered after interrupted sync; safe replay is pending"

internal data class CaptureRecoveryDecision(
    val syncState: CaptureSyncState,
    val retryCount: Int,
    val lastError: String?
)

internal fun recoverInterruptedSyncState(
    syncState: CaptureSyncState,
    retryCount: Int,
    lastError: String?
): CaptureRecoveryDecision {
    if (syncState != CaptureSyncState.SYNCING) {
        return CaptureRecoveryDecision(syncState, retryCount, lastError)
    }

    return CaptureRecoveryDecision(
        syncState = CaptureSyncState.RETRYABLE_FAILURE,
        retryCount = retryCount + 1,
        lastError = INTERRUPTED_CAPTURE_RECOVERY_MESSAGE
    )
}
