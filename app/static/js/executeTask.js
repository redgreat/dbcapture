// 执行任务（数据库结构对比并生成报告）
async function executeTask(taskId) {
    // 使用美观的确认对话框替代原生 confirm
    const confirmed = await showConfirmDialog(
        '确定要执行该任务并生成对比报告吗？', 
        '执行任务', 
        '执行', 
        '取消',
        'btn-success'
    );
    if (!confirmed) return;
    try {
        const statusRes = await fetch(`/api/v1/tasks/${taskId}/status`, {
            headers: getHeaders()
        });
        const statusData = await statusRes.json();

        if (statusData === 'running') {
            showWarningToast('任务正在执行中，请稍后再试。', 'warning');
            return;
        }
        const executePromise = fetch(`/api/v1/tasks/${taskId}/execute`, {
            method: 'POST',
            headers: getHeaders()
        });
        setTimeout(fetchTasks, 500);      
        const res = await executePromise;
        const data = await res.json();
        
        if (res.ok) {
            showWarningToast('任务已提交执行，请稍后查看日志和报告。', 'success');
        } else {
            showWarningToast('执行失败：' + (data.detail || JSON.stringify(data)), 'error');
            fetchTasks();
        }
    } catch (e) {
        showWarningToast('请求异常：' + e, 'error');
    }
}
