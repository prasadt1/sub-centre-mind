# Diagram Prompts for Nano Banan / AI Diagram Tools

Use these prompts with Nano Banan, Excalidraw AI, or similar diagram generation tools.

---

## Diagram 1: System Architecture Overview

**Filename**: `system-architecture.png`

**Prompt**:
```
Create a clean, modern system architecture diagram for "Sub-Centre Mind" healthcare decision support system.

Components (top to bottom):

1. TOP LAYER: "ANM (User)" 
   - Icon: User with medical cross
   - Label: "WhatsApp / CLI Interface"

2. SECOND LAYER: "Query Router"
   - Shape: Decision diamond
   - Label: "boundary_card.json"
   - Two output arrows

3. THIRD LAYER (Split):
   LEFT PATH: "RAG Pipeline" box containing:
     • Intent Detection (IFA vs Calcium)
     • FAISS Retrieval (1790 chunks)
     • Intent Reranking (1.35× boost)
   
   RIGHT PATH: "Refusal Handler" box containing:
     • Tool Calling (refuse_and_escalate)
     • MO Notification (urgency levels)

4. FOURTH LAYER: "Gemma 4 E4B (Ollama)"
   - Shape: Rounded rectangle
   - Label: "Local Inference | think: false"
   - Icon: Brain or AI chip

5. BOTTOM LAYER: "Nudge Engine"
   - Shape: Rounded rectangle
   - Label: "WhatsApp Closed-Loop"
   - Icon: WhatsApp logo
   - Feedback arrow back to top

Color scheme:
- Blue (#4A90E2): Data flow arrows
- Red (#E74C3C): Refusal path
- Green (#2ECC71): Answer path
- Orange (#F39C12): Nudge loop
- Gray (#95A5A6): Background boxes

Style: Clean, professional, healthcare-appropriate, flat design
Add small latency labels: "2.1s avg" on Gemma box
```

---

## Diagram 2: RAG Pipeline Detailed Flow

**Filename**: `rag-pipeline-flow.png`

**Prompt**:
```
Create a vertical flowchart showing the RAG (Retrieval-Augmented Generation) pipeline.

Steps (top to bottom):

1. START: "Query Input"
   - Shape: Rounded rectangle
   - Examples: "IFA dose?", "गर्भवती महिलाओं के लिए IFA?"
   - Color: Light blue

2. "Intent Detection"
   - Shape: Hexagon
   - Label: "IFA vs Calcium vs Generic"
   - Keywords shown: "आयरन", "कैल्शियम", "iron"
   - Color: Purple

3. "Multilingual Embedding"
   - Shape: Rectangle
   - Label: "paraphrase-multilingual-MiniLM-L12-v2"
   - Sublabel: "384-dimensional vectors"
   - Color: Blue

4. "FAISS Retrieval"
   - Shape: Cylinder (database)
   - Label: "IndexFlatIP | 1790 chunks"
   - Sublabel: "top-48 candidates"
   - Color: Teal

5. "Intent Reranking"
   - Shape: Diamond
   - Label: "Boost relevant chunks"
   - Formula: "score × 1.35 (strong match)"
   - Color: Orange

6. "Top-5 Selection"
   - Shape: Rectangle
   - Label: "Threshold: score >0.7"
   - Example: "[1] WHO p.12 (0.92)"
   - Color: Yellow

7. "Prompt Construction"
   - Shape: Rectangle
   - Label: "Chunks + Safety Rules"
   - Color: Light green

8. "Gemma 4 Generation"
   - Shape: Rounded rectangle
   - Label: "think: false | temp: 0.1"
   - Icon: AI brain
   - Color: Green

9. END: "Answer + Citations"
   - Shape: Rounded rectangle
   - Example: "180 tablets + [1] WHO p.12"
   - Icon: Document with checkmark
   - Color: Dark green

Timing annotations (right side):
- Retrieval: 0.3s
- Reranking: <0.1s
- Generation: 1.8s
- TOTAL: 2.1s

Style: Technical flowchart with gradient colors (blue → green)
Add small icons for each step
Use arrows with labels showing data type (text, vectors, chunks)
```

---

## Diagram 3: Decision Boundary Matrix

**Filename**: `decision-boundary-matrix.png`

**Prompt**:
```
Create a 2x2 matrix diagram visualizing the Decision Boundary Card.

Axes:
- X-axis (horizontal): "Query Complexity" (Low → High)
- Y-axis (vertical): "Clinical Risk" (Low → High)

QUADRANT 1 (Bottom-Left): "Protocol Questions"
- Risk: Low | Complexity: Low
- Background: Light green (#D5F4E6)
- Icon: Book with checkmark
- Examples:
  • "IFA tablet dose?"
  • "ANC visit schedule?"
  • "Immunization day?"
- Action: "✓ Answer with RAG"
- Count: "16 answerable queries"

QUADRANT 2 (Top-Left): "Danger Signs"
- Risk: High | Complexity: Low
- Background: Dark red (#FADBD8)
- Icon: Alert triangle
- Examples:
  • "Heavy bleeding"
  • "Seizures"
  • "Severe pain"
- Action: "✗ Refuse + Escalate (CRITICAL)"
- Response time: "Immediate"

QUADRANT 3 (Bottom-Right): "Edge Cases"
- Risk: Low | Complexity: High
- Background: Light yellow (#FEF9E7)
- Icon: Question mark
- Examples:
  • "Rare protocols"
  • "Unclear guidelines"
  • "Multiple conditions"
- Action: "✗ Refuse + Escalate (MEDIUM)"
- Response time: "24 hours"

QUADRANT 4 (Top-Right): "Diagnostic/Prescriptive"
- Risk: High | Complexity: High
- Background: Red (#F5B7B1)
- Icon: Stethoscope with X
- Examples:
  • "Is 140/90 high BP?"
  • "Insulin dose?"
  • "Lab result interpretation?"
- Action: "✗ Refuse + Escalate (HIGH)"
- Response time: "Same day"

Legend (bottom):
Urgency Levels:
🔴 Critical (immediate)
🟠 High (same day)
🟡 Medium (24 hours)
🟢 Low (routine)

Style: Clean matrix with clear quadrant separation
Use healthcare-appropriate colors
Add icons for each quadrant
Show example queries in each section
```

---

## Diagram 4: Edge Deployment Architecture

**Filename**: `deployment-architecture.png`

**Prompt**:
```
Create a network/infrastructure diagram showing edge deployment architecture.

CENTER: "Sub-Centre" (building icon with medical cross)
Box with dashed border containing:

  1. "Mini-PC / Raspberry Pi 5"
     - Icon: Small server/computer
     - Specs: "8GB RAM | ₹15K"
     - Label: "Gemma 4 E4B (9.6 GB)"
     - Status indicator: Green dot "Running"

  2. "ANM Phone"
     - Icon: Smartphone
     - Label: "WhatsApp Interface"
     - Connection: Solid line to Mini-PC (labeled "Local WiFi")

  3. "Router" (optional)
     - Icon: WiFi router
     - Dashed border (optional component)

  4. "4G Modem" (optional)
     - Icon: Antenna
     - Dashed border (optional component)
     - Label: "Low bandwidth"

BOTTOM: "District Health Office" (building icon)
Box containing:
  - "HMIS Portal" (database icon)
  - "Medical Officer Dashboard" (monitor icon)

CONNECTIONS:
1. Mini-PC ↔ ANM Phone
   - Thick solid line
   - Label: "Primary: Offline inference"
   - Color: Green

2. 4G Modem ↔ District Office
   - Thin dashed line
   - Label: "Optional: Daily HMIS sync"
   - Color: Blue
   - Bandwidth: "~10 MB/day"

3. 4G Modem ↔ WhatsApp Cloud
   - Dotted line
   - Label: "Optional: Nudge messages"
   - Color: Orange
   - Bandwidth: "<1 MB/day"

ANNOTATIONS:
- "Offline-First" badge (green) near Mini-PC
- "PHI Never Leaves Device" badge (blue) near Sub-Centre
- "Optional Connectivity" badge (gray) near 4G Modem

POWER:
- Solar panel icon near Sub-Centre
- Label: "<50W power consumption"

Style: Infrastructure/network diagram
Use isometric or flat icons
Muted professional colors
Show data flow with arrows
Add bandwidth/latency labels
```

---

## Diagram 5: Closed-Loop Nudge State Machine

**Filename**: `nudge-state-machine.png`

**Prompt**:
```
Create a circular state machine diagram for the WhatsApp nudge engine.

STATES (circles arranged in a cycle):

1. "pending_ifa"
   - Color: Light gray (#BDC3C7)
   - Position: Top center
   - Label: "Ready to send"

2. "ifa_sent"
   - Color: Blue (#3498DB)
   - Position: Right
   - Icon: WhatsApp logo
   - Label: "Message sent"
   - Timestamp: "Day 1, 9:00 AM"

3. "ifa_confirmed"
   - Color: Green (#2ECC71)
   - Position: Bottom right
   - Icon: Checkmark
   - Label: "Patient replied 'ली'"

4. "overdue_1"
   - Color: Yellow (#F1C40F)
   - Position: Bottom left
   - Icon: Clock
   - Label: "No reply (3 days)"

5. "overdue_2"
   - Color: Orange (#E67E22)
   - Position: Left
   - Icon: Clock with exclamation
   - Label: "No reply (6 days)"

6. "overdue_3"
   - Color: Red (#E74C3C)
   - Position: Top left
   - Icon: Alert
   - Label: "No reply (9 days)"

7. "escalate_to_anm"
   - Color: Dark red (#C0392B)
   - Position: Outside circle (top)
   - Icon: Medical cross with alert
   - Label: "ANM follow-up required"

TRANSITIONS (arrows with labels):

Happy path (green arrows):
- pending_ifa → ifa_sent: "Send WhatsApp"
- ifa_sent → ifa_confirmed: "Patient replies 'ली'"
- ifa_confirmed → pending_ifa: "Next cycle (24h)"

Overdue path (yellow/orange/red arrows):
- ifa_sent → overdue_1: "No reply (3 days)"
- overdue_1 → overdue_2: "Reminder sent, no reply (3 days)"
- overdue_2 → overdue_3: "Final reminder, no reply (3 days)"
- overdue_3 → escalate_to_anm: "3 missed doses"

Recovery path (dashed green arrows):
- overdue_1 → ifa_confirmed: "Late reply 'ली'"
- overdue_2 → ifa_confirmed: "Late reply 'ली'"

ANNOTATIONS:
- "Confirmation rate: 85%" near ifa_confirmed
- "Escalation rate: 5%" near escalate_to_anm
- "Avg cycle time: 24h" near pending_ifa

MESSAGE EXAMPLES (speech bubbles):
- Near ifa_sent: "नमस्ते! आज का IFA टैबलेट लिया? हाँ के लिए 'ली' भेजें।"
- Near ifa_confirmed: "ली ✓"
- Near overdue_1: "Reminder: IFA टैबलेट लेना न भूलें!"

Style: State machine diagram with circular layout
Color-coded by urgency (green → yellow → orange → red)
Use icons for each state
Show timing on transitions
Add example messages
Professional healthcare colors
```

---

## Diagram 6: Query Flow Comparison (Answer vs Refusal)

**Filename**: `query-flow-comparison.png`

**Prompt**:
```
Create a side-by-side comparison diagram showing two query flows.

LEFT SIDE: "Protocol Query (Answerable)"
Background: Light green (#E8F8F5)

Flow:
1. Input: "IFA tablet dose for pregnant women?"
   - Icon: Speech bubble
   - Color: Blue

2. Query Router: "Matches protocol pattern"
   - Icon: Decision diamond
   - Color: Green

3. RAG Pipeline:
   - Intent: "IFA detected"
   - Retrieval: "5 chunks found"
   - Top score: "0.92"
   - Icon: Database + magnifying glass

4. Gemma 4: "Generate answer"
   - Icon: AI brain
   - Latency: "1.8s"

5. Output: "180 tablets (1 daily for 180 days)"
   - Citations: "[1] WHO p.12 (0.92)"
   - Icon: Document with checkmark
   - Color: Green

Total time: 2.1s

RIGHT SIDE: "Diagnostic Query (Refusal)"
Background: Light red (#FADBD8)

Flow:
1. Input: "Is 140/90 high BP?"
   - Icon: Speech bubble
   - Color: Blue

2. Query Router: "Matches diagnostic pattern"
   - Icon: Decision diamond
   - Color: Red

3. Refusal Handler:
   - Tool: "refuse_and_escalate"
   - Reason: "BP interpretation requires MO"
   - Urgency: "HIGH"
   - Icon: Stop sign

4. Gemma 4: "Generate tool call"
   - Icon: AI brain
   - Latency: "1.5s"

5. Output: "Escalated to Medical Officer"
   - Target: "Dr. Sharma"
   - Urgency: "High (same day)"
   - Icon: Alert with medical cross
   - Color: Red

Total time: 1.8s

COMPARISON METRICS (bottom):
Table showing:
| Metric | Protocol | Diagnostic |
|--------|----------|------------|
| Latency | 2.1s | 1.8s |
| Retrieval | Yes (5 chunks) | No |
| Tool Call | No | Yes (refuse_and_escalate) |
| Safety | Citation required | Escalation required |

Style: Side-by-side comparison with clear visual separation
Use color coding (green vs red)
Show timing at each step
Add icons for each component
Professional healthcare design
```

---

## Diagram 7: Intent Reranking Visualization

**Filename**: `intent-reranking-example.png`

**Prompt**:
```
Create a before/after comparison showing intent reranking in action.

SCENARIO: Query = "IFA tablet dose for pregnant women?"

LEFT SIDE: "Before Reranking (Semantic Only)"
Title: "FAISS Retrieval Results"

Ranked list:
1. Chunk #342 | Score: 0.88
   Source: "MCP-Guide-Book-2018.pdf p.45"
   Text: "Calcium supplementation during pregnancy..."
   Color: Yellow (wrong intent)

2. Chunk #156 | Score: 0.87
   Source: "WHO-Calcium-Supplementation.pdf p.12"
   Text: "Recommended calcium intake..."
   Color: Yellow (wrong intent)

3. Chunk #89 | Score: 0.85
   Source: "WHO-IFA-pregnant-women-2012.pdf p.12"
   Text: "180 IFA tablets (1 daily for 180 days)..."
   Color: Green (correct intent)

4. Chunk #234 | Score: 0.83
   Source: "NHM-SBA-Guidelines.pdf p.67"
   Text: "Nutritional supplementation protocols..."
   Color: Yellow (generic)

5. Chunk #445 | Score: 0.81
   Source: "MCP-Guide-Book-2018.pdf p.89"
   Text: "IFA distribution schedule..."
   Color: Green (correct intent)

RIGHT SIDE: "After Intent Reranking"
Title: "Reranked Results (IFA Intent Detected)"

Ranked list:
1. Chunk #89 | Score: 1.15 (0.85 × 1.35)
   Source: "WHO-IFA-pregnant-women-2012.pdf p.12"
   Text: "180 IFA tablets (1 daily for 180 days)..."
   Color: Dark green (boosted)
   Badge: "Strong IFA match"

2. Chunk #445 | Score: 1.09 (0.81 × 1.35)
   Source: "MCP-Guide-Book-2018.pdf p.89"
   Text: "IFA distribution schedule..."
   Color: Green (boosted)
   Badge: "Strong IFA match"

3. Chunk #342 | Score: 0.88 (unchanged)
   Source: "MCP-Guide-Book-2018.pdf p.45"
   Text: "Calcium supplementation during pregnancy..."
   Color: Gray (demoted)

4. Chunk #156 | Score: 0.87 (unchanged)
   Source: "WHO-Calcium-Supplementation.pdf p.12"
   Text: "Recommended calcium intake..."
   Color: Gray (demoted)

5. Chunk #234 | Score: 0.83 (unchanged)
   Source: "NHM-SBA-Guidelines.pdf p.67"
   Text: "Nutritional supplementation protocols..."
   Color: Gray (demoted)

INTENT DETECTION BOX (top center):
"Query Analysis"
- Keywords found: "IFA", "tablet", "pregnant"
- Hindi keywords: None
- Detected intent: IRON_IFA
- Boost factor: 1.35×

IMPACT METRICS (bottom):
- Relevant chunks in top-3: Before: 1/3 → After: 2/3
- Top result relevance: Before: 0.88 (wrong) → After: 1.15 (correct)
- Answer quality: Improved ✓

Style: Before/after comparison with clear visual distinction
Use color coding (green = relevant, yellow = wrong intent, gray = demoted)
Show score calculations
Add badges for boosted items
Professional technical diagram
```

---

## Usage Instructions

1. **Copy the prompt** for the diagram you want to create
2. **Paste into Nano Banan** or similar AI diagram tool
3. **Adjust colors/style** if needed for your presentation
4. **Export as PNG** at high resolution (2x or 3x)
5. **Save to** `docs/diagrams/` folder in the repository

## Recommended Tools

- **Nano Banan**: https://nanobanan.com/ (AI-powered diagrams)
- **Excalidraw AI**: https://excalidraw.com/ (hand-drawn style)
- **Mermaid Live**: https://mermaid.live/ (code-based diagrams)
- **Whimsical**: https://whimsical.com/ (flowcharts and wireframes)

## File Naming Convention

Save diagrams as:
- `docs/diagrams/01-system-architecture.png`
- `docs/diagrams/02-rag-pipeline-flow.png`
- `docs/diagrams/03-decision-boundary-matrix.png`
- `docs/diagrams/04-deployment-architecture.png`
- `docs/diagrams/05-nudge-state-machine.png`
- `docs/diagrams/06-query-flow-comparison.png`
- `docs/diagrams/07-intent-reranking-example.png`

Then reference in ARCHITECTURE.md with:
```markdown
![System Architecture](diagrams/01-system-architecture.png)
```
