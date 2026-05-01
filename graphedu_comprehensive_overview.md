# GraphEdu — Comprehensive Project Overview
### Working, Tech Stack & AI/ML System Integration

---

## 1. What Is GraphEdu?

GraphEdu is an **AI-powered adaptive educational platform** built for university-level courses. It replaces a static, one-size-fits-all teaching model with a dynamic system where:

- The **curriculum itself is a knowledge graph** — topics have prerequisites, and learning has a logical order
- **Tests adapt in real-time** to each student's cognitive level using Bloom's Taxonomy
- **AI generates questions, remedial plans, and entire curricula** on-demand
- A **Graph Neural Network** predicts which topics a student is likely to fail *before* they fail them
- Every weak area surfaces in an **interactive visual graph** with AI-generated study plans attached

The system has **three roles** — Student, Faculty, and Admin — each with distinct capabilities and workflows.

---

## 2. Complete Tech Stack

### 2a. Frontend (React App — Port 5173)

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Framework | **React 18 + Vite** | Fast HMR dev server, component-based UI |
| Routing | **React Router v6** | Role-based protected routes |
| Styling | **Tailwind CSS v3** | Utility-first responsive design |
| Graph Visualization | **react-force-graph-2d** (D3.js) | Physics-based curriculum graph canvas |
| Auth | **Firebase Auth SDK** | Google OAuth 2.0 sign-in |
| HTTP | **Axios + native fetch** | API communication |
| Icons | **Lucide React** | Consistent icon set |
| State | **React hooks + Context API** | Theme, user session |
| Build Tool | **Vite** | ES module bundling |

**Key Pages:**

| Route | Page | Role |
|-------|------|------|
| `/dashboard` | Student home — progress, modules, quick quiz | Student |
| `/quiz` | Adaptive MCQ + Coding quiz engine | Student |
| `/result` | Score + AI recommendations + weak area detection | Student |
| `/expand` | Interactive D3 knowledge graph canvas | Student + Faculty |
| `/descriptive-test` | Long-form text answer test | Student |
| `/coding-test` | AI-generated coding challenge | Student |
| `/my-tests` | Performance history + AI study plans | Student |
| `/analytics` | Score charts, BTL progression graphs | Student |
| `/faculty/dashboard` | Question bank, student management, graph seeding | Faculty |
| `/faculty/reports/:id` | Per-test class analytics | Faculty |
| `/admin` | Subject catalog, faculty access approvals | Admin |

---

### 2b. Node.js/Express Backend (Port 5001)

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Runtime | **Node.js v20 + ES Modules** | Server runtime |
| Framework | **Express.js** | REST API server |
| Primary Database | **MongoDB + Mongoose** | Documents: users, tests, progress, AI plans |
| Graph Database | **Neo4j** | Curriculum knowledge graph |
| Auth | **Firebase Admin SDK** | Token verification |
| LLM (cloud) | **Google Gemini 2.5 Flash** (`@google/generative-ai`) | Graph generation, question bank |
| LLM (local) | **Ollama REST API** (LLaMA 3) | Adaptive question generation |
| Code Execution | **Compiler route** (sandboxed) | Runs student code for test cases |
| Config | **dotenv** | Environment variables |

**MongoDB Collections:**

| Collection | Model | Contents |
|-----------|-------|---------|
| `users` | `User` | Name, email, role, graphId, Firebase UID |
| `ai_generated_questions` | `AIGeneratedQuestion` | Questions with BTL level, status (pending/approved/rejected) |
| `student_chapter_progress` | `StudentChapterProgress` | Per-chapter BTL level + average score |
| `student_test_records` | `StudentTestRecord` | Score, percentage, BTL at attempt, streak |
| `student_ai_plans` | `StudentAIPlan` | RAG-generated remedial plans per chapter |
| `subject_graphs` | `SubjectGraph` | AI-generated curriculum JSON, locked state |
| `subjects` | `Subject` | Course catalog |
| `faculty_subject_access` | `FacultySubjectAccess` | Approval workflow records |
| `submissions` | `Submission` | Full quiz submissions with per-question results |
| `tests` | `Test` | Faculty-created test configurations |

**API Route Groups:**

| Prefix | Router | Responsibilities |
|--------|--------|----------------|
| `/api/auth` | `authRoutes` | Login, register, Firebase sync |
| `/api/ai` | `aiQuestionRoutes` | Generate questions, approve/reject, question bank |
| `/api/student-tests` | `studentTestRoutes` | Record results, generate AI plans |
| `/api/faculty` | `facultyRoutes` | Students list, subject requests, class stats |
| `/api/syllabus` | `syllabusRoutes` | Graph generation, graph data fetch |
| `/api/submissions` | `submissionRoutes` | Save/fetch quiz submissions |
| `/api/admin` | `adminRoutes` | Faculty access approval |
| `/api/compile` | `compilerRoutes` | Execute student code against test cases |
| `/api/reports` | `reportRoutes` | Analytics for faculty per-test view |

---

### 2c. Python FastAPI ML Backend (Port 8001)

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Framework | **FastAPI + Uvicorn** | Async REST API |
| GNN Framework | **PyTorch Geometric** | GCN layer (`GCNConv`) |
| Deep Learning | **PyTorch** | Tensor ops, model training, MC Dropout |
| Vector DB | **FAISS** (`langchain-community`) | Textbook embedding index |
| Embeddings | **HuggingFace `all-MiniLM-L6-v2`** | 384-dim sentence embeddings |
| LLM | **Ollama (LLaMA 3)** via `langchain-ollama` | RAG text generation |
| Orchestration | **LangChain LCEL** | RAG pipeline chaining |
| Text Splitting | **LangChain text splitters** | Markdown + recursive chunking |
| Config | **python-dotenv** | Environment variables |
| CORS | **FastAPI CORSMiddleware** | Allow React frontend origin |

**Endpoints:**

| Endpoint | Method | Function |
|----------|--------|---------|
| `/health` | GET | Check if graph data is loaded |
| `/predict` | POST | GCN + BNN inference → per-topic failure probabilities |
| `/generate-remedial-content` | POST | RAG pipeline → personalized study plan |

---

### 2d. Infrastructure & Orchestration

| Service | Port | Role |
|---------|------|------|
| **MongoDB** | 27017 | Document database |
| **Neo4j** | 7687 | Graph database |
| **Ollama** | 11434 | Local LLM server (LLaMA 3) |
| **FastAPI ML** | 8001 | Python ML backend |
| **Node.js API** | 5001 | Main application backend |
| **React (Vite)** | 5173 | Frontend dev server |

**`start_ecosystem.js`** — A custom Node.js process orchestrator that:
1. Checks each port (TCP socket probe) to see if a service is already running
2. If running externally → marks as `🟢 External`, skips
3. If not running → spawns the process using `child_process.spawn()`
4. Streams `stdout`/`stderr` from all services into a real-time terminal dashboard
5. On `Ctrl+C` → kills all spawned processes (but leaves external ones untouched)

---

## 3. System Working — End-to-End User Journeys

### 3a. Student Journey

```
[1] REGISTRATION / LOGIN
    ├── Email+Password → MongoDB user created, JWT issued
    └── Google Sign-In → Firebase OAuth → Firebase UID stored in MongoDB
            └── Graph ID generated: first 4 letters of name + 4 random digits
                 e.g. "Karthik" → "kart2849"

[2] STUDENT DASHBOARD
    ├── Displays 6 curriculum modules (fetched from Neo4j via /api/syllabus/graph-data)
    ├── Progress bar per module (completed topics from Neo4j :COMPLETED edges)
    └── Quick-launch buttons → Quiz, Graph, Tests

[3] TAKING A QUIZ (Adaptive MCQ Engine)
    ├── Student selects a module (e.g. "Trees")
    ├── System filters question pool to that module's prerequisite topic IDs
    ├── Starts at BTL Level 1 (Remember)
    │    ├── 2 consecutive correct → BTL Level UP (modal notification shown)
    │    └── 1 wrong → BTL Level DOWN
    ├── Up to 20 questions served adaptively (question pool filtered by current BTL)
    ├── Code questions run against test cases via /api/compile (sandboxed execution)
    └── On submit → score calculated, weakTopicIds identified per topic

[4] RESULT PAGE
    ├── Score percentage + pass/fail indicator
    ├── Knowledge Distribution chart (Core/Applications/Analysis)
    ├── "Knowledge Roadmap" → prerequisite recommendations for weak topics
    │    └── Graph-traversal: weak topic IDs → find which module's prerequisites they are
    └── "Get In-Depth Analysis" button → navigates to /expand?view=galaxy&weak=p1,p2,...

[5] KNOWLEDGE GRAPH (Expand Page)
    ├── Fetches dynamic modules from Neo4j (sorted alphabetically)
    ├── "Focused Mode" → shows one module + its prerequisites as a star topology
    ├── "Galaxy Mode" → shows ALL modules + ALL prerequisites interconnected
    ├── Weak nodes (from URL params) highlighted in red with glow halo
    └── Clicking a weak node → triggers RAG fetch from Python ML backend (port 8001)
             └── Returns personalized 3-sentence study plan shown in side panel

[6] AI STUDY PLAN (My Tests Page)
    ├── Lists all test records with BTL level at each attempt
    ├── "Generate AI Plan" button → calls /api/student-tests/generate-plan
    │    └── Backend fetches student's averageScore + currentBTLLevel from MongoDB
    │    └── Calls Python FastAPI /generate-remedial-content (RAG pipeline)
    │    └── Saves plan to student_ai_plans collection
    └── Plan displayed: weak areas, recommended practice, improvement steps
```

---

### 3b. Faculty Journey

```
[1] SUBJECT ACCESS REQUEST
    ├── Faculty views subject catalog (MongoDB subjects collection)
    ├── Selects subject(s) → POST /api/faculty/request-multiple-subjects
    └── Creates FacultySubjectAccess records with status = "pending"

[2] ADMIN APPROVAL
    └── Admin sees pending requests → approves/rejects via PATCH endpoint
         └── Updates FacultySubjectAccess status to "approved"/"rejected"

[3] CURRICULUM GRAPH GENERATION (Faculty Dashboard — CORE FEATURE)
    ├── Faculty enters 6 module names (syllabus)
    ├── Frontend calls POST /api/syllabus/generate-graph
    ├── Backend sends module list to Google Gemini 2.5 Flash
    │    └── Gemini returns structured JSON: modules + prerequisites + colors + descriptions
    ├── Backend seeds the graph into Neo4j via dynamicSeeder.js
    │    └── Creates :Topic nodes and :PRECEDES relationships
    └── SubjectGraph saved to MongoDB (generatedGraphJSON + locked state)

[4] QUESTION BANK GENERATION (Faculty Dashboard)
    ├── Faculty selects chapter → clicks "Generate 40 Questions"
    ├── Backend calls Google Gemini 2.5 Flash with BTL3 + BTL4 constraints
    ├── 40 MCQ questions returned as JSON → bulk-inserted into ai_generated_questions
    ├── Faculty reviews questions → Approve / Reject each one
    └── Only "approved" questions are used in student-facing tests

[5] TEST CREATION & LAUNCH
    ├── Faculty creates Test record → selects approved questions, sets duration
    ├── Students take the test via /quiz or /descriptive-test routes
    └── Faculty views per-test analytics via /faculty/reports/:testId
         └── Aggregated score distribution, class averages, per-student breakdown

[6] STUDENT MONITORING
    └── Faculty dashboard shows all enrolled students:
         ├── Progress % (completed modules / total modules from Neo4j)
         ├── Last score and last attempt date (from MongoDB submissions)
         └── Active / Pending status
```

---

### 3c. Admin Journey

```
[1] Subject catalog management → add/edit subjects
[2] View all faculty subject access requests (all statuses)
[3] Approve or reject requests → triggers Faculty workflow step 3
[4] User management (viewing all roles)
```

---

## 4. How the AI/ML Models Integrate with the Rest of the System

This is the core of GraphEdu. Below is the **exact data flow** showing how each model plugs into the system.

---

### 4a. GCN + BNN — Student Failure Prediction Pipeline

```
Neo4j Graph Database
  │
  │  (1) extract_graph_to_matrix.js runs once (or on graph update)
  │  Cypher: MATCH (t:Topic) RETURN t.topicId, t.name, t.type
  │          MATCH (a)-[:PRECEDES]->(b) RETURN a.topicId, b.topicId
  │
  ▼
backend/ml_data/
  ├── nodes.json         ← [{index, id, name, type}, ...]
  ├── edge_index.json    ← [[source_indices], [target_indices]]  (COO format)
  └── node_features.json ← [[type_onehot..., complexity_float], ...]

  │
  │  (2) FastAPI ML Backend loads these on startup (static, in memory)
  │      base_x = torch.tensor(node_features)
  │      edge_index = torch.tensor(edge_index_data)
  │
  ▼
POST /predict  ← called by frontend (or faculty dashboard)
  { student_id: "...", topic_scores: { "ds-arrays": 0.8, "ds-trees": 0.3 } }

  │
  │  (3) Inject student scores as an extra feature column
  │      student_x = torch.cat([base_x, score_column], dim=1)
  │
  ▼
GraphEDU_GCN (2-layer GCN):
  Layer 1: GCNConv → aggregates each node's features with its neighbours
  Layer 2: GCNConv → second-order neighbourhood aggregation
  Output:  Sigmoid → probability of mastery per node ∈ [0, 1]

  │
  │  (4) MC Dropout: run 20 forward passes with dropout active
  │      mean_preds = average of 20 predictions (actual estimate)
  │      var_preds  = variance of 20 predictions (uncertainty)
  │
  ▼
Response to frontend:
  [
    { topicId: "ds-trees", probability_of_failure: 0.72, uncertainty: 0.08,
      flagged_for_intervention: true },
    { topicId: "ds-arrays", probability_of_failure: 0.21, uncertainty: 0.15,
      flagged_for_intervention: false },
    ...
  ]  (sorted by highest failure risk)

  │
  │  (5) Frontend uses this to:
  │      - Highlight at-risk nodes on the knowledge graph (red glow)
  │      - Show intervention banner on student dashboard
  │      - Feed into the RAG pipeline for remedial content
```

---

### 4b. RAG Pipeline — Remedial Content Generation

```
Student clicks a weak/highlighted node on the Knowledge Graph
  │
  │  Frontend sends:
  ▼
POST http://localhost:8001/generate-remedial-content
  { topic_name: "Binary Search Tree" }

  │
  ▼
rag/vector_store.py — FAISS Retrieval:
  (1) Load FAISS DB from disk (or build it from textbook .md file if first run)
  (2) Embed query: "Binary Search Tree" → 384-dim vector via all-MiniLM-L6-v2
  (3) Cosine similarity search → retrieve top-2 most relevant textbook chunks
      e.g. "Chapter 4.2: BST Insert Operation..." and "Chapter 4.3: BST Traversal..."

  │
  ▼
rag/generator.py — LangChain LCEL Chain:
  (1) Retriever fetches 2 chunks → format_docs() joins them as plain text
  (2) PromptTemplate fills in:
       - {context} = the 2 textbook paragraphs
       - {topic}   = "Binary Search Tree"
  (3) Prompt sent to Ollama (LLaMA 3, temperature=0.3)
  (4) LLM constrained to:
       - Max 3 sentences explaining the core concept
       - 2 sentences on why it's important
       - STRICTLY use only provided context — no invented facts
  (5) StrOutputParser → plain string

  │
  ▼
Response:
  { topic: "Binary Search Tree",
    remedial_plan: "A Binary Search Tree is a hierarchical structure where
    each node's left child is smaller and right child is larger than itself.
    BST enables O(log n) average case search, insert, and delete operations.
    The in-order traversal of a BST yields elements in sorted order. ..." }

  │
  ▼
Frontend (Expand.jsx):
  Displays in side panel under "AI Remedial Tutorial" section (scrollable box)
  Panel is color-coded red to signal it's a weakness area
```

---

### 4c. Adaptive BTL Engine — Quiz Loop

```
Student opens Quiz for "Trees" module
  │
  ▼
Quiz.jsx — Initialization:
  (1) Find the module in dsModules (static + dynamic merged)
  (2) Extract prerequisite topic IDs for that module
  (3) Filter questionPool to only those topic IDs
  (4) Start with first BTL Level 1 question

  │
  ▼
For each question answered:
  (1) Record answer in resultsMap (React state, keyed by question ID)
  (2) Update streak counters:
       correct streak++  (if correct) OR  incorrect streak++ (if wrong)
  (3) Apply BTL state machine:
       ├── correctStreak >= 2 → currentBTL = min(4, currentBTL + 1) [LEVEL UP]
       └── incorrectStreak >= 1 → currentBTL = max(1, currentBTL - 1) [LEVEL DOWN]
  (4) If level changed → show animated modal ("Level UP!" / "Level Adjustment")
  (5) Select next question:
       ├── Priority: unanswered "Marked for Review" questions at current BTL
       └── Fallback: any unasked question at current BTL from filtered pool

  │
  ▼
On Submit (after 20 questions or timer expires):
  (1) Calculate score + identify weakTopicIds (topics with any incorrect answer)
  (2) Build AI plan (prerequisite recommendations from dsModules graph traversal)
  (3) POST /api/submissions → save full submission record to MongoDB
  (4) Navigate to /result page with { results, total, weakTopicIds }

  │
  ▼
Result Page:
  (1) Display score circle (SVG with strokeDasharray = scorePercentage)
  (2) Run recommendation algorithm:
       weakTopicIds.forEach → search each dsModule's prerequisites → collect matching
  (3) Show Knowledge Roadmap (prerequisite-based study path)
  (4) "Get In-Depth Analysis" → navigate to /expand?view=galaxy&weak=p1,p2,...

  │
  ▼
Expand.jsx (Knowledge Graph):
  (1) Parse ?weak= URL params → setHighlightedNodeIds
  (2) Switch to Galaxy view (all modules + all prereqs connected)
  (3) Render weak nodes as RED with animated glow halo
  (4) On click of weak node → trigger RAG fetch (pipeline 4b above)
  (5) Display personalized tutorial in sliding info panel
```

---

### 4d. AI Curriculum Graph Generation — Faculty Workflow

```
Faculty enters 6 module titles in Faculty Dashboard form
  │
  ▼
POST /api/syllabus/generate-graph
  { subject: "Data Structures", modules: ["Arrays", "Linked Lists", ...] }

  │
  ▼
graphGeneratorService.js — Google Gemini 2.5 Flash:
  Prompt: "You are an expert curriculum designer.
           For each of 6 modules, identify 3-5 prerequisite concepts.
           Return ONLY valid JSON (no markdown)."

  Gemini returns:
  [
    { id: "m1", title: "Arrays", longDescription: "...", detail: "...",
      why: "...", color: "#ff0055",
      prerequisites: [
        { id: "p1", title: "Memory Allocation", description: "...",
          reason: "Arrays are contiguous memory blocks..." },
        ...
      ]
    },
    ...
  ]

  │
  ▼
dynamicSeeder.js — Neo4j Seeding:
  For each module:
    MERGE (:Topic {topicId: m.id, subjectId: ...}) SET properties...
  For each prerequisite:
    MERGE (:Topic {topicId: p.id, subjectId: ...}) SET properties...
    MATCH (p:Topic), (m:Topic) MERGE (p)-[:PRECEDES]->(m)

  │
  ▼
SubjectGraph saved to MongoDB (generatedGraphJSON = the Gemini output)

  │
  ▼
Student opens /expand → fetches from /api/syllabus/graph-data
  → Loads the Neo4j graph → dynamicModules state
  → Force graph renders the curriculum as an interactive canvas
```

---

### 4e. AI Question Bank — Faculty Workflow

```
Faculty clicks "Generate 40 Questions" for chapter "Trees"
  │
  ▼
POST /api/ai/generate-bank
  { subject: "Data Structures", chapter: "Trees" }

  │
  ▼
aiQuestionController.js — Google Gemini 2.5 Flash:
  Prompt: "Generate 40 MCQ. First 20: BTL3 (Application). Next 20: BTL4 (Analysis).
           Return strictly valid JSON array."

  Gemini returns: [...40 question objects...]

  │
  ▼
AIGeneratedQuestion.insertMany(questions) → stored with status: "pending"

  │
  ▼
Faculty Reviews on Dashboard:
  ├── Sees each question with BTL level badge
  ├── Clicks ✅ Approve → PATCH /api/ai/questions/:id { status: "approved" }
  └── Clicks ❌ Reject  → PATCH /api/ai/questions/:id { status: "rejected" }

  │
  ▼
Test Creation → only "approved" questions appear in student-facing tests
  (GET /api/ai/questions?chapter=Trees&status=approved)

  │
  ▼
Student takes Descriptive/Coding test → AI question served → result saved
  → Faculty views aggregate analytics via /api/reports/:testId
```

---

## 5. Data Flow Summary Diagram

```
                         ┌──────────────────────────────┐
                         │        STUDENT ACTION        │
                         └──────────────┬───────────────┘
                                        │
          ┌─────────────────────────────▼────────────────────────────┐
          │                  REACT FRONTEND (Vite/5173)              │
          │  Quiz Engine → Result → Knowledge Graph → My Tests       │
          └──────┬────────────────────────────────────┬──────────────┘
                 │ REST (Axios)                        │ REST (fetch)
    ┌────────────▼──────────────────┐    ┌────────────▼──────────────┐
    │  Node.js/Express (5001)       │    │  FastAPI ML Backend (8001) │
    │  ┌─────────────────────────┐  │    │  ┌──────────────────────┐  │
    │  │ MongoDB (questions,     │  │    │  │ GCN + MC Dropout BNN │  │
    │  │ progress, submissions,  │  │    │  │ → failure prediction  │  │
    │  │ users, AI plans)        │  │    │  └──────────────────────┘  │
    │  └─────────────────────────┘  │    │  ┌──────────────────────┐  │
    │  ┌─────────────────────────┐  │    │  │ RAG Pipeline         │  │
    │  │ Neo4j (curriculum graph │  │    │  │ FAISS + MiniLM +     │  │
    │  │ :Topic nodes,          │  │    │  │ LLaMA3 via Ollama    │  │
    │  │ :PRECEDES edges)        │  │    │  └──────────────────────┘  │
    │  └─────────────────────────┘  │    └───────────────────────────┘
    │  ┌─────────────────────────┐  │
    │  │ Gemini 2.5 Flash API    │  │
    │  │ → Curriculum JSON       │  │
    │  │ → 40-Q Bank Generation  │  │
    │  └─────────────────────────┘  │
    │  ┌─────────────────────────┐  │
    │  │ Ollama (LLaMA3) Local   │  │
    │  │ → Adaptive Questions    │  │
    │  └─────────────────────────┘  │
    └───────────────────────────────┘
```

---

## 6. Authentication & Role System

```
┌─────────────────────────────────────────────┐
│  Login Methods                              │
│  ├── Email + Password → JWT token → MongoDB │
│  └── Google OAuth → Firebase → MongoDB sync │
│       (graphId auto-generated on first login)│
└────────────────────┬────────────────────────┘
                     │ role field on User document
          ┌──────────┼──────────┐
          ▼          ▼          ▼
       student    faculty     admin
          │          │          │
     /dashboard  /faculty/  /admin
                dashboard
```

**ProtectedRoute component** reads `role` from `localStorage.user` and redirects unauthorized access.

---

## 7. Deployment Notes

- **Frontend** deployed to **Netlify** (`grphedu.netlify.app`)
- **Backend** deployed to **Render** (`edugraph-mini-project-ty.onrender.com`)
- **ML Backend (FastAPI + Ollama)** runs **locally only** (too heavy for free-tier cloud)
- **Neo4j** runs locally (Neo4j Desktop or a self-hosted instance)
- `start_ecosystem.js` orchestrates the entire local environment in one terminal window

---

## 8. Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **GCN over a simple regression** | The curriculum is a graph — topic mastery depends on prerequisite mastery. A GCN naturally captures this dependency via neighbourhood aggregation. |
| **MC Dropout over deterministic NN** | Provides uncertainty quantification. The system avoids flagging students when the model is itself unsure, preventing false intervention alarms. |
| **FAISS + local LLM for RAG** | Zero API cost for remedial plans, no student data sent to cloud, textbook-grounded answers prevent hallucination. |
| **Gemini for batch generation** | Local LLaMA 3 is too slow for 40-question batch generation. Gemini handles it in ~2 seconds. |
| **Neo4j for curriculum** | Cypher queries naturally express prerequisite chains. Adding a new prerequisite relationship is a single `MERGE (a)-[:PRECEDES]->(b)` — no schema change needed. |
| **Bloom's Taxonomy as difficulty axis** | Universally accepted pedagogical framework. Faculty already design syllabi around it. Maps cleanly to MCQ/Descriptive/Coding test types. |
| **React Force Graph (D3)** | The only approach that produces a visually intuitive, explorable representation of the prerequisite web. Static diagrams don't convey the interconnectedness of concepts. |
