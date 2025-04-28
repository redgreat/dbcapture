// 检查登录状态
function checkAuth() {
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = '/login';
        return false;
    }
    return true;
}

// 获取请求头
function getHeaders() {
    return {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
        'Content-Type': 'application/json'
    };
}

// 退出登录
function logout() {
    localStorage.removeItem('token');
    window.location.href = '/login';
}

// 加载数据库连接列表
async function loadDbConnections() {
    if (!checkAuth()) return;
    try {
        const res = await fetch('/api/v1/connections', {
            headers: getHeaders()
        });
        if (res.status === 401) {
            window.location.href = '/login';
            return;
        }
        const data = await res.json();
        // 更新任务创建表单的选择框
        const sourceSelect = document.getElementById('source_conn_id');
        const targetSelect = document.getElementById('target_conn_id');
        sourceSelect.innerHTML = '<option value="">请选择源数据库</option>';
        targetSelect.innerHTML = '<option value="">请选择目标数据库</option>';
        data.forEach(conn => {
            const label = `${conn.name}（${conn.host}:${conn.port}/${conn.database}）`;
            sourceSelect.innerHTML += `<option value="${conn.id}">${label}</option>`;
            targetSelect.innerHTML += `<option value="${conn.id}">${label}</option>`;
        });
        // 更新连接列表
        const tbody = document.getElementById('connectionTable');
        if (data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center">暂无连接</td></tr>';
        } else {
            tbody.innerHTML = '';
            data.forEach(conn => {
                tbody.innerHTML += `<tr><td>${conn.id}</td><td>${conn.name}</td><td>${conn.host}</td><td>${conn.port}</td><td>${conn.database}</td><td>${conn.user}</td><td><button class="btn btn-danger btn-sm" onclick="deleteConnection(${conn.id})">删除</button></td></tr>`;
            });
        }
    } catch (err) {
        showWarningToast('请求异常：' + err, 'error');
    }
}

// 加载任务列表
async function fetchTasks(showToast = false) {
    if (!checkAuth()) return;
    try {
        const res = await fetch('/api/v1/tasks', {
            headers: getHeaders()
        });
        if (res.status === 401) {
            window.location.href = '/login';
            return;
        }
        const data = await res.json();
        const tbody = document.getElementById('taskTable');
        if (data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center">暂无任务</td></tr>';
        } else {
            tbody.innerHTML = '';
            data.forEach(task => {
                const desc = task.description || '';
                const shortDesc = desc.length > 10 ? desc.slice(0, 10) + '...' : desc;
                let reportBtn = '';
                if (task.status === 'completed' && task.result_url) {
                    reportBtn = `<a href="${task.result_url}" target="_blank" class="btn btn-link btn-sm">查看报告</a>`;
                }
                tbody.innerHTML += `<tr>
                    <td>${task.id}</td>
                    <td>${task.name || ''}</td>
                    <td>${task.source_conn_name || (task.source_conn && task.source_conn.name) || ''}</td>
                    <td>${task.target_conn_name || (task.target_conn && task.target_conn.name) || ''}</td>
                    <td>
                        <span style="cursor:pointer;color:#007bff;" title="点击查看全部" onclick="showDescModal('${encodeURIComponent(desc)}')">${shortDesc}</span>
                    </td>
                    <td>${task.status}</td>
                    <td>
                        <button class="btn btn-success btn-sm me-1" onclick="executeTask(${task.id})">执行</button>
                        <button class="btn btn-primary btn-sm me-1" onclick="showEditTaskModal(
    ${task.id},
    '${encodeURIComponent(task.name||'')}',
    '${encodeURIComponent(task.description||'')}',
    '${encodeURIComponent(task.source_conn_name || (task.source_conn && task.source_conn.name) || '')}',
    '${encodeURIComponent(task.target_conn_name || (task.target_conn && task.target_conn.name) || '')}',
    '${task.source_conn_id}',
    '${task.target_conn_id}',
    '${task.config ? (typeof task.config === 'object' ? encodeURIComponent(JSON.stringify(task.config)) : encodeURIComponent(task.config)) : ''}'
)">修改</button>
                        <button class="btn btn-danger btn-sm" onclick="deleteTask(${task.id})">删除</button>
                        <button class="btn btn-secondary btn-sm" onclick="showTaskLogs(${task.id})">日志</button>
                        ${reportBtn}
                    </td>
                </tr>`;
            });
        }
        
        // 如果需要显示成功提示
        if (showToast) {
            showWarningToast('刷新成功', 'success');
        }
    } catch (err) {
        showWarningToast('请求异常：' + err, 'error');
    }
}

// 显示任务日志弹窗
async function showTaskLogs(taskId, page = 1, pageSize = 10) {
    if (!checkAuth()) return;
    try {
        // 修改API路径，使用task_logs而非logs
        const res = await fetch(`/api/v1/task_logs?task_id=${taskId}&page=${page}&page_size=${pageSize}`, {
            headers: getHeaders()
        });
        if (res.status === 401) {
            window.location.href = '/login';
            return;
        }
        const data = await res.json();
        // 修正tbody的ID引用，与HTML中的ID保持一致
        const tbody = document.getElementById('logTable');
        const modalTitle = document.getElementById('logModalLabel');
        if (modalTitle) {
            modalTitle.textContent = `任务 #${taskId} 日志`;
        }
        
        if (!data.items || data.items.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" class="text-center">暂无日志</td></tr>';
        } else {
            tbody.innerHTML = '';
            data.items.forEach(log => {
                const statusClass = log.status === 'success' ? 'text-success' : 
                                   log.status === 'failed' ? 'text-danger' : 
                                   log.status === 'running' ? 'text-primary' : '';
                // 添加查看报告按钮（如果有报告URL）
                let reportBtn = '';
                // 调试输出日志状态和报告URL
                console.log('Log status:', log.status, 'Result URL:', log.result_url);
                
                // 修改条件，不仅检查success状态，还检查completed状态
                if ((log.status === 'success' || log.status === 'completed') && log.result_url) {
                    reportBtn = `<a href="${log.result_url}" target="_blank" class="btn btn-link btn-sm">查看报告</a>`;
                }
                
                // 处理错误信息，使其可点击查看完整内容
                const errorMsg = log.error_message || '';
                const errorDisplay = errorMsg ? 
                    `<span class="error-message" title="点击查看完整错误信息" 
                           onclick="showErrorModal('${encodeURIComponent(errorMsg)}')"
                    >${errorMsg}</span>` : '';
                
                tbody.innerHTML += `<tr>
                    <td class="time-cell">${log.created_at}</td>
                    <td class="${statusClass}">${log.status}</td>
                    <td>${errorDisplay}</td>
                    <td>${reportBtn}</td>
                </tr>`;
            });
        }
        
        // 渲染分页
        renderLogPagination(taskId, page, pageSize, data.total);
        
        // 显示模态框
        const logModal = document.getElementById('logModal');
        if (logModal) {
            // 先获取已存在的Modal实例，如果没有才创建新的
            let modal = bootstrap.Modal.getInstance(logModal);
            if (!modal) {
                modal = new bootstrap.Modal(logModal);
                
                // 添加事件监听器，在模态框隐藏时清理内容和事件
                logModal.addEventListener('hidden.bs.modal', function () {
                    document.getElementById('logTable').innerHTML = '';
                    document.getElementById('logPagination').innerHTML = '';
                });
            }
            modal.show();
        }
    } catch (err) {
        showWarningToast('请求异常：' + err, 'error');
    }
}

const pageSize = 10;
function renderLogPagination(taskId, page, pageSize, total) {
    const totalPages = Math.ceil(total / pageSize);
    let html = '';
    if (totalPages <= 1) {
        document.getElementById('logPagination').innerHTML = '';
        return;
    }
    // 上一页
    html += `<li class="page-item${page === 1 ? ' disabled' : ''}"><a class="page-link" href="#" onclick="showTaskLogs(${taskId}, ${page-1}, ${pageSize});return false;">上一页</a></li>`;
    // 页码
    for (let i = 1; i <= totalPages; i++) {
        if (i === page || (i <= 2 || i > totalPages - 2 || Math.abs(i - page) <= 1)) {
            html += `<li class="page-item${i === page ? ' active' : ''}"><a class="page-link" href="#" onclick="showTaskLogs(${taskId}, ${i}, ${pageSize});return false;">${i}</a></li>`;
        } else if (i === 3 && page > 4) {
            html += '<li class="page-item disabled"><span class="page-link">...</span></li>';
        } else if (i === totalPages - 2 && page < totalPages - 3) {
            html += '<li class="page-item disabled"><span class="page-link">...</span></li>';
        }
    }
    // 下一页
    html += `<li class="page-item${page === totalPages ? ' disabled' : ''}"><a class="page-link" href="#" onclick="showTaskLogs(${taskId}, ${page+1}, ${pageSize});return false;">下一页</a></li>`;
    document.getElementById('logPagination').innerHTML = html;
}

// 显示错误信息弹窗
function showErrorModal(errorEncoded) {
    const errorMsg = decodeURIComponent(errorEncoded);
    document.getElementById('errorModalBody').textContent = errorMsg || '无错误信息';
    const modal = new bootstrap.Modal(document.getElementById('errorModal'));
    modal.show();
}

// 显示任务描述弹窗
function showDescModal(descEncoded) {
    const desc = decodeURIComponent(descEncoded);
    document.getElementById('descModalBody').textContent = desc || '无描述';
    const modal = new bootstrap.Modal(document.getElementById('descModal'));
    modal.show();
}

// 显示编辑任务弹窗
function showEditTaskModal(id, nameEncoded, descEncoded, sourceConnNameEncoded, targetConnNameEncoded, sourceConnId, targetConnId, configEncoded) {
    const name = decodeURIComponent(nameEncoded);
    const desc = decodeURIComponent(descEncoded);
    const sourceConnName = decodeURIComponent(sourceConnNameEncoded);
    const targetConnName = decodeURIComponent(targetConnNameEncoded);
    const config = configEncoded ? decodeURIComponent(configEncoded) : '';
    
    const form = document.getElementById('editForm');
    form.dataset.id = id;
    // 将数据库连接ID保存到表单的数据属性中，以便在提交时使用
    form.dataset.sourceConnId = sourceConnId;
    form.dataset.targetConnId = targetConnId;
    
    form.name.value = name;
    form.description.value = desc;
    form.source_conn_name.value = sourceConnName;
    form.target_conn_name.value = targetConnName;
    form.config.value = config;
    
    const modal = new bootstrap.Modal(document.getElementById('editTaskModal'));
    modal.show();
}

// 创建任务表单提交
if (document.getElementById('createForm')) {
    document.getElementById('createForm').onsubmit = async function(e) {
        e.preventDefault();
        if (!checkAuth()) return;
        const form = e.target;
        // 使用忽略配置模块收集配置
        const configObj = collectIgnoreConfig();
        const payload = {
            name: form.name.value,
            description: form.description.value,
            source_conn_id: parseInt(form.source_conn_id.value),
            target_conn_id: parseInt(form.target_conn_id.value),
            config: configObj
        };

        try {
            const res = await fetch('/api/v1/tasks', {
                method: 'POST',
                headers: getHeaders(),
                body: JSON.stringify(payload)
            });
            if (res.status === 401) {
                window.location.href = '/login';
                return;
            }
            let data;
            const contentType = res.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                data = await res.json();
            } else {
                data = await res.text();
            }
            if (res.ok) {
                showWarningToast('任务创建成功！', 'success');
                form.reset();
                // 关闭模态框
                let modalEl = document.getElementById('createTaskModal');
                if (modalEl) {
                    let modal = bootstrap.Modal.getInstance(modalEl);
                    if (!modal) modal = new bootstrap.Modal(modalEl);
                    modal.hide();
                }
                fetchTasks();
            } else {
                showWarningToast('创建失败：' + (typeof data === 'string' ? data : JSON.stringify(data)), 'error');
            }
        } catch (err) {
            showWarningToast('请求异常：' + err, 'error');
        }
    };
}

// 编辑任务表单提交
if (document.getElementById('editForm')) {
    document.getElementById('editForm').onsubmit = async function(e) {
        e.preventDefault();
        if (!checkAuth()) return;
        const form = e.target;
        const taskId = form.dataset.id;
        if (!taskId) {
            showWarningToast('任务ID不存在', 'error');
            return;
        }
        let config = form.config.value.trim();
        let configObj = null;
        if (config) {
            try {
                configObj = JSON.parse(config);
            } catch (e) {
                showWarningToast('任务配置必须是合法的JSON格式！', 'error');
                return;
            }
        }
        const payload = {
            name: form.name.value,
            description: form.description.value,
            source_conn_id: parseInt(form.dataset.sourceConnId),
            target_conn_id: parseInt(form.dataset.targetConnId),
            config: configObj
        };

        try {
            const res = await fetch(`/api/v1/tasks/${taskId}`, {
                method: 'PUT',
                headers: getHeaders(),
                body: JSON.stringify(payload)
            });
            if (res.status === 401) {
                window.location.href = '/login';
                return;
            }
            let data;
            const contentType = res.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                data = await res.json();
            } else {
                data = await res.text();
            }
            if (res.ok) {
                showWarningToast('任务更新成功！', 'success');
                // 关闭模态框
                let modalEl = document.getElementById('editTaskModal');
                if (modalEl) {
                    let modal = bootstrap.Modal.getInstance(modalEl);
                    if (!modal) modal = new bootstrap.Modal(modalEl);
                    modal.hide();
                }
                fetchTasks();
            } else {
                showWarningToast('更新失败：' + (typeof data === 'string' ? data : JSON.stringify(data)), 'error');
            }
        } catch (err) {
            showWarningToast('请求异常：' + err, 'error');
        }
    };
}

// 创建连接表单提交
if (document.getElementById('createConnectionForm')) {
    document.getElementById('createConnectionForm').onsubmit = async function(e) {
        e.preventDefault();
        if (!checkAuth()) return;
        const form = e.target;
        const payload = {
            name: form.name.value,
            host: form.host.value,
            port: String(form.port.value),
            database: form.database.value,
            user: form.user.value,
            password: form.password.value,
            description: form.description.value
        };
        try {
            const res = await fetch('/api/v1/connections', {
                method: 'POST',
                headers: getHeaders(),
                body: JSON.stringify(payload)
            });
            if (res.status === 401) {
                window.location.href = '/login';
                return;
            }
            let data;
            const contentType = res.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                data = await res.json();
            } else {
                data = await res.text();
            }
            if (res.ok) {
                showWarningToast('连接创建成功！', 'success');
                form.reset();
                form.port.value = 3306;
                // 关闭模态框
                let modalEl = document.getElementById('createConnModal');
                if (modalEl) {
                    let modal = bootstrap.Modal.getInstance(modalEl);
                    if (!modal) modal = new bootstrap.Modal(modalEl);
                    modal.hide();
                }
                loadDbConnections();
            } else {
                // 针对唯一约束错误友好提示
                if (typeof data === 'string' && data.includes('Duplicate entry')) {
                    showWarningToast('创建失败：连接名称已存在，请更换名称。', 'error');
                } else {
                    showWarningToast('创建失败：' + (typeof data === 'string' ? data : JSON.stringify(data)), 'error');
                }
            }
        } catch (err) {
            showWarningToast('请求异常：' + err, 'error');
        }
    };
}

// 删除任务
async function deleteTask(taskId) {
    // 使用美观的确认对话框替代原生 confirm
    const confirmed = await showConfirmDialog(
        '确定要删除该任务吗？此操作不可恢复。', 
        '删除任务', 
        '删除', 
        '取消',
        'btn-danger'
    );
    if (!confirmed) return;
    try {
        const res = await fetch(`/api/v1/tasks/${taskId}`, {
            method: 'DELETE',
            headers: getHeaders()
        });
        if (res.ok) {
            fetchTasks();
            showWarningToast('任务删除成功', 'success');
        } else {
            showWarningToast('删除失败', 'error');
        }
    } catch (err) {
        showWarningToast('请求异常：' + err, 'error');
    }
}

// 删除连接
async function deleteConnection(connId) {
    // 使用美观的确认对话框替代原生 confirm
    const confirmed = await showConfirmDialog(
        '确定要删除该连接吗？此操作不可恢复。', 
        '删除连接', 
        '删除', 
        '取消',
        'btn-danger'
    );
    if (!confirmed) return;
    try {
        const res = await fetch(`/api/v1/connections/${connId}`, {
            method: 'DELETE',
            headers: getHeaders()
        });
        if (res.ok) {
            loadDbConnections();
        } else {
            showWarningToast('删除失败', 'error');
        }
    } catch (err) {
        showWarningToast('请求异常：' + err, 'error');
    }
}

// 初始化加载
if (checkAuth()) {
    fetchTasks();
    loadDbConnections();
}

// 初始化刷新按钮
document.addEventListener('DOMContentLoaded', function() {
    // 获取刷新按钮元素
    const refreshBtn = document.getElementById('refreshTasksBtn');
    
    // 如果按钮存在，添加点击事件处理
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            // 调用fetchTasks函数刷新任务列表，并显示成功提示
            fetchTasks(true);
        });
    }
});
