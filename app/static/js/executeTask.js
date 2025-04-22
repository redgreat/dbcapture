// 右下角toast弹窗
function showWarningToast(msg) {
    let toast = document.getElementById('toast-warning');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'toast-warning';
        toast.style.position = 'fixed';
        toast.style.bottom = '30px';
        toast.style.right = '30px';
        toast.style.zIndex = 9999;
        toast.style.background = 'rgba(255,193,7,0.95)';
        toast.style.color = '#222';
        toast.style.padding = '14px 28px';
        toast.style.borderRadius = '8px';
        toast.style.boxShadow = '0 2px 12px rgba(0,0,0,0.15)';
        toast.style.fontSize = '16px';
        toast.style.display = 'none';
        document.body.appendChild(toast);
    }
    toast.innerText = msg;
    toast.style.display = 'block';
    setTimeout(() => {
        toast.style.display = 'none';
    }, 3500);
}

// 执行任务（数据库结构对比并生成报告）
async function executeTask(taskId) {
    if (!confirm('确定要执行该任务并生成对比报告吗？')) return;
    try {
        const res = await fetch(`/api/v1/tasks/${taskId}/execute`, {
            method: 'POST',
            headers: getHeaders()
        });
        const data = await res.json();
        if (res.ok) {
            showWarningToast('任务已提交执行，请稍后查看日志和报告。');
            fetchTasks();
        } else {
            showWarningToast('执行失败：' + (data.detail || JSON.stringify(data)));
        }
    } catch (e) {
        showWarningToast('请求异常：' + e);
    }
}
