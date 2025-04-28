/**
 * 通用确认对话框
 * 用于替代浏览器原生的confirm对话框，提供更美观的UI
 */

// 确认对话框实例
let confirmModalInstance = null;

/**
 * 显示确认对话框
 * @param {string} message 确认消息
 * @param {string} title 对话框标题，可选
 * @param {string} confirmBtnText 确认按钮文本，可选
 * @param {string} cancelBtnText 取消按钮文本，可选
 * @param {string} confirmBtnClass 确认按钮样式类，可选
 * @returns {Promise<boolean>} 用户选择结果，确认返回true，取消返回false
 */
function showConfirmDialog(message, title = '操作确认', confirmBtnText = '确定', cancelBtnText = '取消', confirmBtnClass = 'btn-primary') {
    return new Promise((resolve) => {
        // 获取确认对话框元素
        const modalEl = document.getElementById('confirmModal');
        if (!modalEl) {
            console.error('确认对话框元素不存在');
            // 降级使用原生confirm
            resolve(confirm(message));
            return;
        }

        // 设置对话框内容
        document.getElementById('confirmModalLabel').textContent = title;
        document.getElementById('confirmMessage').textContent = message;
        
        // 获取按钮元素
        const confirmBtn = document.getElementById('confirmButton');
        const cancelBtn = modalEl.querySelector('.modal-footer .btn-secondary');
        
        // 设置按钮文本
        confirmBtn.textContent = confirmBtnText;
        if (cancelBtn) cancelBtn.textContent = cancelBtnText;
        
        // 设置确认按钮样式
        confirmBtn.className = `btn ${confirmBtnClass}`;
        
        // 移除之前的事件监听器
        const newConfirmBtn = confirmBtn.cloneNode(true);
        confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);
        
        // 添加确认按钮点击事件
        newConfirmBtn.addEventListener('click', function() {
            if (confirmModalInstance) {
                confirmModalInstance.hide();
            }
            resolve(true);
        });
        
        // 添加取消按钮和关闭事件
        modalEl.addEventListener('hidden.bs.modal', function onHidden() {
            modalEl.removeEventListener('hidden.bs.modal', onHidden);
            resolve(false);
        }, { once: true });
        
        // 显示对话框
        if (!confirmModalInstance) {
            confirmModalInstance = new bootstrap.Modal(modalEl);
        }
        confirmModalInstance.show();
    });
}
