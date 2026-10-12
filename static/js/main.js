
function toggleAI() {
    document.getElementById('ai-chat-window').classList.toggle('ai-hidden');
}

function openTab(tabName, contentUrl) {
    const headerContainer = document.getElementById('tab-headers');
    const body = document.getElementById('tab-body');
    
    // Remove active class from all tabs
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    
    // Create tab button if not exists
    let btn = document.getElementById('tab-' + tabName);
    if (!btn) {
        btn = document.createElement('button');
        btn.id = 'tab-' + tabName;
        btn.className = 'tab-btn';
        btn.innerText = tabName;
        btn.onclick = () => {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            loadContent(contentUrl);
        };
        headerContainer.appendChild(btn);
    }
    
    btn.classList.add('active');
    loadContent(contentUrl);
}

async function loadContent(url) {
    const body = document.getElementById('tab-body');
    body.innerHTML = '<div class="text-center">جاري التحميل...</div>';
    try {
        const response = await fetch(url);
        body,innerHTML = await response.text();
    } catch (e) {
        body.innerHTML = '<div class="text-danger">خطأ في تحميل الصفحة</div>';
    }
}

async function sendToAI() {
    const input = document.getElementById('ai-input');
    const messages = document.getElementById('ai-messages');
    const text = input.value;
    if (!text) return;

    messages.innerHTML += `<div class="user-msg"><b>أنت:</b> ${text}</div>`;
    input.value = '';

    const response = await fetch('/api/ai/process', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({query: text})
    });
    const data = await response.json();
    messages.innerHTML += `<div class="ai-msg"><b>المساعد:</b> ${data.reply}</div>`;
    messages.scrollTop = messages.scrollHeight;
}
