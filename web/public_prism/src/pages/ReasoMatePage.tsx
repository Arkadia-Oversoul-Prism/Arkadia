/** ReasoMate is the authenticated messenger surface of the canonical Social Field.
 *
 * One component, two windows: NovaNet mounts the public field, ReasoMate mounts the
 * authenticated human ↔ Arkana thread. Both read the same `api/messages` runtime —
 * this is a lens, not a second conversational system.
 */
import SocialFieldVerified from './SocialFieldVerified'

export default function ReasoMatePage() {
  return <SocialFieldVerified initialMode="reasomate" />
}
