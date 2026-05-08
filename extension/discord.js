let lastTitle = document.title;
let isCooldown = false; 

const observer = new MutationObserver(() => {
    if (document.title !== lastTitle) {
        if (!isCooldown && (document.title.includes('새 메시지') || document.title.match(/\(\d+\)/))) {
            
            chrome.runtime.sendMessage({
                action: "notifyDashboard",
                payload: {
                    source: "DISCORD",
                    message: "<b>디스코드</b>에 새로운 알림이 있습니다.",
                    border_color: "#5865F2" //Blurple
                }
            });

            isCooldown = true;
            setTimeout(() => { isCooldown = false; }, 5000);
        }
        lastTitle = document.title;
    }
});

const titleNode = document.querySelector('title');
if (titleNode) {
    observer.observe(titleNode, { childList: true });
}