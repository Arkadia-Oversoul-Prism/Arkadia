/**
 * Spiral Grove frontend projection of the canonical A.I.S capability registry.
 *
 * Source of truth: spiral_grove.registry.build_ais_capability_catalog()
 * This file is intentionally read-only UI data. It grants no authorization,
 * does not replace Knowledge OS, and does not contain learner evidence.
 */

export type CapabilityStatus = 'DRAFT' | 'ACTIVE' | 'RETIRED'
export type LearnerCapabilityStatus = 'NOT_STARTED' | 'EXPLORING' | 'PRACTICING' | 'DEMONSTRATED' | 'MASTERED'
export type LearningActivityKind = 'research' | 'writing' | 'build' | 'reflection' | 'presentation' | 'field' | 'creative' | 'collaborative'
export type LearningActivityStatus = 'available' | 'completed'
export type LearningWorkMode = 'notes' | 'artifact' | 'field_log' | 'presentation_plan' | 'creative_brief' | 'team_plan'

export interface GroveCapability { id: string; slug: string; name: string; description: string; domain: string; level: number; prerequisites: string[]; outcomes: string[]; status: CapabilityStatus }
export interface LearnerCapabilityState { learner_id: string; capability_id: string; status: LearnerCapabilityStatus; demonstrated_level: number | null; confidence: number | null; evidence_refs: string[]; last_assessed_at: string | null; next_recommended_action: string | null }
export interface GroveLearningPathProjection { id: string; name: string; audience: string; capability_ids: string[]; progression_rules: Record<string, string>; reason: string; next_capability_id: string }
export interface GroveLearningActivityWorkSurface { mode: LearningWorkMode; prompt_label: string; placeholder: string; artifact_type: string }
export interface GroveLearningActivity { id: string; path_id: string; capability_id: string; title: string; instruction: string; kind: LearningActivityKind; status: LearningActivityStatus; evidence_required: boolean; estimated_minutes: number; deliverable: string; tools: string[]; work_surface: GroveLearningActivityWorkSurface }
export interface GroveLearningPathActivityProjection { path_id: string; capability_id: string; activities: GroveLearningActivity[] }

export const GROVE_DOMAINS = [
  { id: 'digital_intelligence', label: 'Digital Intelligence', icon: '◈', accent: '#00D4AA' },
  { id: 'creative_technology', label: 'Creative Technology', icon: '✦', accent: '#B08DE8' },
  { id: 'systems_thinking', label: 'Systems Thinking', icon: '⌘', accent: '#6A9FD8' },
  { id: 'human_development', label: 'Human Development', icon: '☍', accent: '#D46AA0' },
  { id: 'ecological_agricultural', label: 'Ground Intelligence', icon: '◇', accent: '#6DBE73' },
] as const

type CapabilitySeed = [string, string, string, string, string, number, string[], string[]]

const CAPABILITY_SEEDS: CapabilitySeed[] = [
  ['cap-digital-intelligence','digital-intelligence','Digital Intelligence','Use digital systems critically, safely, and effectively.','digital_intelligence',1,[],['navigate-digital-systems','evaluate-digital-information']],
  ['cap-ai-prompt-engineering','ai-prompt-engineering','AI Prompt Engineering','Design bounded prompts and evaluate AI-assisted outputs.','digital_intelligence',2,['cap-digital-intelligence'],['write-bounded-prompts','evaluate-ai-output']],
  ['cap-research-systems','research-systems','Research Systems','Find, verify, synthesize, and communicate evidence.','digital_intelligence',2,['cap-digital-intelligence'],['source-information','synthesize-evidence']],
  ['cap-digital-operations','digital-operations','Digital Operations','Design repeatable digital workflows and operating routines.','digital_intelligence',3,['cap-digital-intelligence'],['design-workflows','document-operations']],
  ['cap-no-code-development','no-code-development','No-Code Development','Build useful digital prototypes without traditional programming.','digital_intelligence',3,['cap-digital-intelligence','cap-digital-operations'],['prototype-workflows','ship-no-code-tools']],
  ['cap-content-systems','content-systems','Content Systems','Plan, produce, organize, and distribute digital content.','digital_intelligence',2,['cap-digital-intelligence'],['plan-content','build-content-workflows']],
  ['cap-ai-creative-workflows','ai-assisted-creative-workflows','AI-Assisted Creative Workflows','Use AI within accountable creative production workflows.','digital_intelligence',3,['cap-ai-prompt-engineering','cap-content-systems'],['direct-ai-creative-work','review-generated-assets']],
  ['cap-music-production-ai','music-production-with-ai','Music Production with AI','Create and refine music using AI-assisted production workflows.','creative_technology',2,['cap-ai-prompt-engineering'],['produce-ai-assisted-music','iterate-audio-assets']],
  ['cap-audio-engineering','audio-engineering','Audio Engineering','Record, edit, mix, and evaluate audio.','creative_technology',2,['cap-digital-intelligence'],['edit-audio','evaluate-audio-quality']],
  ['cap-creative-writing','creative-writing','Creative Writing','Develop original written work with structure, voice, and revision.','creative_technology',1,[],['write-original-work','revise-writing']],
  ['cap-storytelling','storytelling-systems','Storytelling Systems','Build coherent stories across written, audio, and visual media.','creative_technology',2,['cap-creative-writing'],['structure-stories','adapt-stories-across-media']],
  ['cap-media-production','media-production','Media Production','Plan and produce publishable media projects.','creative_technology',2,['cap-content-systems'],['produce-media','manage-production-workflows']],
  ['cap-visual-design','visual-design','Visual Design','Communicate ideas through effective visual composition and design.','creative_technology',2,['cap-digital-intelligence'],['compose-visual-assets','apply-design-principles']],
  ['cap-problem-solving','problem-solving','Problem Solving','Frame problems, generate options, test assumptions, and choose actions.','systems_thinking',1,[],['frame-problems','evaluate-options']],
  ['cap-decision-architecture','decision-architecture','Decision Architecture','Make explicit, evidence-aware decisions under constraints.','systems_thinking',2,['cap-problem-solving'],['map-decisions','surface-tradeoffs']],
  ['cap-operational-thinking','operational-thinking','Operational Thinking','Translate goals into repeatable systems and accountable actions.','systems_thinking',2,['cap-problem-solving'],['translate-goals-to-actions','design-operating-systems']],
  ['cap-workflow-design','workflow-design','Workflow Design','Model work as clear, measurable, improvable workflows.','systems_thinking',2,['cap-operational-thinking'],['map-workflows','improve-processes']],
  ['cap-pattern-recognition','pattern-recognition','Pattern Recognition','Identify meaningful structures across observations and evidence.','systems_thinking',2,['cap-problem-solving'],['identify-patterns','test-patterns']],
  ['cap-structured-reasoning','structured-reasoning','Structured Reasoning','Build clear arguments, inspect assumptions, and reason transparently.','systems_thinking',2,['cap-problem-solving'],['construct-arguments','inspect-assumptions']],
  ['cap-communication','communication','Communication','Communicate ideas clearly across audiences and formats.','human_development',1,[],['communicate-clearly','adapt-message-to-audience']],
  ['cap-presentation','presentation','Presentation','Present ideas with structure, confidence, evidence, and clarity.','human_development',2,['cap-communication'],['deliver-presentations','defend-ideas']],
  ['cap-confidence-building','confidence-building','Confidence Building','Develop confidence through practice, feedback, and demonstrated capability.','human_development',1,[],['receive-feedback','act-with-agency']],
  ['cap-identity-mapping','identity-mapping','Identity Mapping','Identify strengths, interests, values, and directions for development.','human_development',1,[],['map-strengths','articulate-direction']],
  ['cap-discipline-systems','discipline-systems','Discipline Systems','Build practical routines that support sustained work and learning.','human_development',2,['cap-confidence-building'],['design-routines','maintain-practice']],
  ['cap-collaborative-intelligence','collaborative-intelligence','Collaborative Intelligence','Work productively with peers through shared reasoning and responsibility.','human_development',2,['cap-communication'],['collaborate-effectively','peer-review-work']],
  ['cap-soil-systems','soil-systems','Soil Systems','Understand soil as a living production and ecological system.','ecological_agricultural',1,[],['observe-soil','manage-basic-soil-health']],
  ['cap-farm-operations','farm-operations','Farm Operations','Plan and execute basic agricultural production operations.','ecological_agricultural',2,['cap-soil-systems'],['plan-farm-tasks','track-farm-operations']],
  ['cap-food-systems','food-systems','Food Systems','Understand production, movement, access, and use of food resources.','ecological_agricultural',2,['cap-farm-operations'],['map-food-systems','identify-food-system-bottlenecks']],
  ['cap-water-systems','water-systems','Water Systems','Understand basic water resources, use, conservation, and management.','ecological_agricultural',1,[],['map-water-use','identify-conservation-actions']],
  ['cap-resource-management','resource-management','Resource Management','Allocate scarce resources responsibly against real constraints.','ecological_agricultural',2,['cap-problem-solving'],['allocate-resources','track-resource-use']],
  ['cap-sustainable-agriculture','sustainable-agriculture','Sustainable Agriculture','Design agricultural practices balancing productivity and ecological stewardship.','ecological_agricultural',3,['cap-soil-systems','cap-water-systems','cap-resource-management'],['design-sustainable-practices','evaluate-agricultural-tradeoffs']],
]

export const AIS_CAPABILITIES: GroveCapability[] = CAPABILITY_SEEDS.map(([id, slug, name, description, domain, level, prerequisites, outcomes]) => ({ id, slug, name, description, domain, level, prerequisites, outcomes, status: 'ACTIVE' }))
export const INITIAL_LEARNER_STATES: LearnerCapabilityState[] = AIS_CAPABILITIES.map(capability => ({ learner_id: 'local-learner', capability_id: capability.id, status: 'NOT_STARTED', demonstrated_level: null, confidence: null, evidence_refs: [], last_assessed_at: null, next_recommended_action: capability.prerequisites.length ? 'Complete the prerequisite capabilities first.' : 'Begin an exploration exercise.' }))

export function prerequisitesFor(capabilityId: string): GroveCapability[] {
  const byId = new Map(AIS_CAPABILITIES.map(item => [item.id, item])); const target = byId.get(capabilityId); if (!target) return []
  const result: GroveCapability[] = []; const seen = new Set<string>(); const visit = (id: string) => { if (seen.has(id)) return; const capability = byId.get(id); if (!capability) return; seen.add(id); capability.prerequisites.forEach(visit); if (id !== capabilityId) result.push(capability) }; target.prerequisites.forEach(visit); return result
}

export function learningPathFor(capabilityId: string, learnerState: LearnerCapabilityState, demonstratedCapabilityIds: Set<string> = new Set()): GroveLearningPathProjection | null {
  if (learnerState.capability_id !== capabilityId) return null; const target = AIS_CAPABILITIES.find(item => item.id === capabilityId); if (!target) return null
  const prerequisites = prerequisitesFor(capabilityId); const missing = prerequisites.find(item => !demonstratedCapabilityIds.has(item.id)); const nextCapability = missing || target; const capabilityIds = missing ? [missing.id, target.id] : [target.id]
  return { id: `path-${learnerState.learner_id}-${target.id}-v1`, name: `${target.name} progression`, audience: 'learner', capability_ids: capabilityIds, progression_rules: { entry: 'learner_capability_state', completion: 'evidence_required', next_step: 'registry_prerequisite_or_target' }, reason: missing ? `Prerequisite first: ${missing.name}.` : `Continue developing ${target.name}.`, next_capability_id: nextCapability.id }
}

const ACTIVITY_BLUEPRINTS: Record<LearningActivityKind, Omit<GroveLearningActivity, 'id' | 'path_id' | 'capability_id' | 'title' | 'instruction'>> = {
  research: { kind: 'research', status: 'available', evidence_required: true, estimated_minutes: 30, deliverable: 'A source-backed research brief.', tools: ['Knowledge OS', 'web/library sources'], work_surface: { mode: 'notes', prompt_label: 'Research notes', placeholder: 'Record your question, sources, claims, and what each source supports.', artifact_type: 'research brief' } },
  writing: { kind: 'writing', status: 'available', evidence_required: true, estimated_minutes: 30, deliverable: 'A structured written draft.', tools: ['writing workspace'], work_surface: { mode: 'artifact', prompt_label: 'Draft', placeholder: 'Write the work here. Focus on structure, clarity, and revision.', artifact_type: 'written draft' } },
  build: { kind: 'build', status: 'available', evidence_required: true, estimated_minutes: 45, deliverable: 'A working prototype or process design.', tools: ['chosen build tool'], work_surface: { mode: 'artifact', prompt_label: 'Build log', placeholder: 'Describe what you are building, the steps taken, decisions made, and what works.', artifact_type: 'prototype/build log' } },
  reflection: { kind: 'reflection', status: 'available', evidence_required: false, estimated_minutes: 15, deliverable: 'A concise reflection.', tools: ['reflection workspace'], work_surface: { mode: 'notes', prompt_label: 'Reflection', placeholder: 'What did you notice, what changed in your thinking, and what will you do next?', artifact_type: 'reflection' } },
  presentation: { kind: 'presentation', status: 'available', evidence_required: true, estimated_minutes: 30, deliverable: 'A presentation plan ready for live delivery.', tools: ['presentation tool'], work_surface: { mode: 'presentation_plan', prompt_label: 'Presentation plan', placeholder: 'Set out your opening, key points, evidence, audience, and closing.', artifact_type: 'presentation plan' } },
  field: { kind: 'field', status: 'available', evidence_required: true, estimated_minutes: 45, deliverable: 'A documented field observation.', tools: ['field notebook/camera'], work_surface: { mode: 'field_log', prompt_label: 'Field log', placeholder: 'Record what you observed, where, when, measurements or details, and what you infer.', artifact_type: 'field log' } },
  creative: { kind: 'creative', status: 'available', evidence_required: true, estimated_minutes: 45, deliverable: 'An original creative artifact.', tools: ['chosen creative tool'], work_surface: { mode: 'creative_brief', prompt_label: 'Creative workspace', placeholder: 'Define the concept, audience, creative choices, iterations, and what you produced.', artifact_type: 'creative artifact' } },
  collaborative: { kind: 'collaborative', status: 'available', evidence_required: true, estimated_minutes: 45, deliverable: 'A team plan or shared artifact.', tools: ['shared workspace'], work_surface: { mode: 'team_plan', prompt_label: 'Team work log', placeholder: 'Record roles, shared decisions, contributions, unresolved questions, and the team output.', artifact_type: 'collaborative artifact' } },
}

function activityKindFor(capability: GroveCapability): LearningActivityKind {
  if (capability.domain === 'digital_intelligence') return capability.id.includes('research') ? 'research' : capability.id.includes('no-code') || capability.id.includes('operations') ? 'build' : 'writing'
  if (capability.domain === 'creative_technology') return capability.id.includes('writing') || capability.id.includes('storytelling') ? 'creative' : 'build'
  if (capability.domain === 'systems_thinking') return capability.id.includes('pattern') ? 'research' : 'build'
  if (capability.domain === 'human_development') return capability.id.includes('presentation') || capability.id.includes('communication') ? 'presentation' : capability.id.includes('collaborative') ? 'collaborative' : 'reflection'
  return capability.id.includes('soil') || capability.id.includes('farm') || capability.id.includes('water') ? 'field' : 'research'
}

/** UI projection of the explicit SG-03 activity runtime contract. It supplies stable activity definitions; it does not autonomously generate exercises, create evidence, or mutate learner state. */
export function learningActivitiesFor(path: GroveLearningPathProjection): GroveLearningPathActivityProjection {
  const capabilityId = path.next_capability_id; const capability = AIS_CAPABILITIES.find(item => item.id === capabilityId)
  if (!capability) return { path_id: path.id, capability_id: capabilityId, activities: [] }
  const kind = activityKindFor(capability); const blueprint = ACTIVITY_BLUEPRINTS[kind]
  return { path_id: path.id, capability_id: capabilityId, activities: [{ ...blueprint, id: `activity-${path.id}-${capabilityId}-01`, path_id: path.id, capability_id: capabilityId, title: `${capability.name}: ${kind} activity`, instruction: `Apply ${capability.name} through a ${kind} task. Produce the stated deliverable and keep a clear record of your process.` }] }
}
