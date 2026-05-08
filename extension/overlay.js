// 설정된 대시보드 주소를 가져온 후 오버레이 생성
chrome.storage.sync.get({ dashboardUrl: 'localhost:7600' }, (items) => {
    const myDashboardUrl = items.dashboardUrl;

    const overlay = document.createElement('div');
    overlay.style.cssText = `
        position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%);
        background: rgba(20, 20, 20, 0.85); padding: 10px 15px; 
        border-radius: 20px; border: 1px solid #333;
        z-index: 9999999; display: flex; flex-direction: row; gap: 15px;
        opacity: 0.2; transition: opacity 0.3s ease-in-out, background 0.3s;
        backdrop-filter: blur(5px);
    `;

    overlay.onmouseover = () => { overlay.style.opacity = '1'; overlay.style.background = 'rgba(20, 20, 20, 0.95)'; };
    overlay.onmouseout = () => { overlay.style.opacity = '0.2'; overlay.style.background = 'rgba(20, 20, 20, 0.85)'; };

    function createImgBtn(domain, tooltip, onClick) {
        const btn = document.createElement('img');
        
        // 대시보드는 로컬 파일, 나머지는 구글 Favicon API 사용
        if (domain === "dashboard") {
            btn.src = chrome.runtime.getURL("icon_dashboard.png"); 
        } else {
            btn.src = `https://www.google.com/s2/favicons?domain=${domain}&sz=64`;
        }
        
        btn.title = tooltip; 
        btn.style.cssText = "width: 32px; height: 32px; border-radius: 8px; cursor: pointer; transition: transform 0.2s;";
        btn.onmouseover = () => btn.style.transform = "scale(1.15) translateY(-3px)";
        btn.onmouseout = () => btn.style.transform = "scale(1) translateY(0)";
        btn.onclick = onClick;
        return btn;
    }

    // 버튼 추가 (대시보드는 저장된 URL 또는 'Smart Dashboard' 제목으로 검색)
    overlay.appendChild(createImgBtn("dashboard", "대시보드", () => chrome.runtime.sendMessage({action: "switchTab", keyword: "Smart Dashboard"})));
    overlay.appendChild(createImgBtn("discord.com", "디스코드", () => chrome.runtime.sendMessage({action: "switchTab", keyword: "discord.com"})));
    overlay.appendChild(createImgBtn("chzzk.naver.com", "치지직", () => chrome.runtime.sendMessage({action: "switchTab", keyword: "chzzk.naver.com"})));
    overlay.appendChild(createImgBtn("youtube.com", "유튜브", () => chrome.runtime.sendMessage({action: "switchTab", keyword: "youtube.com"})));
    overlay.appendChild(createImgBtn("music.youtube.com", "유튜브 뮤직", () => chrome.runtime.sendMessage({action: "switchTab", keyword: "music.youtube.com"})));

    document.body.appendChild(overlay);
});