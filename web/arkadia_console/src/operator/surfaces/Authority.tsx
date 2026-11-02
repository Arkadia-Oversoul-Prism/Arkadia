import { ROLES, authorityState, PROVISIONED_SOVEREIGNS } from "../lib/authority";
import { APPROVAL_NOT_EXECUTION } from "../data/approvalNotExecution";
import { Card, Chip, Pill } from "../components/ui";

/**
 * 04 · Authority — the sovereign-control view.
 *
 * Makes explicit: IDENTITY ≠ AUTHORITY, AUTHORITY ≠ AUTHORIZATION,
 * APPROVAL ≠ EXECUTION. Flamekeeper UNPROVISIONED is shown here without a fake
 * "activate" flow (architecture §10, §9 Q2).
 */
export function Authority() {
  const auth = authorityState();

  return (
    <div className="grid" style={{ gap: 16 }}>
      <Card title="Governing authority">
        <div className="auth-posture">
          <Pill tone="unprovisioned">{auth.provision}</Pill>
          <p className="auth-statement">{auth.statement}</p>
          <p className="auth-constraint">{auth.constraint}</p>
        </div>

        <div className="grid cols-2 mt">
          <div>
            <div className="subhead">Unavailable while unprovisioned</div>
            <ul className="verb-list">
              {auth.gatedOperations.map((op) => (
                <li key={op} className="mono unavailable">
                  <span className="verb-mark">⊘</span> {op}
                </li>
              ))}
            </ul>
            <p className="tiny faint">
              These are rendered as unavailable, not as controls. Unavailable authority is visible,
              but never simulated.
            </p>
          </div>
          <div>
            <div className="subhead">Available regardless</div>
            <ul className="verb-list">
              {auth.independentOperations.map((op) => (
                <li key={op}>
                  <span className="verb-mark ok">·</span> {op}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </Card>

      <Card title="How authority is actually granted">
        <div className="subhead">Accepted encodings (enforcement layer)</div>
        <ul className="verb-list">
          {auth.encodings.map((e) => (
            <li key={e} className="mono">
              <span className="verb-mark">·</span> {e}
            </li>
          ))}
        </ul>
        <div className="subhead mt">Provisioned sovereign principals (F.2 / F.4)</div>
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>node_key</th>
                <th>Role</th>
                <th>access_level</th>
              </tr>
            </thead>
            <tbody>
              {PROVISIONED_SOVEREIGNS.map((s) => (
                <tr key={s.node_key}>
                  <td className="mono tiny">{s.node_key}</td>
                  <td className="tiny">{s.role}</td>
                  <td className="mono tiny">{s.access_level}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="tiny faint">
          Two distinct principals, each bound by an admin-set <span className="mono">node_key</span>{" "}
          claim. Distinct-authority governance across them is demonstrated; self-approval is
          prohibited for both.
        </p>
        <div className="prior-collapse">
          <span className="subhead" style={{ margin: 0 }}>
            Unresolved boundary
          </span>
          <span className="small">
            governance/roles.json declares <b>Govern</b> for Flamekeeper only, but{" "}
            <span className="mono">_has_govern_authority</span> also accepts{" "}
            <span className="mono">access_level &gt;= 3</span> — a tier existing node principals
            occupy. The declared model and the enforced model do not agree. This is not resolved;
            it is recorded.
          </span>
        </div>
      </Card>

      <Card title="The three distinctions">
        <div className="distinctions">
          {[
            ["IDENTITY", "AUTHORITY", "Who you are is not what you may decide."],
            ["AUTHORITY", "AUTHORIZATION", "What you may decide is not what you may reach."],
            ["APPROVAL", "EXECUTION", "Deciding is not doing."],
          ].map(([l, r, why]) => (
            <div key={`${l}-${r}`} className="distinction">
              <div className="row" style={{ gap: 10, alignItems: "center" }}>
                <span className="chain-node">{l}</span>
                <span className="neq">≠</span>
                <span className="chain-node">{r}</span>
              </div>
              <div className="tiny faint mt">{why}</div>
            </div>
          ))}
        </div>
      </Card>

      <Card title="Roles">
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>Role</th>
                <th>Permissions</th>
                <th>Governs</th>
              </tr>
            </thead>
            <tbody>
              {ROLES.map((r) => (
                <tr key={r.name}>
                  <td>
                    {r.name}
                    <div className="tiny faint">{r.description}</div>
                  </td>
                  <td>
                    <div className="chips">
                      {r.permissions.map((p) => (
                        <Chip key={p}>{p}</Chip>
                      ))}
                    </div>
                  </td>
                  <td>
                    {r.governs ? (
                      <Pill tone="unprovisioned">rule holds · unseated</Pill>
                    ) : (
                      <span className="tiny faint">no</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="tiny faint mt">
          The Govern permission is declared for the Flamekeeper role in governance/roles.json; no
          principal is seated in that role. The enforcement layer additionally admits the sovereign
          tier — see "How authority is actually granted" above.
        </p>
      </Card>

      <Card title="The worked boundary">
        <p className="small dim" style={{ marginTop: 0 }}>
          {APPROVAL_NOT_EXECUTION.means}
        </p>
        <div className="chips">
          {APPROVAL_NOT_EXECUTION.nonCollapses.map((nc) => (
            <Chip key={`${nc.left}-${nc.right}`}>
              {nc.left} ≠ {nc.right}
            </Chip>
          ))}
        </div>
      </Card>
    </div>
  );
}
