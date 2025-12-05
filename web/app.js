// ============ 本地调试 ============
const TEST_MODE = false; // 设为 true 从 GitHub 远程获取数据，false 使用本地数据
const TEST_DATA_URL = 'https://raw.githubusercontent.com/yuexps/2FStore/refs/heads/main/data/app_details.json';
const TEST_FNPACK_URL = 'https://raw.githubusercontent.com/yuexps/2FStore/refs/heads/main/data/fnpack_details.json';
const TEST_VERSION_URL = 'https://raw.githubusercontent.com/yuexps/2FStore/refs/heads/main/data/version.json';

// GitHub 代理地址列表
const PROXY_OPTIONS = [
    { value: '', label: '无加速' },
    { value: 'https://github.akams.cn/', label: 'github.akams.cn' },
    { value: 'https://gh-proxy.org/', label: 'gh-proxy.org' },
    { value: 'https://ghfast.top/', label: 'ghfast.top' },
    { value: 'custom', label: '自定义' }
];
// ==================================

    // 全局变量
    let appsData = [];
    let filteredApps = [];
    let currentCategory = 'all';
    let currentSort = 'name';
    let githubProxy = ''; // 全局变量存储GitHub代理URL

    // 分页相关变量
    // 当前页码，默认为 1。用户点击分页按钮时会更新此值
    let currentPage = 1;
    // 每页显示的应用数量，可根据需要调整
    // 默认分页数量设置为 12，按需调整此常量即可
    const APPS_PER_PAGE = 12;

    // 分页容器元素
    const paginationEl = document.getElementById('pagination');

// Bing 每日图片 API
const BING_API = 'https://bing.biturl.top/?resolution=1920&format=json&index=0&mkt=zh-CN';

// 安全 HTML 标签白名单
const ALLOWED_TAGS = [
    'b', 'i', 'strong', 'em', 'br', 'a', 'p', 'ul', 'ol', 'li', 
    'code', 'pre', 'span', 'div', 'blockquote', 'hr',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'sub', 'sup', 'mark'
];
const ALLOWED_ATTRS = {
    'a': ['href', 'target', 'rel'],
    'span': ['class', 'style'],
    'div': ['class', 'style'],
    'p': ['class', 'style'],
    'code': ['class'],
    'pre': ['class'],
    'blockquote': ['class', 'style'],
    'h1': ['class', 'style'],
    'h2': ['class', 'style'],
    'h3': ['class', 'style'],
    'h4': ['class', 'style'],
    'h5': ['class', 'style'],
    'h6': ['class', 'style']
};

// 安全的 CSS 属性白名单（防止注入攻击）
const ALLOWED_STYLES = [
    'color', 'background-color', 'font-size', 'font-weight', 'font-style',
    'text-align', 'text-decoration', 'line-height', 'margin', 'padding',
    'margin-top', 'margin-bottom', 'margin-left', 'margin-right',
    'padding-top', 'padding-bottom', 'padding-left', 'padding-right',
    'border', 'border-radius', 'opacity'
];

/**
 * 过滤 style 属性，只保留安全的 CSS 属性
 */
function sanitizeStyle(styleString) {
    if (!styleString) return '';
    
    const safeStyles = [];
    const styles = styleString.split(';');
    
    for (const style of styles) {
        const [prop, value] = style.split(':').map(s => s.trim().toLowerCase());
        if (prop && value && ALLOWED_STYLES.includes(prop)) {
            // 检查值中是否包含危险内容（如 url(), expression(), javascript:）
            if (!value.includes('url(') && 
                !value.includes('expression(') && 
                !value.includes('javascript:')) {
                safeStyles.push(`${prop}: ${value}`);
            }
        }
    }
    
    return safeStyles.join('; ');
}

/**
 * 安全的 HTML 过滤函数
 * 只允许白名单中的标签和属性，防止 XSS 攻击
 */
function sanitizeHtml(html) {
    if (!html || typeof html !== 'string') return '';
    
    // 创建临时 DOM 解析 HTML
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = html;
    
    // 递归清理节点
    function cleanNode(node) {
        const childNodes = Array.from(node.childNodes);
        
        for (const child of childNodes) {
            if (child.nodeType === Node.TEXT_NODE) {
                // 文本节点保留
                continue;
            } else if (child.nodeType === Node.ELEMENT_NODE) {
                const tagName = child.tagName.toLowerCase();
                
                if (!ALLOWED_TAGS.includes(tagName)) {
                    // 不在白名单中的标签，用其文本内容替换
                    const textNode = document.createTextNode(child.textContent);
                    node.replaceChild(textNode, child);
                } else {
                    // 清理属性
                    const allowedAttrs = ALLOWED_ATTRS[tagName] || [];
                    const attrs = Array.from(child.attributes);
                    
                    for (const attr of attrs) {
                        if (!allowedAttrs.includes(attr.name)) {
                            child.removeAttribute(attr.name);
                        } else if (attr.name === 'href') {
                            // 检查 href 是否安全（只允许 http/https/mailto）
                            const href = attr.value.toLowerCase().trim();
                            if (!href.startsWith('http://') && 
                                !href.startsWith('https://') && 
                                !href.startsWith('mailto:')) {
                                child.removeAttribute('href');
                            }
                        } else if (attr.name === 'style') {
                            // 过滤 style 属性
                            const safeStyle = sanitizeStyle(attr.value);
                            if (safeStyle) {
                                child.setAttribute('style', safeStyle);
                            } else {
                                child.removeAttribute('style');
                            }
                        }
                    }
                    
                    // 为外部链接添加安全属性
                    if (tagName === 'a') {
                        child.setAttribute('target', '_blank');
                        child.setAttribute('rel', 'noopener noreferrer');
                    }
                    
                    // 递归清理子节点
                    cleanNode(child);
                }
            } else {
                // 其他类型节点（如注释）直接移除
                node.removeChild(child);
            }
        }
    }
    
    cleanNode(tempDiv);
    return tempDiv.innerHTML;
}

// DOM元素
const appList = document.getElementById('app-list');
const appDetail = document.getElementById('app-detail');
const appDetailContent = document.getElementById('app-detail-content');
const backBtn = document.getElementById('back-btn');
const searchInput = document.getElementById('search-input');
const searchBtn = document.getElementById('search-btn');
const categoryList = document.getElementById('category-list');
const sortSelect = document.getElementById('sort-select');
const submitAppBtn = document.getElementById('submit-app-btn');
const submitModal = document.getElementById('submit-modal');
const closeModal = document.querySelector('.miuix-modal-close');
const proxySelect = document.getElementById('proxy-select');
const customProxyContainer = document.getElementById('custom-proxy-container');
const customProxyInput = document.getElementById('custom-proxy-input');
const appCountEl = document.getElementById('app-count');
const menuToggle = document.getElementById('menu-toggle');
const sidebar = document.querySelector('.miuix-sidebar');

// 初始化应用
document.addEventListener('DOMContentLoaded', () => {
    loadProxySetting(); // 加载保存的代理设置
    loadBingBackground(); // 加载 Bing 每日背景
    loadAppsData();
    setupEventListeners();
});

// 加载 Bing 每日背景图片
async function loadBingBackground() {
    try {
        // 检查本地缓存
        const cached = localStorage.getItem('bingBackground');
        const cachedDate = localStorage.getItem('bingBackgroundDate');
        const today = new Date().toDateString();
        
        if (cached && cachedDate === today) {
            document.body.style.backgroundImage = `url(${cached})`;
            return;
        }
        
        const response = await fetch(BING_API);
        if (response.ok) {
            const data = await response.json();
            if (data.url) {
                document.body.style.backgroundImage = `url(${data.url})`;
                // 缓存到本地
                localStorage.setItem('bingBackground', data.url);
                localStorage.setItem('bingBackgroundDate', today);
            }
        }
    } catch (error) {
        console.warn('加载 Bing 背景图片失败:', error);
        // 失败时使用默认背景色
    }
}

// 设置事件监听器
function setupEventListeners() {
    backBtn.addEventListener('click', showAppList);
    searchBtn.addEventListener('click', handleSearch);
    searchInput.addEventListener('keyup', (e) => {
        if (e.key === 'Enter') handleSearch();
    });
    sortSelect.addEventListener('change', handleSort);
    submitAppBtn.addEventListener('click', () => {
        submitModal.classList.remove('hidden');
    });
    closeModal.addEventListener('click', () => {
        submitModal.classList.add('hidden');
    });
    
    // 汉堡菜单切换侧边栏
    menuToggle.addEventListener('click', () => {
        sidebar.classList.toggle('collapsed');
        document.documentElement.classList.toggle('sidebar-collapsed');
        // 保存状态到 localStorage
        localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));
    });
    
    // 同步侧边栏状态（从 html 类同步到 sidebar 元素）
    if (document.documentElement.classList.contains('sidebar-collapsed')) {
        sidebar.classList.add('collapsed');
    }
    
    // 监听代理设置变化
    proxySelect.addEventListener('change', handleProxyChange);
    
    // 监听自定义代理输入框变化
    customProxyInput.addEventListener('blur', handleCustomProxyChange);
    customProxyInput.addEventListener('keyup', (e) => {
        if (e.key === 'Enter') handleCustomProxyChange();
    });
    
    // 点击模态框背景关闭
    submitModal.addEventListener('click', (e) => {
        if (e.target === submitModal) {
            submitModal.classList.add('hidden');
        }
    });
    
    // 分类点击事件
    categoryList.addEventListener('click', (e) => {
        const listItem = e.target.closest('.miuix-list-item');
        if (listItem) {
            // 移除所有活动状态
            document.querySelectorAll('.miuix-list-item').forEach(item => {
                item.classList.remove('active');
            });
            
            // 添加活动状态到当前项
            listItem.classList.add('active');
            
            // 设置当前分类并过滤应用
            currentCategory = listItem.dataset.category;
            filterApps();
        }
    });
    
    // 键盘快捷键：ESC 关闭模态框和详情
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            if (!submitModal.classList.contains('hidden')) {
                submitModal.classList.add('hidden');
            } else if (!appDetail.classList.contains('hidden')) {
                showAppList();
            }
        }
    });
}

// 处理代理设置变化
function handleProxyChange() {
    if (proxySelect.value === 'custom') {
        customProxyContainer.classList.remove('hidden');
        // 如果之前有保存的自定义代理，则加载它
        const savedCustomProxy = localStorage.getItem('customGithubProxy');
        if (savedCustomProxy) {
            customProxyInput.value = savedCustomProxy;
            githubProxy = savedCustomProxy; // 确保全局变量也被设置
        }
    } else {
        customProxyContainer.classList.add('hidden');
        githubProxy = proxySelect.value;
        // 保存代理设置到localStorage
        localStorage.setItem('githubProxy', githubProxy);
        // 重新加载应用数据以应用新的代理设置
        loadAppsData();
    }
}

// 处理自定义代理变化
function handleCustomProxyChange() {
    let customProxy = customProxyInput.value.trim();
    
    // 验证URL格式
    if (customProxy && !customProxy.startsWith('http://') && !customProxy.startsWith('https://')) {
        alert('请输入有效的URL，必须以 http:// 或 https:// 开头');
        return;
    }
    
    // 确保URL以斜杠结尾
    if (customProxy && !customProxy.endsWith('/')) {
        customProxy += '/';
    }
    
    githubProxy = customProxy;
    customProxyInput.value = customProxy;
    
    // 保存代理设置到localStorage
    localStorage.setItem('githubProxy', 'custom');
    localStorage.setItem('customGithubProxy', customProxy);
    
    // 重新加载应用数据以应用新的代理设置
    loadAppsData();
}

// 初始化代理选择器选项
function initProxyOptions() {
    proxySelect.innerHTML = PROXY_OPTIONS.map(option => 
        `<option value="${option.value}">${option.label}</option>`
    ).join('');
}

// 加载保存的代理设置
function loadProxySetting() {
    initProxyOptions(); // 先初始化选项
    const savedProxy = localStorage.getItem('githubProxy');
    if (savedProxy) {
        githubProxy = savedProxy; // 确保全局变量被设置
        if (savedProxy === 'custom') {
            proxySelect.value = 'custom';
            customProxyContainer.classList.remove('hidden');
            const savedCustomProxy = localStorage.getItem('customGithubProxy');
            if (savedCustomProxy) {
                customProxyInput.value = savedCustomProxy;
                githubProxy = savedCustomProxy; // 确保全局变量也被设置
            }
        } else {
            proxySelect.value = githubProxy;
        }
    }
}

// 通过代理URL处理函数
function getProxyUrl(url) {
    if (!githubProxy || !url) return url;
    // 只对GitHub相关URL应用代理
    if (url.includes('github.com') || url.includes('githubusercontent.com')) {
        return githubProxy + url;
    }
    return url;
}

// 提取所有分类
function extractCategories() {
    const categories = new Set(['all']);
    
    appsData.forEach(app => {
        if (app.category) {
            categories.add(app.category);
        }
    });
    
    // 更新分类列表
    categoryList.innerHTML = '';
    categories.forEach(category => {
        const li = document.createElement('li');
        li.className = 'miuix-list-item';
        li.dataset.category = category;
        
        const span = document.createElement('span');
        span.className = 'miuix-list-item-text';
        span.textContent = category === 'all' ? '全部' : getCategoryDisplayName(category);
        
        li.appendChild(span);
        
        if (category === currentCategory) {
            li.classList.add('active');
        }
        
        categoryList.appendChild(li);
    });
}

// 获取分类显示名称
function getCategoryDisplayName(category) {
    const categoryNames = {
        'uncategorized': '未分类',
        'utility': '工具',
        'media': '媒体',
        'network': '网络',
        'development': '开发',
        'system': '系统',
        'productivity': '生产力',
        'games': '游戏'
    };
    
    return categoryNames[category] || category;
}

// 过滤应用
function filterApps() {
    // 先按分类过滤
    if (currentCategory === 'all') {
        filteredApps = [...appsData];
    } else {
        filteredApps = appsData.filter(app => app.category === currentCategory);
    }
    
    // 再按搜索关键词过滤
    const searchTerm = searchInput.value.trim().toLowerCase();
    if (searchTerm) {
        filteredApps = filteredApps.filter(app => 
            app.name.toLowerCase().includes(searchTerm) ||
            app.description.toLowerCase().includes(searchTerm) ||
            app.author.toLowerCase().includes(searchTerm)
        );
    }
    
    // 最后排序
    sortApps();
    
        // 显示应用列表
        // 筛选或排序后返回第一页
        currentPage = 1;
        renderAppList();
}

// 排序应用
function sortApps() {
    switch (currentSort) {
        case 'name':
            filteredApps.sort((a, b) => a.name.localeCompare(b.name));
            break;
        case 'stars':
            filteredApps.sort((a, b) => (b.stars || 0) - (a.stars || 0));
            break;
        case 'updated':
            filteredApps.sort((a, b) => new Date(b.lastUpdate) - new Date(a.lastUpdate));
            break;
    }
}

// 处理搜索
function handleSearch() {
    filterApps();
}

// 处理排序
function handleSort() {
    currentSort = sortSelect.value;
    filterApps();
}

// 渲染应用列表
function renderAppList() {
    // 更新应用计数
    if (appCountEl) {
        appCountEl.textContent = `共 ${filteredApps.length} 个应用`;
    }
    
    if (filteredApps.length === 0) {
        appList.innerHTML = `
            <div class="empty-state">
                <svg class="empty-icon" xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="11" cy="11" r="8"></circle>
                    <path d="m21 21-4.35-4.35"></path>
                    <path d="M8 8l6 6"></path>
                    <path d="M14 8l-6 6"></path>
                </svg>
                <p class="empty-title">没有找到匹配的应用</p>
                <p class="empty-desc">试试其他搜索关键词或分类</p>
            </div>
        `;
        return;
    }
    
    // 使用分批渲染提高性能
    appList.innerHTML = '';
    const fragment = document.createDocumentFragment();

    // 计算当前页需要渲染的应用索引区间
    const startIndex = (currentPage - 1) * APPS_PER_PAGE;
    const endIndex = startIndex + APPS_PER_PAGE;
    const pageApps = filteredApps.slice(startIndex, endIndex);

    pageApps.forEach((app, index) => {
        const cardHtml = createAppCard(app);
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = cardHtml;
        const cardElement = tempDiv.firstElementChild;

        // 添加渐入动画
        cardElement.style.opacity = '0';
        cardElement.style.transform = 'translateY(20px)';
        cardElement.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
        cardElement.style.transitionDelay = `${index * 50}ms`;

        fragment.appendChild(cardElement);

        cardElement.addEventListener('click', () => {
            const appId = cardElement.dataset.appId;
            showAppDetail(appId);
        });
    });

    appList.appendChild(fragment);

    // 渲染分页导航
    renderPagination();

    // 触发重新排以开始动画
    requestAnimationFrame(() => {
        document.querySelectorAll('.app-card').forEach(card => {
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        });
    });
}

// 分页：跳转至指定页码并重新渲染列表
function goToPage(page) {
    const totalPages = Math.ceil(filteredApps.length / APPS_PER_PAGE);
    if (page < 1) page = 1;
    if (page > totalPages) page = totalPages;
    // 如果目标页与当前页相同，则无需刷新
    if (page === currentPage) return;
    currentPage = page;
    renderAppList();
}

// 渲染分页按钮，根据应用数量自动生成页码
function renderPagination() {
    // 如果不存在容器或未定义则跳过
    if (!paginationEl) return;
    const totalPages = Math.ceil(filteredApps.length / APPS_PER_PAGE);
    // 当只有一页或没有应用时，不显示分页
    if (totalPages <= 1) {
        paginationEl.innerHTML = '';
        return;
    }
    let html = '';
    // 上一页按钮
    const prevDisabled = currentPage === 1 ? 'disabled' : '';
    html += `<button class="page-btn prev-btn" data-page="${currentPage - 1}" ${prevDisabled}>&laquo;</button>`;

    // 工具函数：生成页码按钮
    const appendPageBtn = (page) => {
        const active = page === currentPage ? 'active' : '';
        html += `<button class="page-btn ${active}" data-page="${page}">${page}</button>`;
    };

    if (totalPages <= 7) {
        // 页数较少时直接显示所有页码
        for (let i = 1; i <= totalPages; i++) {
            appendPageBtn(i);
        }
    } else {
        // 显示首尾页和当前页附近页码，中间使用省略号
        appendPageBtn(1);
        // 在当前页前添加省略号
        if (currentPage > 3) {
            html += `<span class="page-ellipsis">...</span>`;
        }
        // 计算当前页附近的显示范围
        const start = Math.max(2, currentPage - 1);
        const end = Math.min(totalPages - 1, currentPage + 1);
        for (let i = start; i <= end; i++) {
            appendPageBtn(i);
        }
        // 在当前页后添加省略号
        if (currentPage < totalPages - 2) {
            html += `<span class="page-ellipsis">...</span>`;
        }
        appendPageBtn(totalPages);
    }

    // 下一页按钮
    const nextDisabled = currentPage === totalPages ? 'disabled' : '';
    html += `<button class="page-btn next-btn" data-page="${currentPage + 1}" ${nextDisabled}>&raquo;</button>`;

    paginationEl.innerHTML = html;

    // 为所有页码按钮绑定点击事件
    Array.from(paginationEl.querySelectorAll('.page-btn')).forEach(btn => {
        btn.addEventListener('click', () => {
            const page = parseInt(btn.getAttribute('data-page'), 10);
            if (!isNaN(page)) {
                goToPage(page);
            }
        });
    });
}

// 获取开发者链接（优先使用 author_url，否则从仓库 URL 提取）
function getAuthorUrl(app) {
    if (app.author_url) return app.author_url;
    // 从 GitHub 仓库 URL 提取所有者链接
    if (app.repository && app.repository.includes('github.com')) {
        const match = app.repository.match(/github\.com\/([^\/]+)/);
        if (match) {
            return `https://github.com/${match[1]}`;
        }
    }
    return null;
}

// 创建应用卡片
function createAppCard(app) {
    const initial = app.name.charAt(0).toUpperCase();
    const iconUrl = app.iconUrl || '';
    let sourceBadge = '';
    if (app.source) {
        sourceBadge = `<span class="app-source-badge store-${app.source.toLowerCase()}">${app.source}</span>`;
    }
    
    const authorUrl = getAuthorUrl(app);
    
    // 图片错误处理：失败时显示首字母
    const imgErrorHandler = `onerror="this.style.display='none';this.parentElement.querySelector('.img-placeholder').style.display='flex';"`;
    
    return `
        <div class="miuix-card app-card" data-app-id="${app.id}">
            <div class="app-card-header">
                <div class="app-icon">
                    ${iconUrl ? `<img src="${getProxyUrl(iconUrl)}" alt="${app.name}" ${imgErrorHandler} style="width: 100%; height: 100%; object-fit: cover; border-radius: 12px;"><span class="img-placeholder" style="display:none;">${initial}</span>` : initial}
                </div>
                <div class="app-info">
                    <div class="app-name">${app.name}</div>
                    <div class="app-author">${authorUrl ? `<a href="${authorUrl}" target="_blank" class="author-link" onclick="event.stopPropagation()">${app.author}</a>` : `<span>${app.author}</span>`}</div>
                </div>
            </div>
            <div class="app-card-body">
                <div class="app-description">${sanitizeHtml(app.description) || '暂无描述'}</div>
                <div class="app-meta">
                    <span>⭐ ${app.stars || 0}</span>
                    <span>🍴 ${app.forks || 0}</span>
                    <span>📦 ${app.version || '1.0.0'}</span>
                    <span>🕐 ${formatDate(app.lastUpdate)}</span>
                    ${sourceBadge}
                </div>
            </div>
        </div>
    `;
}

// 显示应用详情
function showAppDetail(appId) {
    const app = appsData.find(a => a.id === appId);
    if (!app) return;
    
    const initial = app.name.charAt(0).toUpperCase();
    const iconUrl = app.iconUrl || '';
    let sourceBadge = '';
    if (app.source) {
        sourceBadge = `<span class="app-source-badge store-${app.source.toLowerCase()}">${app.source}</span>`;
    }
    
    const authorUrl = getAuthorUrl(app);
    
    // 图片错误处理
    const imgErrorHandler = `onerror="this.style.display='none';this.parentElement.querySelector('.img-placeholder').style.display='flex';"`;
    
    appDetailContent.innerHTML = `
        <div class="app-detail-container">
            <div class="app-detail-header">
                <div class="app-detail-icon">
                    ${iconUrl ? `<img src="${getProxyUrl(iconUrl)}" alt="${app.name}" ${imgErrorHandler} style="width: 100%; height: 100%; object-fit: cover; border-radius: 16px;"><span class="img-placeholder" style="display:none;">${initial}</span>` : initial}
                </div>
                <div class="app-detail-info">
                    <div class="app-detail-name">${app.name} ${sourceBadge}</div>
                    <div class="app-detail-author">${authorUrl ? `<a href="${authorUrl}" target="_blank" class="author-link">${app.author}</a>` : `<span>${app.author}</span>`}</div>
                    <div class="app-detail-stats">
                        <span>⭐ ${app.stars || 0}</span>
                        <span>🍴 ${app.forks || 0}</span>
                        <span>🏷️ ${getCategoryDisplayName(app.category || 'uncategorized')}</span>
                        <span>📦 ${app.version || '1.0.0'}</span>
                    </div>
                </div>
            </div>
            
            <div class="app-detail-description">
                ${sanitizeHtml(app.description) || '暂无描述'}
            </div>
            
            <div class="app-detail-actions">
                ${app.downloadUrl ? `<a href="${getProxyUrl(app.downloadUrl)}" class="download-btn" download><svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>下载应用</a>` : ''}
                <a href="${app.repository}" target="_blank" class="repo-btn"><svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4"></path><path d="M9 18c-4.51 2-5-2-7-2"></path></svg>查看仓库</a>
            </div>
            
            ${app.screenshots && app.screenshots.length > 0 ? `
                <div class="app-screenshots">
                    <h3>截图</h3>
                    <div class="screenshot-container">
                        ${app.screenshots.map(screenshot => `
                            <img src="${getProxyUrl(screenshot)}" alt="应用截图" class="screenshot">
                        `).join('')}
                    </div>
                </div>
            ` : ''}
            
            <div class="app-last-update">
                最后更新: ${formatDate(app.lastUpdate)}
            </div>
        </div>
    `;
    
    // 平滑切换到详情页
    appList.style.opacity = '0';
    setTimeout(() => {
        appList.classList.add('hidden');
        appDetail.classList.remove('hidden');
        setTimeout(() => {
            appDetail.style.opacity = '1';
        }, 50);
    }, 200);
}

// 显示应用列表
function showAppList() {
    // 平滑切换回列表页
    appDetail.style.opacity = '0';
    setTimeout(() => {
        appDetail.classList.add('hidden');
        appList.classList.remove('hidden');
        setTimeout(() => {
            appList.style.opacity = '1';
        }, 50);
    }, 200);
}

// 格式化日期
function formatDate(dateString) {
    if (!dateString) return '未知';
    
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now - date);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays < 7) {
        return `${diffDays}天前`;
    } else if (diffDays < 30) {
        return `${Math.floor(diffDays / 7)}周前`;
    } else if (diffDays < 365) {
        return `${Math.floor(diffDays / 30)}个月前`;
    } else {
        return `${Math.floor(diffDays / 365)}年前`;
    }
}

// 显示错误信息
function showError(message) {
    appList.innerHTML = `<div class="miuix-card"><div class="miuix-card-content" style="padding: 32px; text-align: center; font-size: 16px; color: var(--miuix-color-error);">${message}</div></div>`;
}

// 显示加载动画
function showLoading() {
    // 使用骨架屏代替旋转加载器
    const skeletonCards = Array(6).fill('').map(() => `
        <div class="skeleton-card">
            <div class="skeleton-header">
                <div class="skeleton-icon skeleton-pulse"></div>
                <div class="skeleton-info">
                    <div class="skeleton-title skeleton-pulse"></div>
                    <div class="skeleton-author skeleton-pulse"></div>
                </div>
            </div>
            <div class="skeleton-body">
                <div class="skeleton-desc skeleton-pulse"></div>
                <div class="skeleton-desc skeleton-pulse" style="width: 60%;"></div>
            </div>
        </div>
    `).join('');
    
    appList.innerHTML = skeletonCards;
}

// 智能缓存：基于版本哈希，只在数据变化时下载
async function fetchWithVersionCheck(url, cacheKey, versionKey, remoteVersion) {
    const cachedData = localStorage.getItem(cacheKey);
    const cachedVersion = localStorage.getItem(`${cacheKey}_version`);
    
    // 如果版本号相同且有缓存，直接使用缓存
    if (remoteVersion && cachedVersion === remoteVersion && cachedData) {
        console.log(`[Cache] ${cacheKey}: 版本未变化(${remoteVersion})，使用缓存`);
        try {
            return JSON.parse(cachedData);
        } catch (e) {
            // 缓存损坏，继续下载
        }
    }
    
    try {
        const response = await fetch(url, { cache: 'no-cache' });
        
        if (response.ok) {
            const data = await response.json();
            
            // 保存到缓存
            localStorage.setItem(cacheKey, JSON.stringify(data));
            if (remoteVersion) {
                localStorage.setItem(`${cacheKey}_version`, remoteVersion);
            }
            
            console.log(`[Cache] ${cacheKey}: 已更新缓存，版本: ${remoteVersion || 'unknown'}`);
            return data;
        }
        
        // 请求失败但有缓存，使用缓存
        if (cachedData) {
            console.warn(`请求 ${url} 失败，使用缓存数据`);
            return JSON.parse(cachedData);
        }
        
        throw new Error(`HTTP ${response.status}`);
    } catch (error) {
        // 网络错误时尝试使用缓存
        if (cachedData) {
            console.warn(`网络错误，使用缓存数据:`, error);
            return JSON.parse(cachedData);
        }
        throw error;
    }
}

// 获取远程版本信息
async function fetchVersionInfo() {
    const versionUrl = TEST_MODE ? TEST_VERSION_URL : './version.json';
    try {
        const response = await fetch(versionUrl, { cache: 'no-cache' });
        if (response.ok) {
            return await response.json();
        }
    } catch (error) {
        console.warn('获取版本信息失败:', error);
    }
    return null;
}

// 加载应用数据
async function loadAppsData() {
    try {
        // 显示加载动画
        showLoading();
        
        // 根据测试模式选择数据源
        const appUrl = TEST_MODE ? TEST_DATA_URL : './app_details.json';
        const fnpackUrl = TEST_MODE ? TEST_FNPACK_URL : './fnpack_details.json';
        
        if (TEST_MODE) {
            console.log('[Debug] 测试模式已启用，从 GitHub 远程获取数据');
        }
        
        // 首先获取版本信息（小文件，~100字节）
        const versionInfo = await fetchVersionInfo();
        const appVersion = versionInfo?.app_details?.hash;
        const fnpackVersion = versionInfo?.fnpack_details?.hash;
        
        // 根据版本信息智能加载数据
        const [appData, fnpackData] = await Promise.all([
            fetchWithVersionCheck(appUrl, 'appDetailsCache', 'app_details', appVersion),
            fetchWithVersionCheck(fnpackUrl, 'fnpackDetailsCache', 'fnpack_details', fnpackVersion)
        ]);
        
        // 合并两个数据源的应用数据，并为不同来源的应用添加标识
        const standardApps = (appData.apps || []).map(app => ({ ...app, source: '2FStore' }));
        const fnpackApps = (fnpackData.apps || []).map(app => ({ ...app, source: 'FnDepot' }));
        
        // 合并并去重（如果有重复的应用ID）
        const appMap = new Map();
        [...standardApps, ...fnpackApps].forEach(app => {
            // 优先保留标准应用，如果没有则使用FnPack应用
            if (!appMap.has(app.id)) {
                appMap.set(app.id, app);
            }
        });
        
        appsData = Array.from(appMap.values());
        
        // 提取所有分类
        extractCategories();
        
        // 初始显示所有应用
        filterApps();
    } catch (error) {
        console.error('加载应用数据失败:', error);
        showError('加载应用数据失败，请稍后再试。');
    }
}