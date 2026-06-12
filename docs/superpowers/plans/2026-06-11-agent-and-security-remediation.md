# ByteSavor Agent And Security Remediation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Correct the false-positive fixes, close the authentication and image-input security gaps, establish a real feedback-aware conversation state, and upgrade the fixed BYTE pipeline into a stateful tool-using Agent.

**Architecture:** Keep the existing FastAPI routes and domain services, but introduce explicit boundaries for authentication exchange, validated image inputs, conversation state, tool execution, and agent planning. Deliver the work in independently testable phases so the system remains demonstrable after every phase.

**Tech Stack:** FastAPI, Pydantic v2, SQLAlchemy async, Redis, httpx, pytest, Vue 3/uni-app, optional LangGraph after deterministic state-machine behavior is tested.

---

## Phase 1: Correctness And Security Baseline

### Task 1: Make VLM Unavailability An Explicit Error Contract

**Files:**
- Modify: `app/routers/sense.py`
- Modify: `app/schemas.py`
- Test: `tests/test_sense.py`

- [ ] Keep the existing failing test that requires `status=error` and `error.code=VLM_UNAVAILABLE`.
- [ ] Add tests proving the response contains no fabricated ingredients.
- [ ] Return `ErrorResponse(code="VLM_UNAVAILABLE")` when the Provider returns `None`.
- [ ] Run `JWT_SECRET=test-review-secret pytest -q tests/test_sense.py`.
- [ ] Run the full pytest suite.

### Task 2: Validate Image Inputs At The Server Boundary

**Files:**
- Create: `app/services/image_input.py`
- Modify: `app/routers/sense.py`
- Modify: `app/routers/quality.py`
- Modify: `app/routers/nutrition.py`
- Modify: `app/routers/guide.py`
- Modify: `app/routers/agent.py`
- Test: `tests/test_image_input.py`

- [ ] Write tests rejecting unsupported schemes, localhost, loopback, private/link-local IPs, non-image content types, and bodies larger than 5 MiB.
- [ ] Write tests accepting a bounded `data:image/jpeg;base64,...` payload and a mocked HTTPS image response.
- [ ] Implement one validator that returns a normalized safe image source.
- [ ] For remote URLs, use `httpx` streaming with redirect limits, timeout, content type validation, content length validation, and an actual byte counter.
- [ ] Ensure all image-consuming routes call the same validator before VLM invocation.
- [ ] Run the new tests and full suite.

### Task 3: Separate Demo Authentication From WeChat Authentication

**Files:**
- Modify: `app/core/config.py`
- Modify: `app/schemas.py`
- Create: `app/services/wechat_auth.py`
- Modify: `app/routers/auth.py`
- Modify: `.env.example`
- Modify: `docker-compose.yml`
- Test: `tests/test_auth.py`

- [ ] Add `AUTH_MODE=demo|wechat`, with production deployment requiring `wechat`.
- [ ] Preserve the current openid endpoints only under explicit demo mode.
- [ ] Add a `code` login/register request for WeChat mode.
- [ ] Exchange code server-side through the official `code2session` endpoint using server-side credentials.
- [ ] Reject client-provided openid in WeChat mode.
- [ ] Mock WeChat HTTP responses in tests; cover invalid code, upstream timeout, and missing openid.
- [ ] Run auth tests and full suite.

### Task 4: Enforce Production Secrets And Origin Policy At Startup

**Files:**
- Modify: `app/core/config.py`
- Modify: `app/core/security.py`
- Modify: `app/main.py`
- Modify: `.env.example`
- Test: `tests/test_security_config.py`

- [ ] Write tests rejecting production JWT secrets shorter than 32 bytes and known placeholders.
- [ ] Validate configuration during lifespan startup rather than first token creation.
- [ ] Add explicit `CORS_ORIGINS`; reject wildcard origins when credentials are enabled in production.
- [ ] Disable detailed errors and interactive docs in production mode.
- [ ] Run configuration tests and full suite.

## Phase 2: Real Feedback-Aware Conversation State

### Task 5: Add A Stable Conversation Identifier

**Files:**
- Modify: `app/schemas.py`
- Modify: `app/routers/agent.py`
- Modify: `app/services/agent.py`
- Modify: `bsapp/src/api/index.js`
- Modify: `bsapp/src/pages/home/home.vue`
- Test: `tests/test_agent.py`

- [ ] Add `conversation_id` to `AgentRequest`; generate it client-side once per chat session.
- [ ] Keep `trace_id` unique per execution and never use it as the conversation key.
- [ ] Return both identifiers in Agent responses.
- [ ] Add tests proving two executions share one conversation but have distinct trace IDs.

### Task 6: Replace The Broken In-Process Preference Cache

**Files:**
- Replace: `app/services/session_prefs.py`
- Modify: `app/services/feedback.py`
- Modify: `app/routers/feedback.py`
- Modify: `app/services/agent.py`
- Modify: `app/routers/agent.py`
- Test: `tests/test_agent_feedback_loop.py`

- [ ] Make feedback requests carry the relevant `conversation_id`.
- [ ] Store conversation preferences in Redis under `bs:conversation:{id}:prefs` with a documented TTL.
- [ ] Load persistent profile preferences and conversation preferences before Decision.
- [ ] Pass merged preferences into `decide_fn`; remove the hard-coded empty list.
- [ ] Write an end-to-end test showing a high rating changes a later recommendation reason/order in the same conversation.
- [ ] Delete the unused `all_prefs` code and process-global dictionary.

## Phase 3: Stateful Tool-Using Agent

### Task 7: Define Agent State And Tool Contracts

**Files:**
- Create: `app/agent/state.py`
- Create: `app/agent/tools.py`
- Create: `app/agent/planner.py`
- Modify: `app/services/providers.py`
- Test: `tests/test_agent_planner.py`

- [ ] Define typed `AgentState`, `AgentAction`, `ToolResult`, `StageAttempt`, and termination reasons.
- [ ] Register Sense, Decision, Task, Nutrition, Quality, Guide, and Feedback as allowlisted tools.
- [ ] Implement a deterministic planner first: route by intent and state, request clarification for missing required inputs, and enforce a maximum step count.
- [ ] Test recommend-only, image-recognition, nutrition, guide, shopping, clarification, and failure-recovery paths.

### Task 8: Introduce Conditional Execution And Replanning

**Files:**
- Create: `app/agent/runtime.py`
- Modify: `app/routers/agent.py`
- Replace: `app/services/langgraph_agent.py`
- Test: `tests/test_agent_runtime.py`

- [ ] Execute one planned action at a time and merge each Tool result into state.
- [ ] Re-run the planner after every Tool result.
- [ ] Add branches for VLM failure, empty recommendation, fallback recommendation, and missing user input.
- [ ] Return ordered plan/tool/result events for frontend rendering.
- [ ] Prove the runtime can skip unnecessary tools and stop safely.

### Task 9: Integrate LangGraph After Runtime Semantics Pass

**Files:**
- Modify: `requirements.txt`
- Replace: `app/services/langgraph_agent.py`
- Modify: `app/routers/agent.py`
- Test: `tests/test_langgraph_agent.py`

- [ ] Add the LangGraph dependency with a bounded compatible version.
- [ ] Map the tested state/runtime semantics into `StateGraph`.
- [ ] Use a checkpointer keyed by `conversation_id`.
- [ ] Keep tools backend-controlled; the LLM may select only schema-valid allowlisted actions.
- [ ] Add recursion/step limits and tests for termination.
- [ ] Switch the production Agent route to the compiled graph.

### Task 10: Render The Real Agent Process In The Frontend

**Files:**
- Modify: `bsapp/src/api/index.js`
- Modify: `bsapp/src/pages/home/home.vue`
- Test: frontend browser smoke flow

- [ ] Persist `conversation_id` for the active chat.
- [ ] Render plan, tool start, tool result, fallback, clarification, and final answer events.
- [ ] Allow the user to answer Agent clarification questions without losing state.
- [ ] Preserve recipe export/history behavior.
- [ ] Verify desktop and mobile layouts with browser screenshots.

## Phase 4: Recommendation Evaluation And Data Quality

### Task 11: Build An Offline Recommendation Evaluation Set

**Files:**
- Create: `tests/fixtures/recommendation_eval.json`
- Create: `app/evaluation/recommendation.py`
- Create: `tests/test_recommendation_quality.py`

- [ ] Add at least 50 manually reviewed queries with relevant recipe IDs.
- [ ] Compute HitRate@5 and NDCG@5.
- [ ] Compare current weights against at least two alternatives.
- [ ] Record chosen weights and evidence in `docs/CORE_TECH.md`.

### Task 12: Add Candidate Retrieval And Data Confidence

**Files:**
- Create: database migration for recipe ingredient/tag indexes or relation tables
- Modify: `app/models/recipe.py`
- Modify: `app/services/decision.py`
- Modify: `app/seed/seed_recipes.py`
- Test: decision and migration tests

- [ ] Add candidate recall by ingredient/tag before in-memory ranking.
- [ ] Add `data_quality`, `nutrition_confidence`, and `human_verified_at`.
- [ ] Mark estimated nutrition in API responses and frontend UI.
- [ ] Benchmark candidate count and latency before/after.

## Verification Gate

- [ ] `pytest -q` passes with no failed tests.
- [ ] H5 production build passes.
- [ ] Agent tests prove dynamic tool selection, conditional branches, replanning, termination, and conversation memory.
- [ ] Security tests prove production auth does not accept arbitrary openid and image inputs cannot target private networks or exceed limits.
- [ ] Browser demo proves the UI shows an actual multi-step Agent process.
- [ ] `CORE_TECH.md`, `REVIEW_FIXES.md`, API docs, and defense materials match the implemented system.

