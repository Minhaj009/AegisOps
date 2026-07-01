// app.js - AegisOps Premium Matte Dashboard Controller

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("run-form");
    const targetInput = document.getElementById("target-path");
    const submitBtn = document.getElementById("submit-btn");
    const clearBtn = document.getElementById("clear-console-btn");
    const consoleLogs = document.getElementById("console-logs");
    
    // Telemetry HUD Elements
    const hudTokens = document.getElementById("hud-tokens");
    const hudCost = document.getElementById("hud-cost");
    const hudSandbox = document.getElementById("hud-sandbox");
    const hudRuntime = document.getElementById("hud-runtime");

    // Session Diagnostics Elements
    const diagCalls = document.getElementById("diag-calls");
    const diagInputTokens = document.getElementById("diag-input-tokens");
    const diagOutputTokens = document.getElementById("diag-output-tokens");
    const diagAvgLatency = document.getElementById("diag-avg-latency");

    // Code Diff Elements
    const codeOriginal = document.getElementById("code-original");
    const codePatched = document.getElementById("code-patched");
    const fileLabelOriginal = document.getElementById("file-label-original");
    const fileLabelPatched = document.getElementById("file-label-patched");

    // Approval DOM Elements
    const approvalCard = document.getElementById("approval-card");
    const approveBtn = document.getElementById("approve-btn");
    const rejectBtn = document.getElementById("reject-btn");

    // Agent Society Communication Element
    const communicationChat = document.getElementById("communication-chat");

    let eventSource = null;
    let timerInterval = null;
    let secondsElapsed = 0;
    let tokenCount = 0;
    let lastRenderedMsgCount = 0;

    // Agent metadata map: CSS class, avatar initials, and display name
    const AGENT_META = {
        "Lead Auditor":     { cls: "agent-lead-auditor",     initials: "LA", label: "Lead Auditor" },
        "Patch Developer":  { cls: "agent-patch-developer",  initials: "PD", label: "Patch Developer" },
        "Sandbox Engineer": { cls: "agent-sandbox-engineer", initials: "SE", label: "Sandbox Engineer" },
        "Git Manager":      { cls: "agent-git-manager",      initials: "GM", label: "Git Manager" },
        "Orchestrator":     { cls: "agent-orchestrator",     initials: "OR", label: "Orchestrator" },
        "User":             { cls: "agent-user",             initials: "U",  label: "User" }
    };

    // Helper to format large numbers with commas
    function formatNumber(num) {
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    }

    // Helper to format time as MM:SS
    function formatTime(secs) {
        const minutes = Math.floor(secs / 60);
        const seconds = secs % 60;
        const mm = minutes < 10 ? `0${minutes}` : minutes;
        const ss = seconds < 10 ? `0${seconds}` : seconds;
        return `${mm}:${ss}`;
    }

    // Timer functions
    function startTimer() {
        stopTimer();
        secondsElapsed = 0;
        hudRuntime.innerText = "00:00";
        timerInterval = setInterval(() => {
            secondsElapsed++;
            hudRuntime.innerText = formatTime(secondsElapsed);
        }, 1000);
    }

    function stopTimer() {
        if (timerInterval) {
            clearInterval(timerInterval);
            timerInterval = null;
        }
    }

    // Update Token Monitor
    function setTokenCount(count) {
        tokenCount = count;
        hudTokens.innerText = formatNumber(tokenCount);
    }

    // Update Sandbox Monitor state
    function setSandboxState(stateLabel, stateClass) {
        hudSandbox.innerText = stateLabel.toUpperCase();
        hudSandbox.className = "item-value"; // reset to new index.html base class
        if (stateClass) {
            const mappedClass = stateClass.replace("status-", "state-").replace("state-off", "state-inactive");
            hudSandbox.classList.add(mappedClass);
        }
    }

    // Update Metrics and Costs in UI
    function updateMetricsHUD(metrics) {
        if (!metrics) return;
        
        const totalTokens = (metrics.total_input_tokens || 0) + (metrics.total_output_tokens || 0);
        hudTokens.innerText = formatNumber(totalTokens);
        
        const cost = metrics.total_estimated_cost_usd || 0;
        hudCost.innerText = `$${cost.toFixed(6)}`;
        
        // Update diagnostics sidebar card
        if (diagCalls) diagCalls.innerText = metrics.total_calls || 0;
        if (diagInputTokens) diagInputTokens.innerText = formatNumber(metrics.total_input_tokens || 0);
        if (diagOutputTokens) diagOutputTokens.innerText = formatNumber(metrics.total_output_tokens || 0);
        
        const avgLat = metrics.average_latency_seconds || 0;
        if (diagAvgLatency) diagAvgLatency.innerText = `${avgLat.toFixed(2)}s`;
    }

    // Render Agent Society Communication Bubbles (incremental)
    function renderAgentMessages(messages) {
        if (!communicationChat || !messages || messages.length === 0) return;
        
        // Only render new messages since last render
        if (messages.length <= lastRenderedMsgCount) return;
        
        // Clear empty state on first render
        if (lastRenderedMsgCount === 0) {
            communicationChat.innerHTML = "";
        }
        
        const newMessages = messages.slice(lastRenderedMsgCount);
        
        newMessages.forEach(msg => {
            const senderMeta = AGENT_META[msg.sender] || { cls: "agent-orchestrator", initials: "??", label: msg.sender };
            const recipientMeta = AGENT_META[msg.recipient] || { cls: "", initials: "", label: msg.recipient };
            
            const bubble = document.createElement("div");
            bubble.className = `chat-bubble ${senderMeta.cls}`;
            bubble.innerHTML = `
                <div class="bubble-avatar">${senderMeta.initials}</div>
                <div class="bubble-body">
                    <div class="bubble-header">
                        <span class="bubble-sender">${senderMeta.label}</span>
                        <span class="bubble-arrow">➜</span>
                        <span class="bubble-recipient">${recipientMeta.label}</span>
                    </div>
                    <div class="bubble-content">${msg.message}</div>
                </div>
            `;
            communicationChat.appendChild(bubble);
        });
        
        lastRenderedMsgCount = messages.length;
        communicationChat.scrollTop = communicationChat.scrollHeight;
    }

    // Helper to log text to our console view
    function logToConsole(message, type = "system") {
        const line = document.createElement("div");
        line.className = `log-line ${type}-line`;
        
        const timestamp = new Date().toLocaleTimeString();
        line.innerText = `[${timestamp}] ${message}`;
        
        consoleLogs.appendChild(line);
        consoleLogs.scrollTop = consoleLogs.scrollHeight;
    }

    // Reset timeline classes
    function resetTimeline() {
        const nodes = document.querySelectorAll(".state-node");
        nodes.forEach(node => {
            node.classList.remove("active", "complete", "failed");
        });
    }

    // Update active states
    function updateTimeline(activeState) {
        const order = ["START", "AUDIT", "PATCH", "TEST", "COMMIT"];
        const activeIndex = order.indexOf(activeState);

        order.forEach((state, index) => {
            const node = document.getElementById(`node-${state}`);
            if (!node) return;

            if (index < activeIndex) {
                node.classList.remove("active", "failed");
                node.classList.add("complete");
            } else if (index === activeIndex) {
                node.classList.remove("complete", "failed");
                node.classList.add("active");
            } else {
                node.classList.remove("active", "complete", "failed");
            }
        });
    }

    // Parsing Search-and-Replace Block diffs
    function parseAndRenderDiff(patchContent) {
        if (!patchContent) return;

        // Extract filename if exists
        let filename = "target_file.py";
        const fileMatch = patchContent.match(/FILE:\s*([^\n\r]+)/);
        if (fileMatch) {
            filename = fileMatch[1].strip ? fileMatch[1].strip() : fileMatch[1].trim();
        }

        // Try extracting search blocks
        const searchPattern = /<<<<<<< SEARCH[\r\n]+([\s\S]*?)=======/;
        const replacePattern = /=======[\r\n]+([\s\S]*?)>>>>>>> REPLACE/;

        const searchMatch = patchContent.match(searchPattern);
        const replaceMatch = patchContent.match(replacePattern);

        if (searchMatch && replaceMatch) {
            fileLabelOriginal.innerText = `- ${filename} (Search Block)`;
            fileLabelPatched.innerText = `+ ${filename} (Replace Block)`;
            codeOriginal.innerText = searchMatch[1];
            codePatched.innerText = replaceMatch[1];
        } else {
            // Fallback: Display raw patch in both if unable to split
            fileLabelOriginal.innerText = `Raw Patch Output`;
            fileLabelPatched.innerText = `Raw Patch Output`;
            codeOriginal.innerText = patchContent;
            codePatched.innerText = patchContent;
        }
    }

    // Clear logs
    clearBtn.addEventListener("click", () => {
        consoleLogs.innerHTML = "";
        logToConsole("Console logs cleared.", "system");
    });

    // Form submission
    form.addEventListener("submit", (e) => {
        e.preventDefault();

        const targetPath = targetInput.value.trim();
        if (!targetPath) return;

        if (eventSource) {
            eventSource.close();
        }

        // Reset UI & State
        resetTimeline();
        startTimer();
        setTokenCount(0);
        setSandboxState("OFFLINE", "status-off");
        
        // Reset diagnostics panel & HUD cost
        if (hudCost) hudCost.innerText = "$0.000000";
        if (diagCalls) diagCalls.innerText = "0";
        if (diagInputTokens) diagInputTokens.innerText = "0";
        if (diagOutputTokens) diagOutputTokens.innerText = "0";
        if (diagAvgLatency) diagAvgLatency.innerText = "0.00s";
        
        // Reset Agent Society Communication
        lastRenderedMsgCount = 0;
        if (communicationChat) {
            communicationChat.innerHTML = `
                <div class="comms-empty-state">
                    <i class="fa-solid fa-satellite-dish"></i>
                    <p>Establishing agent communication channel...</p>
                </div>
            `;
        }
        
        fileLabelOriginal.innerText = "-";
        fileLabelPatched.innerText = "+";
        codeOriginal.innerText = "Waiting for Patch Developer Agent generation...";
        codePatched.innerText = "Waiting for Patch Developer Agent generation...";
        
        logToConsole(`Initiating pipeline execution for target: ${targetPath}`, "info");

        // Hide approval panel
        approvalCard.classList.add("hidden");
        approveBtn.disabled = false;
        rejectBtn.disabled = false;

        // Disable input
        submitBtn.disabled = true;
        targetInput.disabled = true;
        submitBtn.querySelector(".btn-text").innerText = "Executing Pipeline...";

        // Extract selected mode
        const modeRadio = document.querySelector('input[name="pipeline-mode"]:checked');
        const mode = modeRadio ? modeRadio.value : "autopilot";

        // Establish connection
        const url = `/api/run?target=${encodeURIComponent(targetPath)}&mode=${mode}`;
        eventSource = new EventSource(url);

        eventSource.onmessage = (event) => {
            try {
                const payload = JSON.parse(event.data);
                const { state, message, data } = payload;

                let logType = "info";
                if (state === "ERROR") logType = "error";
                else if (state === "COMPLETED" || state === "COMMIT") logType = "success";
                else if (state === "ROLLBACK") logType = "warn";
                
                logToConsole(message, logType);

                // Update Telemetry Metrics from backend payload
                if (data && data.metrics) {
                    updateMetricsHUD(data.metrics);
                }

                // Update Agent Society Communication
                if (data && data.agent_messages) {
                    renderAgentMessages(data.agent_messages);
                }

                // Update Telemetry Metrics & States
                if (state === "START") {
                    updateTimeline("START");
                    setTokenCount(1500); // initial schema ingestion tokens
                    setSandboxState("OFFLINE", "status-off");
                } 
                else if (state === "SNAPSHOT") {
                    setTokenCount(tokenCount + 300);
                }
                else if (state === "AUDIT") {
                    updateTimeline("AUDIT");
                    if (message.includes("Analyzing")) {
                        setTokenCount(tokenCount + 8500); // prompt size
                    } else if (message.includes("completed")) {
                        setTokenCount(tokenCount + 3200); // response size
                    }
                } 
                else if (state === "PATCH") {
                    updateTimeline("PATCH");
                    if (message.includes("Generating")) {
                        setTokenCount(tokenCount + 4200);
                    } else if (message.includes("generated")) {
                        setTokenCount(tokenCount + 1800);
                        if (data && data.patch) {
                            parseAndRenderDiff(data.patch);
                        }
                    }
                } 
                else if (state === "TEST") {
                    updateTimeline("TEST");
                    if (message.includes("Provisioning")) {
                        setSandboxState("PROVISIONING", "status-active");
                        setTokenCount(tokenCount + 500);
                    } else if (message.includes("passed")) {
                        setSandboxState("VERIFIED", "status-success");
                    } else if (message.includes("failed")) {
                        setSandboxState("TEST FAILED", "status-error");
                        setTokenCount(tokenCount + 2400); // diagnostic query
                    }
                } 
                else if (state === "WAITING_FOR_APPROVAL") {
                    setSandboxState("AWAITING OK", "status-active");
                    approvalCard.classList.remove("hidden");
                    approveBtn.disabled = false;
                    rejectBtn.disabled = false;
                }
                else if (state === "APPROVAL_DECISION") {
                    approvalCard.classList.add("hidden");
                }
                else if (state === "ROLLBACK") {
                    setSandboxState("OFFLINE", "status-off");
                }
                else if (state === "COMMIT") {
                    updateTimeline("COMMIT");
                } 
                else if (state === "COMPLETED") {
                    stopTimer();
                    setSandboxState("ISOLATED", "status-success");
                    document.querySelectorAll(".state-node").forEach(node => {
                        node.classList.remove("active");
                        node.classList.add("complete");
                    });
                    cleanupConnection();
                } 
                else if (state === "ERROR") {
                    stopTimer();
                    setSandboxState("OFFLINE", "status-off");
                    const activeNode = document.querySelector(".state-node.active");
                    if (activeNode) {
                        activeNode.classList.remove("active");
                        activeNode.classList.add("failed");
                    }
                    cleanupConnection();
                }

            } catch (err) {
                logToConsole(`Failed to parse event data: ${err}`, "error");
            }
        };

        eventSource.onerror = (err) => {
            logToConsole("SSE connection closed or lost. Execution complete.", "system");
            stopTimer();
            cleanupConnection();
        };
    });

    // Approval Button Event Listeners
    approveBtn.addEventListener("click", () => {
        approveBtn.disabled = true;
        rejectBtn.disabled = true;
        logToConsole("Developer clicked APPROVE. Authorizing backend commit...", "info");
        fetch("/api/approve")
            .then(res => res.json())
            .then(data => {
                logToConsole("Approval signal acknowledged by server.", "system");
            })
            .catch(err => {
                logToConsole(`Error sending approval: ${err}`, "error");
                approveBtn.disabled = false;
                rejectBtn.disabled = false;
            });
    });

    rejectBtn.addEventListener("click", () => {
        approveBtn.disabled = true;
        rejectBtn.disabled = true;
        logToConsole("Developer clicked REJECT. Requesting rollback...", "warn");
        fetch("/api/reject")
            .then(res => res.json())
            .then(data => {
                logToConsole("Rejection signal acknowledged by server.", "system");
            })
            .catch(err => {
                logToConsole(`Error sending rejection: ${err}`, "error");
                approveBtn.disabled = false;
                rejectBtn.disabled = false;
            });
    });

    function cleanupConnection() {
        if (eventSource) {
            eventSource.close();
            eventSource = null;
        }
        submitBtn.disabled = false;
        targetInput.disabled = false;
        submitBtn.querySelector(".btn-text").innerText = "Execute Remediation Pipeline";
        approvalCard.classList.add("hidden");
    }

    // Synchronize diff pane heights
    const originalPane = document.querySelector('.diff-pane-original');
    const patchedPane = document.querySelector('.diff-pane-patched');
    
    if (originalPane && patchedPane) {
        let isSyncing = false;
        const syncHeight = (entries) => {
            if (isSyncing) return;
            isSyncing = true;
            for (let entry of entries) {
                const height = entry.target.getBoundingClientRect().height;
                if (entry.target === originalPane) {
                    patchedPane.style.height = `${height}px`;
                } else {
                    originalPane.style.height = `${height}px`;
                }
            }
            requestAnimationFrame(() => {
                isSyncing = false;
            });
        };
        
        const observer = new ResizeObserver(syncHeight);
        observer.observe(originalPane);
        observer.observe(patchedPane);
    }
});
