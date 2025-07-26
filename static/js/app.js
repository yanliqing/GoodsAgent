// 全局变量
let currentSessionId = null;
let accessToken = null;
let isLoggedIn = false;

// API基础URL
const API_BASE_URL = '/api/v1';

// DOM元素
const chatMessages = document.getElementById('chatMessages');
const messageInput = document.getElementById('messageInput');
const sendMessageBtn = document.getElementById('sendMessageBtn');
const uploadImageBtn = document.getElementById('uploadImageBtn');
const imageUpload = document.getElementById('imageUpload');
const chatSessionsList = document.getElementById('chatSessionsList');
const newChatBtn = document.getElementById('newChatBtn');
const loginBtn = document.getElementById('loginBtn');
const registerBtn = document.getElementById('registerBtn');
const loginSubmitBtn = document.getElementById('loginSubmitBtn');
const registerSubmitBtn = document.getElementById('registerSubmitBtn');

// 模态框
const loginModal = new bootstrap.Modal(document.getElementById('loginModal'));
const registerModal = new bootstrap.Modal(document.getElementById('registerModal'));
const productsModal = new bootstrap.Modal(document.getElementById('productsModal'));

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    // 检查本地存储中的令牌
    accessToken = localStorage.getItem('accessToken');
    if (accessToken) {
        isLoggedIn = true;
        updateUIForLoggedInUser();
        loadChatSessions();
    }

    // 添加事件监听器
    addEventListeners();
});

// 添加事件监听器
function addEventListeners() {
    // 发送消息
    sendMessageBtn.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    // 上传图片
    uploadImageBtn.addEventListener('click', () => {
        imageUpload.click();
    });
    imageUpload.addEventListener('change', uploadImage);

    // 新建会话
    newChatBtn.addEventListener('click', createNewSession);

    // 登录和注册
    loginBtn.addEventListener('click', () => loginModal.show());
    registerBtn.addEventListener('click', () => registerModal.show());
    loginSubmitBtn.addEventListener('click', login);
    registerSubmitBtn.addEventListener('click', register);
}

// 更新已登录用户的UI
function updateUIForLoggedInUser() {
    loginBtn.innerHTML = '<i class="bi bi-box-arrow-right"></i> 退出';
    loginBtn.removeEventListener('click', () => loginModal.show());
    loginBtn.addEventListener('click', logout);
    registerBtn.style.display = 'none';
}

// 加载聊天会话列表
async function loadChatSessions() {
    if (!isLoggedIn) return;

    try {
        const response = await fetch(`${API_BASE_URL}/chat/sessions`, {
            headers: {
                'Authorization': `Bearer ${accessToken}`
            }
        });

        if (response.ok) {
            const sessions = await response.json();
            renderChatSessions(sessions);

            // 如果有会话，加载第一个会话的消息
            if (sessions.length > 0) {
                currentSessionId = sessions[0].id;
                loadChatMessages(currentSessionId);
            }
        } else {
            console.error('加载会话失败:', await response.text());
        }
    } catch (error) {
        console.error('加载会话出错:', error);
    }
}

// 渲染聊天会话列表
function renderChatSessions(sessions) {
    chatSessionsList.innerHTML = '';

    sessions.forEach(session => {
        const li = document.createElement('li');
        li.className = 'nav-item';
        li.innerHTML = `
            <div class="d-flex align-items-center">
                <a class="nav-link flex-grow-1 ${session.id === currentSessionId ? 'active' : ''}" href="#" data-session-id="${session.id}">
                    <i class="bi bi-chat-dots"></i> ${session.title}
                </a>
                <button class="btn btn-sm btn-outline-danger delete-session-btn" data-session-id="${session.id}" title="删除会话">
                    <i class="bi bi-trash"></i>
                </button>
            </div>
        `;
        
        // 添加会话点击事件
        li.querySelector('a').addEventListener('click', (e) => {
            e.preventDefault();
            currentSessionId = session.id;
            document.querySelectorAll('#chatSessionsList .nav-link').forEach(el => {
                el.classList.remove('active');
            });
            e.target.classList.add('active');
            loadChatMessages(session.id);
        });
        
        // 添加删除按钮事件
        li.querySelector('.delete-session-btn').addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            deleteSession(session.id);
        });
        
        chatSessionsList.appendChild(li);
    });
}

// 加载聊天消息
async function loadChatMessages(sessionId) {
    if (!isLoggedIn) return;

    try {
        const response = await fetch(`${API_BASE_URL}/chat/sessions/${sessionId}/messages`, {
            headers: {
                'Authorization': `Bearer ${accessToken}`
            }
        });

        if (response.ok) {
            const messages = await response.json();
            renderChatMessages(messages);
        } else {
            console.error('加载消息失败:', await response.text());
        }
    } catch (error) {
        console.error('加载消息出错:', error);
    }
}

// 渲染聊天消息
function renderChatMessages(messages) {
    chatMessages.innerHTML = '';

    messages.forEach(message => {
        addMessageToChat(message.role, message.content, message.message_type, message.metadata);
    });

    // 滚动到底部
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// 创建新会话
async function createNewSession() {
    if (!isLoggedIn) {
        loginModal.show();
        return;
    }

    // 清空聊天区域
    chatMessages.innerHTML = '';
    addMessageToChat('assistant', '你好！我是淘宝智能搜索助手，有什么可以帮到你的吗？');

    // 发送第一条消息创建会话
    currentSessionId = null;
}

// 发送消息
async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message) return;

    if (!isLoggedIn) {
        loginModal.show();
        return;
    }

    // 添加用户消息到聊天区域
    addMessageToChat('user', message);
    messageInput.value = '';

    // 显示加载状态
    const loadingMessage = addMessageToChat('assistant', '<i class="bi bi-three-dots"></i> 思考中...');

    try {
        const response = await fetch(`${API_BASE_URL}/chat/send`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${accessToken}`
            },
            body: JSON.stringify({
                session_id: currentSessionId,
                message: message,
                message_type: 'text'
            })
        });

        if (response.ok) {
            const data = await response.json();
            // 更新会话ID
            currentSessionId = data.session_id;
            // 移除加载消息
            chatMessages.removeChild(loadingMessage);
            // 添加助手回复
            addMessageToChat('assistant', data.message, data.message_type, data.metadata);
            // 刷新会话列表
            loadChatSessions();
        } else {
            // 移除加载消息
            chatMessages.removeChild(loadingMessage);
            // 显示错误
            addMessageToChat('assistant', '抱歉，处理您的请求时出现了问题。请稍后再试。');
            console.error('发送消息失败:', await response.text());
        }
    } catch (error) {
        // 移除加载消息
        chatMessages.removeChild(loadingMessage);
        // 显示错误
        addMessageToChat('assistant', '抱歉，连接服务器时出现了问题。请检查您的网络连接。');
        console.error('发送消息出错:', error);
    }
}

// 上传图片
async function uploadImage(event) {
    if (!isLoggedIn) {
        loginModal.show();
        return;
    }

    const file = event.target.files[0];
    if (!file) return;

    // 检查文件类型
    if (!file.type.startsWith('image/')) {
        alert('请选择图片文件');
        return;
    }

    // 添加用户消息到聊天区域
    const reader = new FileReader();
    reader.onload = async (e) => {
        const imageData = e.target.result;
        // 显示图片消息
        addMessageToChat('user', `<img src="${imageData}" alt="用户上传图片" style="max-width: 100%; max-height: 300px;">`, 'image');

        // 显示加载状态
        const loadingMessage = addMessageToChat('assistant', '<i class="bi bi-three-dots"></i> 分析图片中...');

        try {
            const response = await fetch(`${API_BASE_URL}/chat/image-search`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${accessToken}`
                },
                body: JSON.stringify({
                    session_id: currentSessionId,
                    image_data: imageData.split(',')[1], // 去除base64前缀
                    message: '请帮我找一下这张图片中的商品'
                })
            });

            if (response.ok) {
                const data = await response.json();
                // 更新会话ID
                currentSessionId = data.session_id;
                // 移除加载消息
                chatMessages.removeChild(loadingMessage);
                // 添加助手回复
                addMessageToChat('assistant', data.message, data.message_type, data.metadata);
                // 如果有商品数据，显示商品模态框
                if (data.metadata && data.metadata.products && data.metadata.products.length > 0) {
                    showProductsModal(data.metadata.products);
                }
                // 刷新会话列表
                loadChatSessions();
            } else {
                // 移除加载消息
                chatMessages.removeChild(loadingMessage);
                // 显示错误
                addMessageToChat('assistant', '抱歉，处理您的图片时出现了问题。请稍后再试。');
                console.error('图片搜索失败:', await response.text());
            }
        } catch (error) {
            // 移除加载消息
            chatMessages.removeChild(loadingMessage);
            // 显示错误
            addMessageToChat('assistant', '抱歉，连接服务器时出现了问题。请检查您的网络连接。');
            console.error('图片搜索出错:', error);
        }
    };
    reader.readAsDataURL(file);

    // 清空文件输入，以便可以再次选择同一文件
    event.target.value = '';
}

// 添加消息到聊天区域
function addMessageToChat(role, content, messageType = 'text', metadata = null) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    // 根据消息类型处理内容
    if (messageType === 'text') {
        // 处理可能的商品链接
        content = processProductLinks(content);
        contentDiv.innerHTML = content;
    } else if (messageType === 'image') {
        contentDiv.innerHTML = content; // 已经是HTML
    } else if (messageType === 'product' && metadata) {
        // 显示商品信息
        contentDiv.innerHTML = formatProductInfo(metadata);
    }

    // 添加时间
    const timeDiv = document.createElement('div');
    timeDiv.className = 'message-time';
    timeDiv.textContent = new Date().toLocaleTimeString();

    messageDiv.appendChild(contentDiv);
    messageDiv.appendChild(timeDiv);
    chatMessages.appendChild(messageDiv);

    // 滚动到底部
    chatMessages.scrollTop = chatMessages.scrollHeight;

    return messageDiv;
}

// 处理消息中的商品链接
function processProductLinks(content) {
    // 简单的正则表达式来匹配可能的商品ID
    const regex = /商品ID[：:](\s*)([\w-]+)/g;
    return content.replace(regex, (match, space, itemId) => {
        return `商品ID${space}<a href="#" class="product-link" data-item-id="${itemId}">${itemId}</a>`;
    });
}

// 格式化商品信息
function formatProductInfo(product) {
    return `
        <div class="product-info-card">
            <h5>${product.title}</h5>
            <p class="price">¥${product.price} <span class="original-price">¥${product.original_price || ''}</span></p>
            <p>${product.description || ''}</p>
            <div class="product-meta">
                <span>店铺: ${product.shop_name || '未知'}</span>
                <span>销量: ${product.sales || '0'}</span>
                <span>评分: ${product.rating || '无'}</span>
            </div>
            <a href="${product.detail_url || '#'}" target="_blank" class="btn btn-sm btn-primary mt-2">查看详情</a>
        </div>
    `;
}

// 显示商品模态框
function showProductsModal(products) {
    const productsContainer = document.getElementById('productsContainer');
    productsContainer.innerHTML = '';

    products.forEach(product => {
        const productDiv = document.createElement('div');
        productDiv.className = 'col-md-4 mb-3';
        productDiv.innerHTML = `
            <div class="product-card">
                <img src="${product.image_url || '/static/img/no-image.png'}" class="product-image" alt="${product.title}">
                <div class="product-info">
                    <h5 class="product-title">${product.title}</h5>
                    <div>
                        <span class="product-price">¥${product.price}</span>
                        ${product.original_price ? `<span class="product-original-price">¥${product.original_price}</span>` : ''}
                    </div>
                    <div class="product-meta">
                        <span>${product.shop_name || '未知店铺'}</span>
                        <span>销量: ${product.sales || '0'}</span>
                    </div>
                    <button class="btn btn-sm btn-primary mt-2 select-product" data-item-id="${product.item_id}">选择此商品</button>
                </div>
            </div>
        `;

        // 添加选择商品事件
        productDiv.querySelector('.select-product').addEventListener('click', () => {
            productsModal.hide();
            messageInput.value = `我想了解更多关于这个商品的信息：商品ID: ${product.item_id}`;
            sendMessage();
        });

        productsContainer.appendChild(productDiv);
    });

    productsModal.show();
}

// 登录
async function login() {
    const username = document.getElementById('loginUsername').value.trim();
    const password = document.getElementById('loginPassword').value.trim();
    const loginError = document.getElementById('loginError');

    if (!username || !password) {
        loginError.textContent = '请输入用户名和密码';
        loginError.style.display = 'block';
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/auth/login/json`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username,
                password
            })
        });

        if (response.ok) {
            const data = await response.json();
            accessToken = data.access_token;
            localStorage.setItem('accessToken', accessToken);
            isLoggedIn = true;
            updateUIForLoggedInUser();
            loginModal.hide();
            loadChatSessions();
        } else {
            const errorData = await response.json();
            loginError.textContent = errorData.detail || '登录失败，请检查用户名和密码';
            loginError.style.display = 'block';
        }
    } catch (error) {
        loginError.textContent = '连接服务器时出现问题，请稍后再试';
        loginError.style.display = 'block';
        console.error('登录出错:', error);
    }
}

// 注册
async function register() {
    const username = document.getElementById('registerUsername').value.trim();
    const email = document.getElementById('registerEmail').value.trim();
    const password = document.getElementById('registerPassword').value.trim();
    const registerError = document.getElementById('registerError');

    if (!username || !email || !password) {
        registerError.textContent = '请填写所有字段';
        registerError.style.display = 'block';
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/auth/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username,
                email,
                password
            })
        });

        if (response.ok) {
            registerModal.hide();
            alert('注册成功，请登录');
            loginModal.show();
        } else {
            const errorData = await response.json();
            registerError.textContent = errorData.detail || '注册失败，请稍后再试';
            registerError.style.display = 'block';
        }
    } catch (error) {
        registerError.textContent = '连接服务器时出现问题，请稍后再试';
        registerError.style.display = 'block';
        console.error('注册出错:', error);
    }
}

// 退出登录
function logout() {
    localStorage.removeItem('accessToken');
    accessToken = null;
    isLoggedIn = false;
    currentSessionId = null;
    
    // 更新UI
    loginBtn.innerHTML = '<i class="bi bi-person"></i> 登录';
    loginBtn.removeEventListener('click', logout);
    loginBtn.addEventListener('click', () => loginModal.show());
    registerBtn.style.display = 'inline-block';
    
    // 清空会话列表和聊天区域
    chatSessionsList.innerHTML = '';
    chatMessages.innerHTML = '';
    
    // 显示欢迎消息
    addMessageToChat('assistant', '你好！我是淘宝智能搜索助手，可以帮你：<ul><li>搜索淘宝商品</li><li>通过图片找相似商品</li><li>提供商品推荐</li><li>查询订单和物流信息</li><li>解答购物相关问题</li></ul>请问有什么可以帮到你的吗？');
}

// 删除会话
async function deleteSession(sessionId) {
    if (!confirm('确定要删除这个会话吗？删除后无法恢复。')) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/chat/sessions/${sessionId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${accessToken}`,
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            // 如果删除的是当前会话，清空聊天区域
            if (sessionId === currentSessionId) {
                currentSessionId = null;
                chatMessages.innerHTML = '';
                addMessageToChat('assistant', '你好！我是淘宝智能搜索助手，可以帮你：<ul><li>搜索淘宝商品</li><li>通过图片找相似商品</li><li>提供商品推荐</li><li>查询订单和物流信息</li><li>解答购物相关问题</li></ul>请问有什么可以帮到你的吗？');
            }
            
            // 重新加载会话列表
            loadChatSessions();
        } else {
            const errorData = await response.json();
            alert('删除会话失败：' + (errorData.detail || '未知错误'));
        }
    } catch (error) {
        console.error('删除会话出错:', error);
        alert('删除会话时出现网络错误，请稍后再试');
    }
}