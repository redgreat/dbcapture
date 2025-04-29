/**
 * 数据库比较报告页面的JavaScript逻辑
 */

// 页面加载完成后处理所有JSON内容和返回顶部按钮
document.addEventListener('DOMContentLoaded', function() {
    // 处理JSON内容
    handleJsonContent();
    
    // 初始化返回顶部按钮
    initBackToTopButton();
});

/**
 * 处理JSON内容，将Unicode转义序列转换为中文字符
 */
function handleJsonContent() {
    // 获取所有包含JSON数据的元素
    const jsonElements = document.querySelectorAll('.json-content');
    
    // 遍历每个元素并处理其JSON数据
    jsonElements.forEach(function(element) {
        try {
            // 从data-json属性获取JSON字符串
            const jsonData = element.getAttribute('data-json');
            if (jsonData) {
                // 解析JSON字符串为JavaScript对象（这会自动将Unicode转义序列转换为中文字符）
                const jsonObj = JSON.parse(jsonData);
                // 重新格式化为带缩进的JSON字符串
                const formattedJson = JSON.stringify(jsonObj, null, 2);
                // 设置元素内容
                element.textContent = formattedJson;
            }
        } catch (error) {
            console.error('解析JSON时出错:', error);
            element.textContent = '解析JSON数据时出错';
        }
    });
}

/**
 * 初始化返回顶部按钮
 */
function initBackToTopButton() {
    // 获取返回顶部按钮元素
    const backToTopBtn = document.getElementById('backToTop');
    
    if (backToTopBtn) {
        // 滚动事件监听器，控制按钮的显示和隐藏
        window.addEventListener('scroll', function() {
            // 当滚动超过300px时显示按钮
            if (window.pageYOffset > 300) {
                backToTopBtn.style.display = 'block';
            } else {
                backToTopBtn.style.display = 'none';
            }
        });
        
        // 点击返回顶部按钮的事件处理
        backToTopBtn.addEventListener('click', function() {
            // 平滑滚动到页面顶部
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }
}
