// Inicializa os ícones Lucide no carregamento
document.addEventListener("DOMContentLoaded", () => {
    lucide.createIcons();
});

let currentJobId = null;
let pollingInterval = null;
let rawReportContent = "";

// Elementos da UI
const queryInput = document.getElementById("query-input");
const startBtn = document.getElementById("start-btn");
const statusSection = document.getElementById("status-section");
const statusBadge = document.getElementById("status-badge");
const logsTerminal = document.getElementById("logs-terminal");
const reportSection = document.getElementById("report-section");
const reportBody = document.getElementById("report-body");
const copyBtn = document.getElementById("copy-btn");
const downloadBtn = document.getElementById("download-btn");

// Elementos de Aprovação (HITL)
const approvalSection = document.getElementById("approval-section");
const subQueriesEditor = document.getElementById("sub-queries-editor");
const addQueryBtn = document.getElementById("add-query-btn");
const approveBtn = document.getElementById("approve-btn");

// Steps do Progresso Visual
const steps = {
    PLANNING: document.getElementById("step-PLANNING"),
    AWAITING_APPROVAL: document.getElementById("step-AWAITING_APPROVAL"),
    RESEARCHING: document.getElementById("step-RESEARCHING"),
    WRITING: document.getElementById("step-WRITING")
};

// Event Listeners
startBtn.addEventListener("click", handleStartResearch);
queryInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") handleStartResearch();
});
copyBtn.addEventListener("click", copyToClipboard);
downloadBtn.addEventListener("click", downloadMarkdownFile);
addQueryBtn.addEventListener("click", handleAddQueryRow);
approveBtn.addEventListener("click", handleApproveResearch);

// Função para Disparar a Pesquisa (Fase 1: Planejamento)
async function handleStartResearch() {
    const query = queryInput.value.trim();
    if (!query) return alert("Por favor, insira o tópico da sua pesquisa.");

    // Reseta o estado da tela
    resetUI();

    try {
        startBtn.disabled = true;
        startBtn.querySelector("span").textContent = "Planejando...";

        const response = await fetch("/api/research", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ query: query })
        });

        if (!response.ok) throw new Error("Erro de servidor ao iniciar pesquisa.");

        const data = await response.json();
        currentJobId = data.job_id;

        // Exibe o painel de status
        statusSection.classList.remove("hidden");
        updateBadge("Planejando", "active");

        // Inicia o Polling de Logs e Status
        startPolling();
    } catch (error) {
        console.error(error);
        alert("Falha ao iniciar a pesquisa: " + error.message);
        startBtn.disabled = false;
        startBtn.querySelector("span").textContent = "Iniciar Pesquisa";
    }
}

// Inicia o monitoramento periódico do Job
function startPolling() {
    if (pollingInterval) clearInterval(pollingInterval);
    
    // Atualiza imediatamente e depois a cada 2 segundos
    pollStatus();
    pollingInterval = setInterval(pollStatus, 2000);
}

// Consulta a API e atualiza a interface
async function pollStatus() {
    if (!currentJobId) return;

    try {
        const response = await fetch(`/api/research/${currentJobId}`);
        if (!response.ok) throw new Error("Erro ao consultar status.");

        const data = await response.json();
        
        // Atualiza os Logs no terminal
        updateLogs(data.logs);

        // Atualiza os indicadores de passos (steps) baseados no status do banco
        updateStepsVisuals(data.status);

        if (data.status === "AWAITING_APPROVAL") {
            // Pausa o polling enquanto aguarda a aprovação do usuário
            clearInterval(pollingInterval);
            pollingInterval = null;
            
            updateBadge("Aprovação Requerida", "active");
            
            // Popula o editor e exibe a caixa de edição
            populateApprovalEditor(data.sub_queries);
            approvalSection.classList.remove("hidden");
            approvalSection.scrollIntoView({ behavior: "smooth" });
            
            startBtn.disabled = false;
            startBtn.querySelector("span").textContent = "Iniciar Pesquisa";
        } else if (data.status === "COMPLETED") {
            clearInterval(pollingInterval);
            updateBadge("Concluído", "success");
            
            // Exibe e renderiza o relatório Markdown
            rawReportContent = data.report_content;
            renderReport(data.report_content);
            
            startBtn.disabled = false;
            startBtn.querySelector("span").textContent = "Iniciar Pesquisa";
        } else if (data.status === "FAILED") {
            clearInterval(pollingInterval);
            updateBadge("Falhou", "failed");
            startBtn.disabled = false;
            startBtn.querySelector("span").textContent = "Iniciar Pesquisa";
            alert("Ocorreu um erro crítico durante a pesquisa. Verifique os logs no terminal.");
        } else {
            // Em progresso (PLANNING, RESEARCHING, WRITING)
            updateBadge(capitalize(data.status), "active");
        }
    } catch (error) {
        console.error(error);
        addSingleLog("[ERRO DE CONEXÃO] Falha ao comunicar com o servidor. Re-tentando...");
    }
}

// Cria um campo de entrada para uma sub-query no editor
function createQueryRow(value = "") {
    const row = document.createElement("div");
    row.className = "editor-row";
    
    const input = document.createElement("input");
    input.type = "text";
    input.value = value;
    input.placeholder = "Digite um termo ou sub-tópico de pesquisa...";
    
    const deleteBtn = document.createElement("button");
    deleteBtn.className = "btn-delete";
    deleteBtn.title = "Remover tópico";
    deleteBtn.innerHTML = '<i data-lucide="trash-2" style="width: 16px; height: 16px;"></i>';
    
    deleteBtn.addEventListener("click", () => {
        row.remove();
    });
    
    row.appendChild(input);
    row.appendChild(deleteBtn);
    
    subQueriesEditor.appendChild(row);
    lucide.createIcons();
}

// Preenche o editor com os tópicos sugeridos pelo Planner
function populateApprovalEditor(subQueries) {
    subQueriesEditor.innerHTML = "";
    if (subQueries && subQueries.length > 0) {
        subQueries.forEach(sq => {
            createQueryRow(sq);
        });
    } else {
        createQueryRow("");
    }
}

// Adiciona um novo tópico vazio
function handleAddQueryRow() {
    createQueryRow("");
}

// Submete a aprovação das sub-queries para reiniciar a investigação
async function handleApproveResearch() {
    const inputs = subQueriesEditor.querySelectorAll(".editor-row input");
    const subQueries = [];
    
    inputs.forEach(input => {
        const val = input.value.trim();
        if (val) subQueries.push(val);
    });
    
    if (subQueries.length === 0) {
        return alert("Por favor, adicione pelo menos uma sub-consulta para prosseguir com a pesquisa.");
    }
    
    try {
        approveBtn.disabled = true;
        approveBtn.querySelector("span").textContent = "Iniciando Investigação...";
        
        const response = await fetch(`/api/research/${currentJobId}/approve`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ sub_queries: subQueries })
        });
        
        if (!response.ok) throw new Error("Erro de servidor ao submeter aprovação.");
        
        // Esconde a área de aprovação e reinicia o polling
        approvalSection.classList.add("hidden");
        updateBadge("Investigando", "active");
        
        startPolling();
    } catch (error) {
        console.error(error);
        alert("Falha ao submeter o escopo aprovado: " + error.message);
    } finally {
        approveBtn.disabled = false;
        approveBtn.querySelector("span").textContent = "Aprovar e Iniciar Investigação";
    }
}

// Atualização de Logs na UI
let lastLogsLength = 0;
function updateLogs(logs) {
    if (logs.length === lastLogsLength) return;
    
    logsTerminal.innerHTML = "";
    logs.forEach(log => {
        const p = document.createElement("p");
        p.textContent = log;
        logsTerminal.appendChild(p);
    });
    
    lastLogsLength = logs.length;
    logsTerminal.scrollTop = logsTerminal.scrollHeight;
}

function addSingleLog(msg) {
    const p = document.createElement("p");
    p.textContent = msg;
    p.style.color = "#ef4444";
    logsTerminal.appendChild(p);
    logsTerminal.scrollTop = logsTerminal.scrollHeight;
}

// Atualiza o Badge de Status
function updateBadge(text, type) {
    statusBadge.textContent = text === "Awaiting_approval" ? "Aprovação Requerida" : text;
    statusBadge.className = `badge ${type}`;
}

// Atualiza a visualização dos círculos de progresso
function updateStepsVisuals(status) {
    // Limpa classes
    Object.values(steps).forEach(step => {
        if (step) step.classList.remove("active", "completed");
    });

    if (status === "PLANNING") {
        steps.PLANNING.classList.add("active");
    } else if (status === "AWAITING_APPROVAL") {
        steps.PLANNING.classList.add("completed");
        steps.AWAITING_APPROVAL.classList.add("active");
    } else if (status === "RESEARCHING") {
        steps.PLANNING.classList.add("completed");
        steps.AWAITING_APPROVAL.classList.add("completed");
        steps.RESEARCHING.classList.add("active");
    } else if (status === "WRITING") {
        steps.PLANNING.classList.add("completed");
        steps.AWAITING_APPROVAL.classList.add("completed");
        steps.RESEARCHING.classList.add("completed");
        steps.WRITING.classList.add("active");
    } else if (status === "COMPLETED") {
        steps.PLANNING.classList.add("completed");
        steps.AWAITING_APPROVAL.classList.add("completed");
        steps.RESEARCHING.classList.add("completed");
        steps.WRITING.classList.add("completed");
    }
}

// Renderiza o Relatório Markdown
function renderReport(markdown) {
    marked.setOptions({
        breaks: true,
        gfm: true
    });
    
    reportBody.innerHTML = marked.parse(markdown);
    reportSection.classList.remove("hidden");
    reportSection.scrollIntoView({ behavior: "smooth" });
}

// Copiar Markdown para área de transferência
function copyToClipboard() {
    if (!rawReportContent) return;
    
    navigator.clipboard.writeText(rawReportContent)
        .then(() => {
            const origIcon = copyBtn.innerHTML;
            copyBtn.innerHTML = '<i data-lucide="check" style="color: #10b981;"></i>';
            lucide.createIcons();
            setTimeout(() => {
                copyBtn.innerHTML = origIcon;
                lucide.createIcons();
            }, 2000);
        })
        .catch(err => {
            alert("Erro ao copiar: " + err);
        });
}

// Baixar arquivo Markdown
function downloadMarkdownFile() {
    if (!rawReportContent) return;
    
    const blob = new Blob([rawReportContent], { type: "text/markdown;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    
    const querySlug = queryInput.value.trim()
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, "-")
        .substring(0, 30);
        
    link.href = url;
    link.setAttribute("download", `relatorio-${querySlug || "pesquisa"}.md`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Funções Auxiliares
function resetUI() {
    statusSection.classList.add("hidden");
    approvalSection.classList.add("hidden");
    reportSection.classList.add("hidden");
    logsTerminal.innerHTML = "";
    subQueriesEditor.innerHTML = "";
    reportBody.innerHTML = "";
    rawReportContent = "";
    lastLogsLength = 0;
    
    Object.values(steps).forEach(step => {
        if (step) step.classList.remove("active", "completed");
    });
}

function capitalize(s) {
    if (!s) return "";
    return s.charAt(0).toUpperCase() + s.slice(1).toLowerCase();
}
