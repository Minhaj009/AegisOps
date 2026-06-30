# AegisOps.dev — Autonomous Code Remediation powered by Qwen Cloud

AegisOps is a high-fidelity, autonomous cybersecurity and code patching engine. It integrates static analysis, AST-level vulnerability scanning, and multi-agent consensus validation loops to autonomously generate, verify, and commit security patches to software repositories.

AegisOps is built for the **Global AI Hackathon Series with Qwen Cloud**, targeting **Track 3: Agent Society** (Multi-agent ecosystem coordination) and **Track 4: Autopilot Agent** (Autonomous workflows).

---

## 🚀 Key Features

*   **Lead Auditor Agent**: Ingests codebases, parses AST representation, and runs semantic vulnerability audits to produce a structured security footprint.
*   **Patch Developer Agent (Qwen-Max)**: Consumes the vulnerability footprint and generates surgical, minimal-diff search-and-replace patches to address root flaws.
*   **Sandbox Engineer Agent**: Provisions isolated, short-lived Docker containers mimicking target production environments to execute validation scripts and exploit reproductions.
*   **Consensus Handshake Gate**: Prevents unverified code from merging. The Patch Developer and Sandbox Engineer run a multi-turn feedback loop (up to 3 retries) until the test suite returns `VERIFIED`.
*   **Command Cockpit Dashboard**: A premium, light-themed engineering workspace featuring a horizontal telemetry ribbon, split-pane IDE-grade diff viewer, and a real-time log terminal streamed via Server-Sent Events (SSE).
*   **Alibaba Cloud Ready**: Includes scaffolding for deploying orchestrators to ECS/ACK and pushing sandbox images to the Alibaba Cloud Registry (ACR).

---

## 📐 System Architecture

```mermaid
graph TD
    User([User Target Repo]) -->|Input Cwd| Router[AegisOps Orchestration Router]
    
    subgraph AgentSociety ["Agent Society (Consensus Loop)"]
        Router -->|Scan Codebase| Auditor[Lead Auditor Agent]
        Auditor -->|Vulnerability Context| PatchDev[Patch Developer Agent (Qwen-Max)]
        PatchDev -->|Proposed Diff| Sandbox[Sandbox Engineer Agent]
        Sandbox -->|Docker Container Execution| RunTests[Exploit Validation / Unit Tests]
        RunTests -->|Success / Failure Logs| PatchDev
    end
    
    Sandbox -->|Approved & Verified Patch| GitMgr[Git Manager Agent]
    GitMgr -->|Commit & Push Merge Request| Repo[(Remote Repository)]
    
    Router -->|Real-time Events via SSE| WebUI[Command Cockpit Dashboard]
```

---

## 🛠️ Tech Stack & Qwen Integration

*   **Large Language Model**: [Qwen-Max](https://www.alibabacloud.com/help/en/model-studio/) via the **Alibaba Cloud Model Studio** and `dashscope` SDK.
*   **Orchestration**: Asynchronous Python core utilizing `asyncio` for multi-threaded pipeline execution.
*   **Telemetry**: Custom `metrics_tracker.py` to record execution costs, token consumption, and agent latencies.
*   **Frontend**: Light-themed engineering UI built with Vite, Vanilla CSS design tokens, and a custom heights-synchronized panel resizer.

---

## ☁️ Alibaba Cloud Proof of Deployment

AegisOps.dev is deployed and runs on **Alibaba Cloud Simple Application Server / ECS** in the **Indonesia (Jakarta) / Singapore** regions.

### Qwen Cloud API Integration
The primary LLM gateway code is located in [`src/llm/qwen_gateway.py`](file:///f:/AegisOps/src/llm/qwen_gateway.py#L42) and is configured to route API calls directly to the international Model Studio endpoint:
*   **Base URL**: `https://dashscope-intl.aliyuncs.com/compatible-mode/v1`

### Infrastructure Scaffolding
Deployments are provisioned using the Terraform scripts provided in [`deploy/main.tf`](file:///f:/AegisOps/deploy/main.tf) to set up:
*   VPC & Security Groups.
*   ECS Instances running Docker.
*   Alibaba Cloud Container Registry (ACR) to build and host the Sandbox Engineer's test suite execution containers (see [`deploy/push_to_acr.sh`](file:///f:/AegisOps/deploy/push_to_acr.sh)).

---

## 🤝 Hackathon Tracks & Criteria Alignment

### Track 3: Agent Society
AegisOps demonstrates a highly structured multi-agent ecosystem. Each agent holds defined roles and access constraints:
*   The **Auditor** is read-only.
*   The **Developer** writes patches but cannot merge.
*   The **Sandbox Engineer** validates but cannot edit.
*   The **Interactive Co-pilot Gate** allows developers to approve or reject patches.
They coordinate via a Pydantic-compliant message protocol, resolving code fixes through automated consensus loops.

### Track 4: Autopilot Agent
The orchestrator operates completely on autopilot. A single repository target path initiates a sequential flow: threat modeling -> patching -> container provisioning -> test validation -> git commit, requiring zero human intervention.

---

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
