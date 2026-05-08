chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "switchTab") {
        chrome.tabs.query({}, (tabs) => {
            const targetTab = tabs.find(t => 
                (t.url && t.url.includes(request.keyword)) || 
                (t.title && t.title.includes(request.keyword))
            );
            
            if (targetTab) {
                chrome.tabs.update(targetTab.id, { active: true });
                chrome.windows.update(targetTab.windowId, { focused: true });
            } else {
                console.log("해당 탭을 찾을 수 없습니다:", request.keyword);
            }
        });
        sendResponse({ status: "success" }); 
    } 
    
    else if (request.action === "notifyDashboard") {
        chrome.storage.sync.get({ dashboardUrl: 'localhost:7600' }, (items) => {
            const endpoint = `http://${items.dashboardUrl}/api/notify`;
            
            fetch(endpoint, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(request.payload)
            }).catch(err => console.log("대시보드 전송 실패:", err));
        });
        sendResponse({ status: "success" });
    }
    
    return true; 
});