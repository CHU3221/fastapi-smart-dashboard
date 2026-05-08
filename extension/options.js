chrome.storage.sync.get({ dashboardUrl: '127.0.0.1:7600' }, (items) => {
    document.getElementById('dashboardUrl').value = items.dashboardUrl;
});

document.getElementById('saveBtn').addEventListener('click', () => {
    let url = document.getElementById('dashboardUrl').value.replace(/^https?:\/\//, '');
    
    chrome.storage.sync.set({ dashboardUrl: url }, () => {
        const status = document.getElementById('status');
        status.textContent = '저장되었습니다';
        setTimeout(() => { status.textContent = ''; }, 2000);
    });
});