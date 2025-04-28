/**
 * 右下角toast弹窗
 * @param {string} msg - 提示消息
 * @param {string} type - 提示类型: 'success' (绿色), 'error' (红色), 'warning' (黄色, 默认)
 */
function showWarningToast(msg, type = 'warning') {
    let toast = document.getElementById('toast-warning');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'toast-warning';
        toast.style.position = 'fixed';
        toast.style.bottom = '30px';
        toast.style.right = '30px';
        toast.style.zIndex = 9999;
        toast.style.padding = '14px 28px';
        toast.style.borderRadius = '8px';
        toast.style.boxShadow = '0 2px 12px rgba(0,0,0,0.15)';
        toast.style.fontSize = '16px';
        toast.style.display = 'none';
        document.body.appendChild(toast);
    }
    
    // 根据类型设置背景色
    switch (type) {
        case 'success':
            toast.style.background = 'rgba(40,167,69,0.95)'; // 绿色
            toast.style.color = '#fff';
            break;
        case 'error':
            toast.style.background = 'rgba(220,53,69,0.95)'; // 红色
            toast.style.color = '#fff';
            break;
        case 'warning':
        default:
            toast.style.background = 'rgba(255,193,7,0.95)'; // 黄色
            toast.style.color = '#222';
            break;
    }
    
    toast.innerText = msg;
    toast.style.display = 'block';
    setTimeout(() => {
        toast.style.display = 'none';
    }, 3500);
}

window.showWarningToast = showWarningToast;
