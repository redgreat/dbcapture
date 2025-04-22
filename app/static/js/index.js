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
        showWarningToast('请求异常：' + err);
    }
}

// 加载任务列表
async function fetchTasks() {
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
    } catch (err) {
        showWarningToast('请求异常：' + err);
    }
}

// 任务日志弹窗逻辑
async function showTaskLogs(taskId, page = 1, pageSize = 20) {
    const modal = new bootstrap.Modal(document.getElementById('logModal'));
    document.getElementById('logTable').innerHTML = '';
    modal.show();
    try {
        const res = await fetch(`/api/v1/task_logs?task_id=${taskId}&page=${page}&page_size=${pageSize}`);
        const result = await res.json();
        const items = result.items || [];
        const total = result.total || 0;
        if (!Array.isArray(items) || items.length === 0) {
            document.getElementById('logTable').innerHTML += '<tr><td colspan="4" class="text-center">暂无日志</td></tr>';
        } else {
            items.forEach(log => {
                const err = log.error_message ? log.error_message.replace(/'/g, '&apos;').replace(/"/g, '&quot;') : '';
                const reportBtn = (log.status === 'completed' && log.result_url) ? `<a href="${log.result_url}" target="_blank" class="btn btn-link btn-sm">查看报告</a>` : '';
                document.getElementById('logTable').innerHTML += `<tr>
                    <td>${log.created_at ? log.created_at.replace('T', ' ').slice(0, 19) : ''}</td>
                    <td>${log.status}</td>
                    <td title="${err}">${err.length > 20 ? err.slice(0, 20) + '...' : err}</td>
                    <td>${reportBtn}</td>
                </tr>`;
            });
        }
        renderLogPagination(taskId, page, pageSize, total);
    } catch (e) {
        document.getElementById('logTable').innerHTML = '<tr><td colspan="4" class="text-center text-danger">加载失败</td></tr>';
        document.getElementById('logPagination').innerHTML = '';
    }
}

window.showTaskLogs = showTaskLogs;
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


// 任务编辑弹窗逻辑
function showEditTaskModal(id, name, description, sourceConnName, targetConnName, sourceConnId, targetConnId, config) {
    const modal = new bootstrap.Modal(document.getElementById('editTaskModal'));
    const form = document.getElementById('editForm');
    form.dataset.id = id;
    form.name.value = decodeURIComponent(name || '');
    form.description.value = decodeURIComponent(description || '');
    // 修复：优先用 sourceConnName/targetConnName，否则尝试解析 JSON 对象
    let src = '';
    let tgt = '';
    try {
        src = sourceConnName ? decodeURIComponent(sourceConnName) : '';
        tgt = targetConnName ? decodeURIComponent(targetConnName) : '';
    } catch {}
    form.source_conn_name.value = src;
    form.target_conn_name.value = tgt;
    // 缓存ID
    form.dataset.sourceConnId = sourceConnId || '';
    form.dataset.targetConnId = targetConnId || '';
    // 配置赋值
    let configStr = '';
    if (config && config !== 'null') {
        if (typeof config === 'object') {
            configStr = JSON.stringify(config, null, 2);
        } else {
            try {
                configStr = decodeURIComponent(config);
            } catch {
                configStr = config;
            }
        }
    }
    form.config.value = configStr;
    modal.show();
}

// 编辑任务表单提交
if (document.getElementById('editForm')) {
    document.getElementById('editForm').onsubmit = async function(e) {
        e.preventDefault();
        const id = this.dataset.id;
        let config = this.config.value.trim();
        let configObj = null;
        if (config) {
            try {
                configObj = JSON.parse(config);
            } catch (e) {
                showWarningToast('任务配置必须是合法的JSON格式！');
                return;
            }
        }
        const payload = {
            name: this.name.value.trim(),
            description: this.description.value.trim(),
            source_conn_id: this.dataset.sourceConnId,
            target_conn_id: this.dataset.targetConnId,
            config: configObj
        };
        try {
            const res = await fetch(`/api/v1/tasks/${id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            if (res.status === 400) {
                const data = await res.json();
                showWarningToast(data.detail || '任务名称已存在');
                return;
            }
            if (!res.ok) throw new Error('修改失败');
            bootstrap.Modal.getInstance(document.getElementById('editTaskModal')).hide();
            fetchTasks();
            showWarningToast('任务修改成功');
        } catch (e) {
            showWarningToast('修改失败：' + (e.message || e));
        }
    }
}

// 任务描述弹窗逻辑
function showDescModal(desc) {
    const modalBody = document.getElementById('descModalBody');
    modalBody.textContent = decodeURIComponent(desc);
    const modal = new bootstrap.Modal(document.getElementById('descModal'));
    modal.show();
}

// 创建任务表单提交
if (document.getElementById('createForm')) {
    document.getElementById('createForm').onsubmit = async function(e) {
        e.preventDefault();
        if (!checkAuth()) return;
        const form = e.target;
        let config = form.config.value.trim();
        let configObj = null;
        if (config) {
            try {
                configObj = JSON.parse(config);
            } catch (e) {
                showWarningToast('任务配置必须是合法的JSON格式！');
                return;
            }
        }
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
                showWarningToast('任务创建成功！');
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
                showWarningToast('创建失败：' + (typeof data === 'string' ? data : JSON.stringify(data)));
            }
        } catch (err) {
            showWarningToast('请求异常：' + err);
        }
    };
}

// 创建连接表单提交
if (document.getElementById('createConnectionForm')) {
    // 每次打开模态框时重置表单
    const modalEl = document.getElementById('createConnectionModal');
    if (modalEl) {
        modalEl.addEventListener('show.bs.modal', function () {
            const form = document.getElementById('createConnectionForm');
            if (form) {
                form.reset();
                form.port.value = 3306;
            }
        });
    }
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
                showWarningToast('连接创建成功！');
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
                    showWarningToast('创建失败：连接名称已存在，请更换名称。');
                } else {
                    showWarningToast('创建失败：' + (typeof data === 'string' ? data : JSON.stringify(data)));
                }
            }
        } catch (err) {
            showWarningToast('请求异常：' + err);
        }
    };
}

// 删除任务
async function deleteTask(taskId) {
    if (!confirm('确定要删除该任务吗？')) return;
    try {
        const res = await fetch(`/api/v1/tasks/${taskId}`, {
            method: 'DELETE',
            headers: getHeaders()
        });
        if (res.ok) {
            fetchTasks();
            showWarningToast('任务删除成功');
        } else {
            showWarningToast('删除失败');
        }
    } catch (err) {
        showWarningToast('请求异常：' + err);
    }
}

// 删除连接
async function deleteConnection(connId) {
    if (!confirm('确定要删除该连接吗？')) return;
    try {
        const res = await fetch(`/api/v1/connections/${connId}`, {
            method: 'DELETE',
            headers: getHeaders()
        });
        if (res.ok) {
            loadDbConnections();
        } else {
            showWarningToast('删除失败');
        }
    } catch (err) {
        showWarningToast('请求异常：' + err);
    }
}

// 初始化加载
if (checkAuth()) {
    fetchTasks();
    loadDbConnections();
}
