/**
 * 忽略配置处理模块
 * 用于处理数据库对象（表、视图、函数、存储过程、触发器）的忽略配置
 */

// 收集所有忽略配置并转换为JSON格式
function collectIgnoreConfig() {
    const config = {
        ignored_tables: {
            exact: [],
            prefixes: []
        },
        ignored_views: {
            exact: []
        },
        ignored_procedures: {
            exact: []
        },
        ignored_functions: {
            exact: []
        },
        ignored_triggers: {
            exact: []
        }
    };

    // 获取所有忽略配置输入框
    document.querySelectorAll('.ignore-config').forEach(textarea => {
        const type = textarea.dataset.type;
        const mode = textarea.dataset.mode;
        const value = textarea.value.trim();
        
        if (value) {
            // 按行分割，过滤空行
            const items = value.split('\n')
                .map(item => item.trim())
                .filter(item => item);
            
            if (items.length > 0) {
                if (type === 'table' && mode === 'exact') {
                    config.ignored_tables.exact = items;
                } else if (type === 'table' && mode === 'prefix') {
                    config.ignored_tables.prefixes = items;
                } else if (type === 'view' && mode === 'exact') {
                    config.ignored_views.exact = items;
                } else if (type === 'procedure' && mode === 'exact') {
                    config.ignored_procedures.exact = items;
                } else if (type === 'function' && mode === 'exact') {
                    config.ignored_functions.exact = items;
                } else if (type === 'trigger' && mode === 'exact') {
                    config.ignored_triggers.exact = items;
                }
            }
        }
    });

    // 清理空数组，减小JSON体积
    if (config.ignored_tables.exact.length === 0) delete config.ignored_tables.exact;
    if (config.ignored_tables.prefixes.length === 0) delete config.ignored_tables.prefixes;
    if (Object.keys(config.ignored_tables).length === 0) delete config.ignored_tables;
    
    if (config.ignored_views.exact.length === 0) delete config.ignored_views;
    if (config.ignored_procedures.exact.length === 0) delete config.ignored_procedures;
    if (config.ignored_functions.exact.length === 0) delete config.ignored_functions;
    if (config.ignored_triggers.exact.length === 0) delete config.ignored_triggers;

    return Object.keys(config).length > 0 ? config : null;
}

// 从JSON配置中填充忽略配置表单
function fillIgnoreConfigForm(configJson) {
    if (!configJson) return;
    
    try {
        const config = typeof configJson === 'string' ? JSON.parse(configJson) : configJson;
        
        // 填充表忽略配置
        if (config.ignored_tables) {
            if (config.ignored_tables.exact && Array.isArray(config.ignored_tables.exact)) {
                document.getElementById('ignoredTables').value = config.ignored_tables.exact.join('\n');
            }
            if (config.ignored_tables.prefixes && Array.isArray(config.ignored_tables.prefixes)) {
                document.getElementById('ignoredTablePrefixes').value = config.ignored_tables.prefixes.join('\n');
            }
        }
        
        // 填充视图忽略配置
        if (config.ignored_views && config.ignored_views.exact && Array.isArray(config.ignored_views.exact)) {
            document.getElementById('ignoredViews').value = config.ignored_views.exact.join('\n');
        }
        
        // 填充存储过程忽略配置
        if (config.ignored_procedures && config.ignored_procedures.exact && Array.isArray(config.ignored_procedures.exact)) {
            document.getElementById('ignoredProcedures').value = config.ignored_procedures.exact.join('\n');
        }
        
        // 填充函数忽略配置
        if (config.ignored_functions && config.ignored_functions.exact && Array.isArray(config.ignored_functions.exact)) {
            document.getElementById('ignoredFunctions').value = config.ignored_functions.exact.join('\n');
        }
        
        // 填充触发器忽略配置
        if (config.ignored_triggers && config.ignored_triggers.exact && Array.isArray(config.ignored_triggers.exact)) {
            document.getElementById('ignoredTriggers').value = config.ignored_triggers.exact.join('\n');
        }
    } catch (e) {
        console.error('解析配置JSON失败:', e);
    }
}

// 在表单提交前处理忽略配置
function setupIgnoreConfigHandling() {
    // 为创建任务表单添加提交前处理
    const createForm = document.getElementById('createForm');
    if (createForm) {
        createForm.addEventListener('submit', function(e) {
            // 收集忽略配置并设置到隐藏字段
            const config = collectIgnoreConfig();
            document.getElementById('configJson').value = config ? JSON.stringify(config) : '';
        });
    }
    
    // 为编辑任务表单添加提交前处理
    const editForm = document.getElementById('editForm');
    if (editForm) {
        editForm.addEventListener('submit', function(e) {
            // 收集忽略配置并设置到隐藏字段
            const config = collectIgnoreConfig();
            // 编辑表单中使用name="config"而非单独的隐藏字段
            const configField = editForm.querySelector('[name="config"]');
            if (configField) {
                configField.value = config ? JSON.stringify(config) : '';
            }
        });
    }
}

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    setupIgnoreConfigHandling();
});
