# GraphEdu — All Mathematical Models, AI Tools & Related Aspects

## System Architecture Overview

GraphEdu is a three-tier intelligent educational platform:

```
┌──────────────────────────────────────────────────────────────────┐
│  React Frontend (Vite + Tailwind)                                │
│  Knowledge Graph Canvas · Quiz Engine · Faculty Dashboard        │
└────────────────┬─────────────────────────────────────────────────┘
                 │ REST API
┌────────────────▼─────────────────────────────────────────────────┐
│  Node.js / Express Backend  (port 5001)                          │
│  MongoDB (users, tests, progress)  ·  Neo4j (curriculum graph)   │
└────────────────┬─────────────────────────────────────────────────┘
                 │ REST API
┌────────────────▼─────────────────────────────────────────────────┐
│  Python FastAPI ML Backend  (port 8001)                          │
│  GCN · Bayesian Neural Network · RAG Pipeline                    │
└──────────────────────────────────────────────────────────────────┘
```

---

## 1. Graph Convolutional Network (GCN)

**File:** [`ml_backend/model/gcn.py`](file:///Users/karthiks/Desktop/Mini%20Project%20/ml_backend/model/gcn.py)

### What it is
A **Graph Convolutional Network (GCN)** is a neural network architecture that operates directly on graph-structured data. Unlike standard neural networks that work on flat vectors, a GCN leverages the *topology* of a graph — its nodes and edges — to learn representations that capture neighbourhood relationships.

### Mathematical Foundation

The core GCN operation (Kipf & Welling, 2016) for a single layer is:

```
H⁽ˡ⁺¹⁾ = σ( D̃⁻¹/² Ã D̃⁻¹/² H⁽ˡ⁾ W⁽ˡ⁾ )
```

Where:
- `Ã = A + I` — Adjacency matrix with self-loops added
- `D̃` — Diagonal degree matrix of `Ã`
- `H⁽ˡ⁾` — Feature matrix at layer `l` (nodes × features)
- `W⁽ˡ⁾` — Learnable weight matrix at layer `l`
- `σ` — Activation function (ReLU in this project)

**Intuition:** Each node's new representation is computed as a *weighted average* of its own features and its neighbours' features, then passed through a linear transformation. This lets the network propagate information across the graph topology.

### Project-Specific Architecture (`GraphEDU_GCN`)

```python
Layer 1:  GCNConv(num_features → 16)  →  ReLU  →  Dropout(0.5)
Layer 2:  GCNConv(16 → 16)            →  ReLU  →  Dropout(0.5)
Output:   Linear(16 → 1)              →  Sigmoid
```

| Component | Role |
|-----------|------|
| **Input nodes** | Topics/prerequisites from Neo4j knowledge graph |
| **Input features** | One-hot encoded node type + randomized complexity score + student score overlay |
| **Edge index** | `PRECEDES` relationships from Neo4j, in PyTorch Geometric COO format |
| **Output** | Per-node sigmoid score ∈ [0, 1] = **probability of mastery** |

### Input Feature Construction
The `extract_graph_to_matrix.js` script exports three JSON files from Neo4j:

1. **`nodes.json`** — node IDs, names, and types
2. **`edge_index.json`** — COO format `[[source_nodes], [target_nodes]]` for PyG
3. **`node_features.json`** — one-hot encoded type vector + random complexity float

At inference time, the student's quiz scores are appended as an extra feature column:

```python
student_x = torch.cat([base_x, score_feature], dim=1)
```

This allows the GCN to condition its mastery predictions on real student performance.

### Why a GCN (not just a normal NN)?
The curriculum is inherently a **Directed Acyclic Graph** (DAG). "Arrays" is a prerequisite for "Linked Lists" which is a prerequisite for "Trees." A GCN captures these prerequisite relationships naturally — predicting failure in "Trees" implicitly considers the student's standing on "Linked Lists."

---

## 2. Bayesian Neural Network via Monte Carlo Dropout

**File:** [`ml_backend/model/bayesian.py`](file:///Users/karthiks/Desktop/Mini%20Project%20/ml_backend/model/bayesian.py)

### What it is
A **Bayesian Neural Network (BNN)** treats model weights as probability distributions rather than fixed values. This produces *uncertainty estimates* alongside predictions — the model doesn't just say "this student will fail Trees," it says "this student will fail Trees *with 85% confidence and low uncertainty.*"

### Monte Carlo Dropout (Gal & Ghahramani, 2016)
Training a true BNN is computationally expensive. The MC Dropout trick approximates Bayesian inference at essentially zero extra cost:

> **Key Insight:** Dropout during *training* is equivalent to approximate variational inference in a Gaussian process. Therefore, running dropout at **inference time** (keeping `model.train()` active) and sampling many forward passes produces an approximate *posterior distribution* over predictions.

```python
model.train()  # Force dropout active during inference!
predictions = []
for _ in range(20):          # T = 20 stochastic forward passes
    out = model(x, edge_index)
    predictions.append(out)

stacked = torch.cat(predictions, dim=0)  # Shape: [20, num_nodes, 1]
mean_preds = stacked.mean(dim=0)         # Posterior mean → actual prediction
var_preds  = stacked.var(dim=0)          # Posterior variance → uncertainty
```

### Mathematical Interpretation

| Quantity | Formula | Meaning |
|----------|---------|---------|
| **Predictive Mean** | `μ = (1/T) Σ f(x, ωₜ)` | Best estimate of mastery probability |
| **Predictive Variance** | `σ² = (1/T) Σ (f(x,ωₜ) - μ)²` | Uncertainty / confidence in the prediction |
| **Prob. of Failure** | `1 - μ` | Risk score for intervention |

Where `ωₜ` is the random weight mask applied by dropout in pass `t`.

### Uncertainty Types Captured
- **Aleatoric uncertainty** — inherent noise in the data (some students are inconsistent)
- **Epistemic uncertainty** — model's lack of knowledge (areas with sparse training data)

### Intervention Flagging Logic (in `main.py`)
```python
"flagged_for_intervention": prob_failure > 0.6 and uncertainty < 0.2
```
This dual condition means: *"Flag this student only if the model is **both confident** (low variance) **and** predicts they will fail."* If the model is uncertain, it conservatively avoids false alarms.

---

## 3. RAG Pipeline (Retrieval-Augmented Generation)

**Files:**
- [`ml_backend/rag/vector_store.py`](file:///Users/karthiks/Desktop/Mini%20Project%20/ml_backend/rag/vector_store.py)
- [`ml_backend/rag/generator.py`](file:///Users/karthiks/Desktop/Mini%20Project%20/ml_backend/rag/generator.py)

### What it is
**Retrieval-Augmented Generation (RAG)** is a technique that grounds LLM outputs in factual, domain-specific knowledge by:
1. Encoding a knowledge base into a vector database
2. At query time, *retrieving* the most semantically relevant passages
3. Injecting them as context into the LLM prompt

This prevents LLM hallucination and constrains the AI tutor to textbook-accurate material.

### Step-by-Step RAG Pipeline

```
"Student is weak at: Linked Lists"
          │
          ▼
┌─────────────────────────────┐
│  1. FAISS Vector DB Lookup  │   ← Sentence embedding similarity search
│  all-MiniLM-L6-v2 model    │
│  Retrieve top-k=2 chunks    │
└──────────────┬──────────────┘
               │ retrieved textbook passages
               ▼
┌─────────────────────────────┐
│  2. Prompt Assembly         │   ← LangChain PromptTemplate
│  context + topic + rules    │
└──────────────┬──────────────┘
               │ constructed prompt
               ▼
┌─────────────────────────────┐
│  3. LLM Generation          │   ← Ollama (llama3, temp=0.3)
│  Max 3 concept sentences    │
│  + 2 importance sentences   │
└──────────────┬──────────────┘
               │ remedial_plan string
               ▼
        Frontend Info Panel
```

### 3a. Vector Store — FAISS + Sentence Transformers

**Embedding model:** `all-MiniLM-L6-v2` (HuggingFace)
- A 22M parameter sentence transformer producing **384-dimensional dense vectors**
- Optimized for semantic similarity search; trained on 1B+ sentence pairs

**FAISS (Facebook AI Similarity Search):**
- Stores all textbook chunk embeddings in an **Approximate Nearest Neighbour (ANN) index**
- Uses **L2 distance** (Euclidean) to find the most semantically similar chunks to the query
- Persisted to disk (`faiss_db/`) so embeddings are only computed once

**Text Splitting Strategy:**
```python
# Stage 1: Semantic split by Markdown headers (preserve chapter context)
MarkdownHeaderTextSplitter(headers=["#", "##"])

# Stage 2: Fine-grained chunk split
RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
```
The two-stage split ensures chunks are both semantically coherent (same heading context) and small enough to be informative individually.

### 3b. Generator — LangChain + Ollama (LLaMA 3)

**LangChain LCEL Chain:**
```python
rag_chain = (
    {"context": retriever | format_docs, "topic": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)
```

- `temperature=0.3` — Low temperature for factual, grounded output (avoids creative hallucinations)
- The prompt explicitly forbids inventing facts: *"Do NOT invent facts. Only use the provided context."*
- Outputs are consumed by the frontend's AI Remedial Tutorial panel on the Knowledge Graph page

---

## 4. Adaptive Testing Engine — Bloom's Taxonomy (BTL)

**File:** [`backend/services/aiQuestionService.js`](file:///Users/karthiks/Desktop/Mini%20Project%20/backend/services/aiQuestionService.js)

### What it is
The adaptive testing engine implements a simplified **Item Response Theory (IRT)** / **Zone of Proximal Development (ZPD)** framework, operationalized using **Bloom's Taxonomy Levels (BTL)** as the difficulty axis.

### Bloom's Taxonomy Levels Used

| BTL Level | Cognitive Domain | Question Type | Example |
|-----------|-----------------|---------------|---------|
| **1** | Remember | Define / Recall | "What is a stack?" |
| **2** | Understand | Explain / Describe | "Explain how LIFO works." |
| **3** | Apply | Solve / Implement | "Write push() for a stack." |
| **4** | Analyze | Evaluate / Compare | "Compare DFS vs BFS for shortest path." |

### Adaptive BTL State Machine

```
Current BTL ──── Answer Correct + consecutiveCorrect ≥ 1? ──▶ BTL = min(4, BTL+1)
     │
     └──── Answer Wrong? ──────────────────────────────────▶ BTL = max(1, BTL-1)
```

```javascript
export const calculateNextBTL = (currentBTL, isCorrect, consecutiveCorrectCount) => {
  if (isCorrect && consecutiveCorrectCount >= 1) {
    return Math.min(4, currentBTL + 1);  // Level UP
  } else if (!isCorrect) {
    return Math.max(1, currentBTL - 1);  // Level DOWN
  }
  return currentBTL;  // Hold
};
```

**Interpretation:**
- A student must answer **2 consecutive questions correctly** before advancing to the next difficulty level (prevents lucky guesses from over-promoting)
- A **single wrong answer** immediately drops the difficulty (to prevent frustration and ensure remediation)
- BTL is clamped to [1, 4] using `Math.min` / `Math.max`

### Persistent State
The `StudentChapterProgress` MongoDB model stores:
```json
{
  "currentBTLLevel": 2,
  "totalTestsAttempted": 7,
  "averageScore": 71.4,
  "chapter": "Stacks & Queues"
}
```

The **running average score** is computed using an **incremental mean formula**:
```
newAvg = (oldAvg × oldCount + newScore) / newCount
```
This avoids storing all historical scores while maintaining a mathematically exact cumulative average.

---

## 5. LLM Integration — Ollama / LLaMA 3 (Local)

**Used in:** Adaptive question generation, RAG remedial plans

### What it is
**LLaMA 3** (Meta AI) is a state-of-the-art open-weight Large Language Model. Running via **Ollama** on `localhost:11434`, it processes the entire inference locally — zero API costs, zero data leakage.

### Question Generation Prompt Engineering

The system uses a structured **zero-shot Chain-of-Constraint** prompt:
- Chapter isolation rules ("If chapter = Trees, do NOT generate Graph questions")
- Strict JSON-only output format (`format: "json"` in API call)
- BTL-level aware question targeting
- Support for 3 question types: **MCQ** (5 marks), **Descriptive** (10 marks), **Coding** (20 marks)

### Temperature Semantics
| Context | Temperature | Effect |
|---------|-------------|--------|
| Adaptive questions | default | Varied, creative questions |
| RAG remedial plan | `0.3` | Factual, constrained, grounded |

---

## 6. LLM Integration — Google Gemini 2.5 Flash (Cloud)

**Files:**
- [`backend/services/graphGeneratorService.js`](file:///Users/karthiks/Desktop/Mini%20Project%20/backend/services/graphGeneratorService.js)
- [`backend/controllers/aiQuestionController.js`](file:///Users/karthiks/Desktop/Mini%20Project%20/backend/controllers/aiQuestionController.js)

### What it is
**Gemini 2.5 Flash** (Google DeepMind) is used for two **heavy batch generation tasks** that would be too slow or too large for local LLaMA 3:

### Task 1: Knowledge Graph Generation (`graphGeneratorService.js`)
Given 6 syllabus module names, Gemini generates a complete **structured curriculum JSON**:
- Module descriptions, `longDescription`, `detail`, `why` fields
- 3–5 prerequisite concepts per module
- Each prerequisite has a `reason` field explaining *why* it's a prerequisite
- Unique hex colors per module for visual distinction

This output is directly seeded into **Neo4j** via the `dynamicSeeder.js` service.

### Task 2: 40-Question Bank (`facultyGenerateBank`)
Generates exactly **40 MCQ questions** in a single call:
- 20 questions at **BTL 3 (Application)**
- 20 questions at **BTL 4 (Analysis)**
- Structured JSON array returned and bulk-inserted into MongoDB

**Why Gemini and not LLaMA 3 for this?**
> "This takes 0 RAM/CPU compared to local Ollama and finishes in ~2 seconds." (comment in `graphGeneratorService.js`)
> Gemini excels at large structured JSON generation tasks where format adherence is critical.

---

## 7. Knowledge Graph — Neo4j (Graph Database)

### What it is
**Neo4j** is a native **property graph database** that stores data as nodes and relationships rather than tables. The entire curriculum is stored as a labelled property graph.

### Graph Schema

```
(:Topic {type: "module"})  ──[:PRECEDES]──▶  (:Topic {type: "module"})
       ▲
       │ [:PRECEDES]
       │
(:Topic {type: "prerequisite"})
```

**Node properties:**
- `topicId`, `subjectId`, `name`, `type`, `longDescription`, `detail`, `why`, `color`, `reason`

**Relationship:** `PRECEDES` — directional edge indicating "this concept must be learned before that concept"

### Cypher Query Pattern (used in `dynamicSeeder.js`)
```cypher
MATCH (m:Topic {type: 'module', subjectId: $subjectId})
OPTIONAL MATCH (p:Topic {type: 'prerequisite', subjectId: $subjectId})-[:PRECEDES]->(m)
RETURN m, collect(p) as prerequisites
ORDER BY m.name ASC
```

### Graph-to-Matrix Extraction Pipeline
The `extract_graph_to_matrix.js` script bridges **Neo4j → PyTorch Geometric**:

1. Fetches all `:Topic` nodes → `nodes.json`
2. Fetches all `[:PRECEDES]` relationships → `edge_index.json` (COO sparse format)
3. Constructs **one-hot encoded feature vectors** for node types → `node_features.json`

**One-Hot Encoding:**
```javascript
const uniqueTypes = [...new Set(nodes.map(n => n.type))];  // e.g. ['module', 'prerequisite']
const featureVector = Array(uniqueTypes.length).fill(0);
featureVector[uniqueTypes.indexOf(node.type)] = 1.0;
featureVector.push(Math.random());  // Dummy complexity feature
```

---

## 8. Force-Directed Graph Visualization (D3 / react-force-graph-2d)

**File:** [`frontend/src/pages/Expand.jsx`](file:///Users/karthiks/Desktop/Mini%20Project%20/frontend/src/pages/Expand.jsx)

### What it is
The curriculum knowledge graph is visualized using **`react-force-graph-2d`**, which wraps D3.js's **force simulation** algorithm.

### Force Simulation Physics

The graph layout is computed by **simulating physical forces** on nodes:

| Force | Configuration | Effect |
|-------|---------------|--------|
| **Charge (repulsion)** | `strength(-400)` | Nodes repel each other — prevents overlap |
| **Link (spring)** | `backbone: 250, prereq: 120` | Edges act as springs — pull connected nodes together |
| **Alpha Decay** | `0.02` (slow) | Simulation cools slowly → more stable final layout |
| **Velocity Decay** | `0.3` | Damping coefficient — prevents oscillation |

The simulation converges to a **minimum energy layout** (like a physical spring-mass system relaxing to equilibrium). The mathematical model is:

```
Position update: x(t+1) = x(t) + v(t)·dt
Velocity update: v(t+1) = v(t)·(1 - velocityDecay) + Σ forces / mass
Alpha (heat):    α(t+1) = α(t)·(1 - alphaDecay)
```

### Two View Modes

| Mode | Description | Graph Topology |
|------|-------------|----------------|
| **Focused** | Shows one module + its prerequisites | Star topology |
| **Galaxy** | Shows ALL modules + ALL prerequisites interconnected | Full curriculum web |

### Weak Node Highlighting Algorithm
After a quiz, weak topic IDs are passed via URL parameters (`?weak=p1,p2,...`). The renderer applies:
- Red fill + red text for weak nodes
- `rgba(239, 68, 68, 0.4)` red halo
- Auto-triggers RAG content fetch from the Python backend for each weak node

### Backbone Particle Animation
A custom particle travels sequentially along module-to-module "backbone" links:

```javascript
const CYCLE_DURATION = 8000;  // 8 seconds total traversal
const progressTotal = (Date.now() % CYCLE_DURATION) / CYCLE_DURATION;
const activeLinkIndex = Math.floor(progressTotal * totalBackboneLinks);
const linkProgress = (progressTotal * totalBackboneLinks) - activeLinkIndex;
// Interpolate position along the active link
const px = start.x + (end.x - start.x) * linkProgress;
const py = start.y + (end.y - start.y) * linkProgress;
```

This is essentially **parametric linear interpolation** along each edge segment, creating a seamless traversal animation.

---

## 9. Weak Area Detection & Prerequisite Recommendation System

**File:** [`frontend/src/pages/Result.jsx`](file:///Users/karthiks/Desktop/Mini%20Project%20/frontend/src/pages/Result.jsx)

### Algorithm
After a quiz, `weakTopicIds` are passed from the quiz engine to the Result page. The recommendation engine:

1. Iterates over all `dsModules` (curriculum graph)
2. For each weak topic ID, finds which module's prerequisite list contains it
3. Surfaces that prerequisite with its `parentModule` context, `why` explanation, and a reference link

```javascript
const recommendations = useMemo(() => {
  const recs = [];
  weakTopicIds.forEach(id => {
    dsModules.forEach(module => {
      const prereq = module.prerequisites?.find(p => p.id === id);
      if (prereq) recs.push({ ...prereq, parentModule: module.title });
    });
  });
  return Array.from(new Map(recs.map(p => [p.id, p])).values()); // Deduplicate
}, [weakTopicIds]);
```

**Deduplication** uses a `Map` keyed on prerequisite ID — a common set-deduplication pattern that preserves insertion order and runs in O(n).

---

## 10. Firebase Authentication Integration

**File:** [`frontend/src/firebase.js`](file:///Users/karthiks/Desktop/Mini%20Project%20/frontend/src/firebase.js)

- **Google Sign-In OAuth 2.0** via Firebase Auth SDK
- Custom **Graph ID** generation: first 4 letters of name + 4 random digits (e.g., `kart2849`)
- MongoDB user record is created/synced on first login

---

## 11. LangChain Orchestration

**Used in:** `rag/generator.py`

LangChain's **LCEL (LangChain Expression Language)** is the pipeline orchestration framework:

| Component | LangChain Class | Role |
|-----------|----------------|------|
| Vector retriever | `FAISS.as_retriever()` | Top-k semantic lookup |
| Prompt builder | `PromptTemplate.from_template()` | Structured prompt assembly |
| LLM connector | `OllamaLLM(model="llama3")` | Local LLM interface |
| Output parser | `StrOutputParser()` | Converts LLM response to plain string |
| Pipeline glue | `RunnablePassthrough()` | Passes topic name unchanged |

The `|` pipe operator chains these into a **declarative data-flow graph**, making the RAG pipeline readable, composable, and easy to swap components.

---

## Complete AI / ML Tool Inventory

| Tool / Model | Type | Where Used | Purpose |
|---|---|---|---|
| **GCN** (`torch_geometric`) | Graph Neural Network | `ml_backend/model/gcn.py` | Predict per-topic mastery probability |
| **MC Dropout BNN** | Bayesian approximation | `ml_backend/model/bayesian.py` | Uncertainty quantification on GCN predictions |
| **FAISS** | ANN Vector Index | `ml_backend/rag/vector_store.py` | Textbook semantic search |
| **all-MiniLM-L6-v2** | Sentence Transformer | `ml_backend/rag/vector_store.py` | Text → 384-dim embedding |
| **LLaMA 3 (Ollama)** | LLM (local) | `rag/generator.py`, `aiQuestionService.js` | RAG generation + adaptive question generation |
| **Gemini 2.5 Flash** | LLM (cloud) | `graphGeneratorService.js`, `aiQuestionController.js` | Curriculum graph generation + 40-question bank |
| **LangChain LCEL** | Orchestration framework | `rag/generator.py` | RAG pipeline assembly |
| **Neo4j** | Graph Database | `dynamicSeeder.js`, `extract_graph_to_matrix.js` | Curriculum knowledge graph storage |
| **Bloom's Taxonomy BTL** | Adaptive algorithm | `aiQuestionService.js`, `studentTestController.js` | Adaptive difficulty state machine |
| **D3 Force Simulation** | Physics-based layout | `Expand.jsx` (react-force-graph-2d) | Knowledge graph visualization |
| **Firebase Auth** | Authentication | `firebase.js` | Google OAuth + Graph ID system |
| **FastAPI** | ML API server | `ml_backend/main.py` | REST endpoints for GCN + RAG inference |
| **PyTorch Geometric** | GNN framework | `gcn.py` | GCN layer implementation (`GCNConv`) |
| **MongoDB** | Document DB | Backend models | Students, tests, progress, AI plans |
