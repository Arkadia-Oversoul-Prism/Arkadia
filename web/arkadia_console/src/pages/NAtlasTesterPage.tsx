/**
 * The external N-ATLaS developer test, as a standalone surface of the one app.
 *
 * This view was answered by the retired operator bundle at `/n-atlas-lab` and
 * `/n-atlas-tester`. Those direct routes stay live and are now served by the
 * canonical application's own `index.html`, so an inbound link is unchanged.
 *
 * It renders outside the shared shell on purpose: the surface's contract is "a
 * short external test … no Arkadia architecture knowledge is required", and the
 * product shell (primary navigation, identity chrome, aurora field) would
 * contradict that promise. That is the one declared use of `SurfaceDef.standalone`.
 */
import { NAtlasTester } from "../operator/surfaces/NAtlasTester";
import "../operator/operator.css";

export function NAtlasTesterPage() {
  return (
    <div className="ark-operator">
      <NAtlasTester />
    </div>
  );
}
