import React from "react"
import { useQuery } from "@tanstack/react-query"
import { api } from "../../lib/dashboardApi"
import { Card, COLORS, Empty, ErrorBox } from "./ui"
import { Table, Row, Cell } from "./Jobs"

export default function Tools() {
  const q = useQuery({
    queryKey: ["tools"],
    queryFn: api.listTools,
    refetchInterval: 30000,
  })

  if (q.isLoading) return <Empty>Loading tools…</Empty>
  if (q.error) return <ErrorBox>{(q.error as Error).message}</ErrorBox>
  const tools = q.data?.tools ?? []

  return (
    <Card title="Tool registry"
          subtitle={`${tools.length} tool${tools.length === 1 ? "" : "s"} available to the planner`}>
      {tools.length === 0 ? (
        <Empty>No tools registered.</Empty>
      ) : (
        <Table headers={["name", "description", "input schema"]}>
          {tools.map((t) => (
            <Row key={t.name} testId={`row-tool-${t.name}`}>
              <Cell mono>{t.name}</Cell>
              <Cell muted>{t.description}</Cell>
              <Cell mono>
                {t.payload_schema && Object.keys(t.payload_schema).length > 0 ? (
                  <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
                    {Object.entries(t.payload_schema).map(([k, v]) => (
                      <span key={k} style={{ fontSize: 11, color: COLORS.muted }}>
                        <span style={{ color: COLORS.gold }}>{k}</span>: {String(v)}
                      </span>
                    ))}
                  </div>
                ) : (
                  <span style={{ color: COLORS.dim, fontSize: 11 }}>(no fields)</span>
                )}
              </Cell>
            </Row>
          ))}
        </Table>
      )}
    </Card>
  )
}
