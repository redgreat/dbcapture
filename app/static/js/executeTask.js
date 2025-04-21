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
            alert('任务已提交执行，请稍后查看日志和报告。');
            fetchTasks();
        } else {
            alert('执行失败：' + (data.detail || JSON.stringify(data)));
        }
    } catch (e) {
        alert('请求异常：' + e);
    }
}
