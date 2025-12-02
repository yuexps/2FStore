// 全局变量
let appsData = [];
let filteredApps = [];
let currentCategory = 'all';
let currentSort = 'name';
let githubProxy = ''; // 新增全局变量存储GitHub代理URL

// Bing 每日图片 API
const BING_API = 'https://bing.biturl.top/?resolution=1920&format=json&index=0&mkt=zh-CN';

// 安全 HTML 标签白名单
const ALLOWED_TAGS = ['b', 'i', 'strong', 'em', 'br', 'a', 'p', 'ul', 'ol', 'li', 'code', 'pre', 'span'];
const ALLOWED_ATTRS = {
    'a': ['href', 'target', 'rel'],
    'span': ['class'],
    'code': ['class'],
    'pre': ['class']
};

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
const filterBtn = document.getElementById('filter-btn');
const filterModal = document.getElementById('filter-modal');
const mobileCategoryList = document.getElementById('mobile-category-list');
const mobileSortSelect = document.getElementById('mobile-sort-select');
const proxyBtn = document.getElementById('proxy-btn');
const proxyModal = document.getElementById('proxy-modal');
const mobileProxySelect = document.getElementById('mobile-proxy-select');
const mobileCustomProxyContainer = document.getElementById('mobile-custom-proxy-container');
const mobileCustomProxyInput = document.getElementById('mobile-custom-proxy-input');

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
    
    // 移动端筛选按钮
    if (filterBtn) {
        filterBtn.addEventListener('click', () => {
            filterModal.classList.remove('hidden');
            updateMobileFilterUI();
        });
    }
    
    // 移动端筛选模态框关闭
    if (filterModal) {
        filterModal.addEventListener('click', (e) => {
            if (e.target === filterModal) {
                filterModal.classList.add('hidden');
            }
        });
        
        const closeBtn = filterModal.querySelector('.miuix-modal-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                filterModal.classList.add('hidden');
            });
        }
    }
    
    // 移动端分类点击
    if (mobileCategoryList) {
        mobileCategoryList.addEventListener('click', (e) => {
            const listItem = e.target.closest('.miuix-list-item');
            if (listItem) {
                currentCategory = listItem.dataset.category;
                filterApps();
                updateMobileFilterUI();
                filterModal.classList.add('hidden');
            }
        });
    }
    
    // 移动端排序
    if (mobileSortSelect) {
        mobileSortSelect.addEventListener('change', () => {
            currentSort = mobileSortSelect.value;
            sortSelect.value = currentSort;
            filterApps();
        });
    }
    
    // 移动端代理设置按钮
    if (proxyBtn) {
        proxyBtn.addEventListener('click', () => {
            proxyModal.classList.remove('hidden');
            // 同步当前代理设置到移动端
            if (mobileProxySelect) {
                mobileProxySelect.value = proxySelect.value;
                if (proxySelect.value === 'custom') {
                    mobileCustomProxyContainer.classList.remove('hidden');
                    mobileCustomProxyInput.value = customProxyInput.value;
                } else {
                    mobileCustomProxyContainer.classList.add('hidden');
                }
            }
        });
    }
    
    // 移动端代理模态框关闭
    if (proxyModal) {
        proxyModal.addEventListener('click', (e) => {
            if (e.target === proxyModal) {
                proxyModal.classList.add('hidden');
            }
        });
        
        const closeBtn = proxyModal.querySelector('.miuix-modal-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                proxyModal.classList.add('hidden');
            });
        }
    }
    
    // 移动端代理选择
    if (mobileProxySelect) {
        mobileProxySelect.addEventListener('change', () => {
            const value = mobileProxySelect.value;
            proxySelect.value = value; // 同步到桌面端选择器
            
            if (value === 'custom') {
                mobileCustomProxyContainer.classList.remove('hidden');
                customProxyContainer.classList.remove('hidden');
            } else {
                mobileCustomProxyContainer.classList.add('hidden');
                customProxyContainer.classList.add('hidden');
                githubProxy = value;
                saveProxySetting();
                reloadCurrentView();
            }
        });
    }
    
    // 移动端自定义代理输入
    if (mobileCustomProxyInput) {
        mobileCustomProxyInput.addEventListener('blur', () => {
            const value = mobileCustomProxyInput.value.trim();
            customProxyInput.value = value; // 同步到桌面端
            handleCustomProxyChange();
        });
        mobileCustomProxyInput.addEventListener('keyup', (e) => {
            if (e.key === 'Enter') {
                customProxyInput.value = mobileCustomProxyInput.value.trim();
                handleCustomProxyChange();
                proxyModal.classList.add('hidden');
            }
        });
    }
    
    // 键盘快捷键：ESC 关闭模态框和详情
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            if (!submitModal.classList.contains('hidden')) {
                submitModal.classList.add('hidden');
            } else if (filterModal && !filterModal.classList.contains('hidden')) {
                filterModal.classList.add('hidden');
            } else if (proxyModal && !proxyModal.classList.contains('hidden')) {
                proxyModal.classList.add('hidden');
            } else if (!appDetail.classList.contains('hidden')) {
                showAppList();
            }
        }
    });
}

// 更新移动端筛选界面
function updateMobileFilterUI() {
    if (!mobileCategoryList) return;
    
    // 同步分类列表
    mobileCategoryList.innerHTML = '';
    const categories = Array.from(categoryList.querySelectorAll('.miuix-list-item'));
    categories.forEach(item => {
        const li = document.createElement('li');
        li.className = 'miuix-list-item';
        li.dataset.category = item.dataset.category;
        if (item.dataset.category === currentCategory) {
            li.classList.add('active');
        }
        li.innerHTML = `<span class="miuix-list-item-text">${item.textContent}</span>`;
        mobileCategoryList.appendChild(li);
    });
    
    // 同步排序选项
    if (mobileSortSelect) {
        mobileSortSelect.value = currentSort;
    }
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

// 加载保存的代理设置
function loadProxySetting() {
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
    
    filteredApps.forEach((app, index) => {
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
    
    // 触发重新排以开始动画
    requestAnimationFrame(() => {
        document.querySelectorAll('.app-card').forEach(card => {
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        });
    });
}

// 创建应用卡片
function createAppCard(app) {
    const initial = app.name.charAt(0).toUpperCase();
    const iconUrl = app.iconUrl || '';
    let sourceBadge = '';
    if (app.source) {
        sourceBadge = `<span class="app-source-badge store-${app.source.toLowerCase()}">${app.source}</span>`;
    }
    
    // 图片错误处理：失败时显示首字母
    const imgErrorHandler = `onerror="this.style.display='none';this.parentElement.querySelector('.img-placeholder').style.display='flex';"`;
    
    return `
        <div class="miuix-card app-card" data-app-id="${app.id}">
            <div class="app-card-header">
                <div class="app-icon">
                    ${iconUrl ? `<img src="${getProxyUrl(iconUrl)}" alt="${app.name}" ${imgErrorHandler} style="width: 100%; height: 100%; object-fit: cover; border-radius: 12px;"><span class="img-placeholder" style="display:none;">${initial}</span>` : initial}
                </div>
                <div class="app-info">
                    <div class="app-name">${app.name} ${sourceBadge}</div>
                    <div class="app-author">作者: ${app.author}</div>
                </div>
            </div>
            <div class="app-card-body">
                <div class="app-description">${sanitizeHtml(app.description) || '暂无描述'}</div>
                <div class="app-meta">
                    <span>⭐ ${app.stars || 0}</span>
                    <span>🔄 ${formatDate(app.lastUpdate)}</span>
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
    
    // 图片错误处理
    const imgErrorHandler = `onerror="this.style.display='none';this.parentElement.querySelector('.img-placeholder').style.display='flex';"`;
    
    appDetailContent.innerHTML = `
        <div class="app-detail-header">
            <div class="app-detail-icon">
                ${iconUrl ? `<img src="${getProxyUrl(iconUrl)}" alt="${app.name}" ${imgErrorHandler} style="width: 100%; height: 100%; object-fit: cover; border-radius: 16px;"><span class="img-placeholder" style="display:none;">${initial}</span>` : initial}
            </div>
            <div class="app-detail-info">
                <div class="app-detail-name">${app.name} ${sourceBadge}</div>
                <div class="app-detail-author">作者: ${app.author}</div>
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

// 智能缓存：检查数据是否有更新
async function fetchWithCache(url, cacheKey) {
    const cachedData = localStorage.getItem(cacheKey);
    const cachedETag = localStorage.getItem(`${cacheKey}_etag`);
    const cachedTime = localStorage.getItem(`${cacheKey}_time`);
    
    // 如果缓存存在且未超过1小时，直接使用缓存
    const ONE_HOUR = 60 * 60 * 1000;
    if (cachedData && cachedTime && (Date.now() - parseInt(cachedTime)) < ONE_HOUR) {
        try {
            return JSON.parse(cachedData);
        } catch (e) {
            // 缓存数据损坏，继续请求新数据
        }
    }
    
    // 构建请求头，如果有 ETag 则发送条件请求
    const headers = {};
    if (cachedETag) {
        headers['If-None-Match'] = cachedETag;
    }
    
    try {
        const response = await fetch(url, { headers });
        
        // 304 Not Modified - 数据未变化，使用缓存
        if (response.status === 304 && cachedData) {
            localStorage.setItem(`${cacheKey}_time`, Date.now().toString());
            return JSON.parse(cachedData);
        }
        
        if (response.ok) {
            const data = await response.json();
            const newETag = response.headers.get('ETag');
            
            // 保存到缓存
            localStorage.setItem(cacheKey, JSON.stringify(data));
            localStorage.setItem(`${cacheKey}_time`, Date.now().toString());
            if (newETag) {
                localStorage.setItem(`${cacheKey}_etag`, newETag);
            }
            
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

// 加载应用数据
async function loadAppsData() {
    try {
        // 显示加载动画
        showLoading();
        
        // 使用智能缓存同时加载两个数据源
        const [appData, fnpackData] = await Promise.all([
            fetchWithCache('./app_details.json', 'appDetailsCache'),
            fetchWithCache('./fnpack_details.json', 'fnpackDetailsCache')
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