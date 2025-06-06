// research-enhance.js - 增强交互功能和视觉效果

document.addEventListener('DOMContentLoaded', function() {
    // 初始化粒子效果
    initParticles();
    
    // 初始化工具提示
    initTooltips();
    
    // 增强按钮和卡片交互
    enhanceInteractions();
    
    // 设置Ajax加载结果
    setupAjaxLoading();
    
    // 添加滚动动画效果
    addScrollAnimations();
});

// 初始化粒子效果
function initParticles() {
    if (typeof particlesJS !== 'undefined') {
        particlesJS('particles-js', {
            "particles": {
                "number": {
                    "value": 80,
                    "density": {
                        "enable": true,
                        "value_area": 1500
                    }
                },
                "color": {
                    "value": ["#3d5af1", "#6f42c1", "#4285f4", "#2b8ae3"]
                },
                "shape": {
                    "type": ["circle", "triangle"],
                    "stroke": {
                        "width": 0,
                        "color": "#000000"
                    },
                    "polygon": {
                        "nb_sides": 5
                    }
                },
                "opacity": {
                    "value": 0.05,
                    "random": true,
                    "anim": {
                        "enable": true,
                        "speed": 0.3,
                        "opacity_min": 0.01,
                        "sync": false
                    }
                },
                "size": {
                    "value": 3,
                    "random": true,
                    "anim": {
                        "enable": true,
                        "speed": 0.5,
                        "size_min": 0.1,
                        "sync": false
                    }
                },
                "line_linked": {
                    "enable": true,
                    "distance": 150,
                    "color": "#3d5af1",
                    "opacity": 0.06,
                    "width": 1
                },
                "move": {
                    "enable": true,
                    "speed": 0.3,
                    "direction": "none",
                    "random": true,
                    "straight": false,
                    "out_mode": "out",
                    "bounce": false,
                    "attract": {
                        "enable": true,
                        "rotateX": 600,
                        "rotateY": 1200
                    }
                }
            },
            "interactivity": {
                "detect_on": "canvas",
                "events": {
                    "onhover": {
                        "enable": true,
                        "mode": "grab"
                    },
                    "onclick": {
                        "enable": true,
                        "mode": "push"
                    },
                    "resize": true
                },
                "modes": {
                    "grab": {
                        "distance": 140,
                        "line_linked": {
                            "opacity": 0.15
                        }
                    },
                    "push": {
                        "particles_nb": 3
                    }
                }
            },
            "retina_detect": true
        });
    }
}

// 初始化工具提示
function initTooltips() {
    const actionBtns = document.querySelectorAll('.action-btn');
    
    actionBtns.forEach(btn => {
        const tooltip = btn.querySelector('.tooltip');
        if (tooltip) {
            btn.addEventListener('mouseenter', function() {
                tooltip.style.opacity = '1';
                tooltip.style.visibility = 'visible';
                tooltip.style.transform = 'translateY(0)';
            });
            
            btn.addEventListener('mouseleave', function() {
                tooltip.style.opacity = '0';
                tooltip.style.visibility = 'hidden';
                tooltip.style.transform = 'translateY(10px)';
            });
        }
    });
}

// 增强按钮和卡片交互
function enhanceInteractions() {
    // 最近查询项点击效果
    const queryItems = document.querySelectorAll('.query-item');
    queryItems.forEach(item => {
        item.addEventListener('click', function() {
            const query = this.getAttribute('data-query');
            const input = document.getElementById('event-input');
            if (input && query) {
                input.value = query;
                
                // 添加点击动画效果
                this.classList.add('query-clicked');
                setTimeout(() => {
                    this.classList.remove('query-clicked');
                }, 500);
            }
        });
    });
    
    // 卡片悬停效果增强（现在应用于动态加载的内容）
    document.addEventListener('mouseenter', function(e) {
        if (e.target.matches('.event-card, .factcheck-card, .topic-card, .evidence-item')) {
            const allCards = document.querySelectorAll('.event-card, .factcheck-card, .topic-card, .evidence-item');
            allCards.forEach(c => {
                if (c !== e.target) {
                    c.style.opacity = '0.8';
                }
            });
        }
    }, true);
    
    document.addEventListener('mouseleave', function(e) {
        if (e.target.matches('.event-card, .factcheck-card, .topic-card, .evidence-item')) {
            const allCards = document.querySelectorAll('.event-card, .factcheck-card, .topic-card, .evidence-item');
            allCards.forEach(c => {
                c.style.opacity = '1';
            });
        }
    }, true);
    
    // 使用事件委托为动态加载的标签添加点击效果
    document.addEventListener('click', function(e) {
        if (e.target.matches('.tag')) {
            e.target.classList.toggle('tag-active');
        }
    });
}

// 设置Ajax加载结果
function setupAjaxLoading() {
    const analyzeBtn = document.getElementById('analyze-btn');
    const btnText = analyzeBtn ? analyzeBtn.querySelector('.btn-text') : null;
    const btnLoader = analyzeBtn ? analyzeBtn.querySelector('.btn-loader') : null;
    const input = document.getElementById('event-input');
    const resultsArea = document.querySelector('.research-results');
    
    if (analyzeBtn && btnText && btnLoader && input && resultsArea) {
        analyzeBtn.addEventListener('click', function() {
            if (!input.value.trim()) {
                // 输入为空时添加晃动效果
                input.classList.add('shake');
                setTimeout(() => {
                    input.classList.remove('shake');
                }, 600);
                return;
            }
            
            // 显示加载状态
            btnText.style.opacity = '0';
            btnLoader.style.display = 'block';
            analyzeBtn.classList.add('loading');
            
            // 更新结果标题为加载中状态
            updateResultsHeader('正在分析...', '正在处理您的请求，请稍候');
            
            // 获取当前模式
            const activeMode = document.querySelector('.mode-btn.active');
            const mode = activeMode ? activeMode.getAttribute('data-mode') : 'timeline';
            
            // 模拟Ajax请求（实际项目中应替换为真实API请求）
            setTimeout(() => {
                // 隐藏空状态
                const emptyState = document.querySelector('.empty-state');
                if (emptyState) emptyState.style.display = 'none';
                
                // 模拟获取数据
                const mockData = getMockData(input.value.trim(), mode);
                
                // 根据模式选择渲染方式
                if (mode === 'timeline') {
                    // 使用card.html模板
                    loadCardTemplate(mockData, resultsArea);
                } else if (mode === 'factcheck') {
                    // 使用内置模板
                    renderFactcheckResults(mockData, resultsArea);
                }
                
                // 恢复按钮状态
                btnText.style.opacity = '1';
                btnLoader.style.display = 'none';
                analyzeBtn.classList.remove('loading');
                
                // 更新滚动动画
                setTimeout(animateOnScroll, 200);
            }, 1500);
        });
    }
}

// 加载card.html模板
function loadCardTemplate(data, container) {
    // 更新结果标题和副标题
    updateResultsHeader(data.title, data.subtitle);
    
    // 创建时间线数据结构
    const timelineData = createTimelineDataFromMock(data);
    
    // 使用fetch API加载card.html模板
    fetch('card.html')
        .then(response => response.text())
        .then(html => {
            // 清除结果区域内容
            clearResultsContent(container);
            
            // 创建一个iframe来显示card.html
            const iframe = document.createElement('iframe');
            iframe.style.width = '100%';
            iframe.style.height = '800px';
            iframe.style.border = 'none';
            iframe.style.borderRadius = '16px';
            iframe.id = 'timeline-frame';
            
            // 添加iframe到容器
            container.appendChild(iframe);
            
            // 设置iframe内容并注入数据
            const iframeDoc = iframe.contentWindow.document;
            iframeDoc.open();
            
            // 替换模板中的示例数据
            const modifiedHtml = html.replace(
                'data() {\n        return {\n          activeIndex: null,\n          data:',
                `data() {\n        return {\n          activeIndex: null,\n          data: ${JSON.stringify(timelineData)},\n          _originalData:`
            );
            
            iframeDoc.write(modifiedHtml);
            iframeDoc.close();
            
            // 调整iframe高度以适应内容
            setTimeout(() => {
                adjustIframeHeight(iframe);
            }, 500);
        })
        .catch(error => {
            console.error('加载模板失败:', error);
            // 失败时回退到默认渲染方式
            renderTimelineResults(data, container);
        });
}

// 根据模拟数据创建card.html所需的时间线数据结构
function createTimelineDataFromMock(mockData) {
    // 转换时间线项
    const events = mockData.timelineItems.map((item, index) => {
        return {
            date: `${item.month}${item.day}日`,
            title: item.title,
            description: item.content
        };
    });
    
    // 如果有相关话题，添加到时间线末尾
    if (mockData.relatedTopics && mockData.relatedTopics.length > 0) {
        mockData.relatedTopics.forEach(topic => {
            events.push({
                date: '相关话题',
                title: topic.title,
                description: topic.content
            });
        });
    }
    
    // 创建card.html所需的数据结构
    return {
        title: mockData.title,
        subtitle: mockData.subtitle,
        background: `这是关于"${mockData.title}"的舆情事件分析。本分析基于最近30天内的社交媒体数据、新闻报道和官方声明，旨在客观呈现事件发展脉络。`,
        summary: mockData.description,
        events: events
    };
}

// 调整iframe高度以适应内容
function adjustIframeHeight(iframe) {
    try {
        const height = iframe.contentWindow.document.body.scrollHeight;
        iframe.style.height = (height + 20) + 'px';
    } catch (e) {
        console.error('调整iframe高度失败', e);
    }
}

// 更新结果标题区域
function updateResultsHeader(title, subtitle) {
    const resultsTitle = document.getElementById('results-title');
    const resultsSubtitle = document.getElementById('results-subtitle');
    
    if (resultsTitle) resultsTitle.textContent = title;
    if (resultsSubtitle) resultsSubtitle.textContent = subtitle;
}

// 根据模式渲染结果
function renderResults(data, mode) {
    const resultsArea = document.querySelector('.research-results');
    
    if (!resultsArea) return;
    
    // 更新标题和副标题
    updateResultsHeader(data.title, data.subtitle);
    
    // 根据模式渲染不同内容
    if (mode === 'timeline') {
        renderTimelineResults(data, resultsArea);
    } else if (mode === 'factcheck') {
        renderFactcheckResults(data, resultsArea);
    }
}

// 渲染时间线结果
function renderTimelineResults(data, container) {
    // 生成HTML内容
    const html = `
        <div class="timeline-result">
            <div class="event-summary">
                <div class="event-card">
                    <div class="event-header">
                        <span class="event-label">事件概况</span>
                        <span class="event-date">分析时间: <span id="analysis-date">${data.analysisDate}</span></span>
                    </div>
                    <h3 id="event-title">${data.title}</h3>
                    <p id="event-description">${data.description}</p>
                    <div class="event-meta">
                        <div class="meta-item">
                            <span class="meta-label">热度指数</span>
                            <div class="meta-value">
                                <span id="heat-value">${data.heatValue}</span>
                                <div class="heat-bar">
                                    <div class="heat-level" style="width: ${data.heatValue}%"></div>
                                </div>
                            </div>
                        </div>
                        <div class="meta-item">
                            <span class="meta-label">情感倾向</span>
                            <div class="sentiment-chart">
                                <div class="sentiment-bar negative" style="width: ${data.sentiment.negative}%">${data.sentiment.negative}%</div>
                                <div class="sentiment-bar neutral" style="width: ${data.sentiment.neutral}%">${data.sentiment.neutral}%</div>
                                <div class="sentiment-bar positive" style="width: ${data.sentiment.positive}%">${data.sentiment.positive}%</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="timeline-container">
                <h3 class="timeline-header">事件发展时间线</h3>
                <div class="timeline">
                    ${data.timelineItems.map((item, index) => `
                        <div class="timeline-item">
                            <div class="timeline-date">
                                <span class="day">${item.day}</span>
                                <span class="month">${item.month}</span>
                            </div>
                            <div class="timeline-content">
                                <h4>${item.title}</h4>
                                <p>${item.content}</p>
                                <div class="timeline-source">来源：${item.source}</div>
                                <div class="content-tags">
                                    ${item.tags.map(tag => `<span class="tag">${tag}</span>`).join('')}
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>

            <div class="related-topics">
                <h3>相关话题分析</h3>
                <div class="topics-container">
                    ${data.relatedTopics.map(topic => `
                        <div class="topic-card">
                            <h4>${topic.title}</h4>
                            <p>${topic.content}</p>
                        </div>
                    `).join('')}
                </div>
            </div>
        </div>
    `;
    
    // 清除旧内容，注入新内容
    clearResultsContent(container);
    container.insertAdjacentHTML('beforeend', html);
}

// 渲染事实核查结果
function renderFactcheckResults(data, container) {
    // 生成HTML内容
    const html = `
        <div class="factcheck-result">
            <div class="factcheck-card">
                <div class="factcheck-header">
                    <div class="factcheck-badge" data-verdict="${data.verdict.type}">
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
                            <line x1="12" y1="9" x2="12" y2="13"></line>
                            <line x1="12" y1="17" x2="12.01" y2="17"></line>
                        </svg>
                        <span class="verdict-text">${data.verdict.text}</span>
                    </div>
                    <div class="factcheck-date">
                        核查时间: <span id="check-date">${data.checkDate}</span>
                    </div>
                </div>
                <h3 id="claim-title">${data.title}</h3>
                <div class="claim-box">
                    <h4>核查内容</h4>
                    <p id="claim-content">${data.claimContent}</p>
                    <div class="claim-source">${data.claimSource}</div>
                </div>
                <div class="verdict-box">
                    <h4>核查结论</h4>
                    <p id="verdict-content">${data.verdictContent}</p>
                </div>
            </div>

            <div class="evidence-section">
                <h3>事实依据</h3>
                <div class="evidence-container">
                    ${data.evidenceItems.map(item => `
                        <div class="evidence-item">
                            <div class="evidence-header">
                                <h4>${item.title}</h4>
                                <div class="evidence-type ${item.type}">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                        ${item.type === 'true' ? 
                                           '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline>' : 
                                           (item.type === 'false' ? 
                                               '<circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line>' : 
                                               '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line>')}
                                    </svg>
                                    <span>${item.typeText}</span>
                                </div>
                            </div>
                            <p>${item.content}</p>
                            <div class="evidence-source">${item.source}</div>
                        </div>
                    `).join('')}
                </div>
            </div>

            <div class="conclusion-section">
                <h3>核查总结</h3>
                <p>${data.conclusion}</p>
                <div class="suggestion-box">
                    <h4>信息识别建议</h4>
                    <ul>
                        ${data.suggestions.map(suggestion => `<li>${suggestion}</li>`).join('')}
                    </ul>
                </div>
            </div>
        </div>
    `;
    
    // 清除旧内容，注入新内容
    clearResultsContent(container);
    container.insertAdjacentHTML('beforeend', html);
}

// 清除结果区域内容
function clearResultsContent(container) {
    // 保留header元素，移除其他内容
    const header = container.querySelector('.results-header');
    container.innerHTML = '';
    if (header) container.appendChild(header);
}

// 获取模拟数据
function getMockData(query, mode) {
    // 生成当前日期
    const now = new Date();
    const dateOptions = { year: 'numeric', month: 'long', day: 'numeric' };
    const currentDate = now.toLocaleDateString('zh-CN', dateOptions);
    
    // 根据模式返回不同的模拟数据
    if (mode === 'timeline') {
        // 根据查询内容选择不同的时间线模板
        if (query.includes('PX') || query.includes('厦门') || query.includes('化工')) {
            // 厦门PX事件时间线（完整版）
            return {
                title: '厦门PX事件时间线',
                subtitle: '2004年至2008年厦门PX项目发展历程',
                description: 'PX(对二甲苯)是重要的石化基础原料，广泛应用于纺织、包装、建筑等行业。2004年至2008年，厦门PX项目从规划到最终迁址，经历了政府决策、专家质疑、公众参与、政策调整等多个阶段，成为中国环境运动的重要案例。',
                analysisDate: currentDate,
                heatValue: 85, // 热度
                sentiment: {
                    negative: 35,
                    neutral: 40,
                    positive: 25
                },
                timelineItems: [
                    {
                        day: '15',
                        month: '7月',
                        title: '项目初始规划',
                        content: '腾龙芳烃(厦门)有限公司计划投资108亿元在海沧区建设PX(对二甲苯)项目，规划年产80万吨PX。项目总投资108亿元，预计年产值超过200亿元。该项目是厦门市"十一五"期间重点引进的工业项目。',
                        source: '厦门日报',
                        tags: ['官方报道', '项目规划']
                    },
                    {
                        day: '10',
                        month: '3月',
                        title: '项目获国家发改委批准',
                        content: '厦门PX项目获得国家发改委立项批准，选址从最初的漳州古雷变更为厦门海沧区，距离市区约7公里，临近居民区和学校。项目总投资108亿元，预计年产80万吨PX。批准文件指出该项目符合国家产业政策，有利于优化石化产业布局。',
                        source: '国家发改委',
                        tags: ['官方文件', '项目审批']
                    },
                    {
                        day: '25',
                        month: '2月',
                        title: '专家提案质疑',
                        content: '厦门大学赵玉山教授等人向政协提交提案，指出项目选址存在安全隐患，不符合化工项目选址要求。提案指出，根据国家相关规定，此类化工项目与居民区的安全距离应不少于100米，而厦门PX项目距离最近的居民区仅约1.5公里，与国际通行的安全标准相距甚远。',
                        source: '厦门政协会议',
                        tags: ['专家建议', '环保质疑']
                    },
                    {
                        day: '18',
                        month: '3月',
                        title: '媒体广泛报道',
                        content: '《中国经营报》发表《厦门百亿项目遭遇环保质疑》一文，随后《凤凰周刊》等媒体也相继报道，引发社会关注。凤凰周刊发表了题为《厦门PX项目：一个化工项目引发的争议》的报道，详细介绍了项目可能带来的环境风险和社会影响。',
                        source: '中国经营报',
                        tags: ['媒体报道', '舆论关注']
                    },
                    {
                        day: '28',
                        month: '5月',
                        title: '短信广泛传播',
                        content: '一条呼吁厦门市民"散步"抗议PX项目的短信在厦门市内广泛传播，短信在几天内传遍全市。短信内容提到："如果PX项目在厦门建成，将等于在厦门设置了一颗原子弹，我们子孙后代将面临白血病和畸形儿的威胁。为了我们自己和子孙后代，请转发这条短信。在6月1日，请到市政府前散步。"',
                        source: '社交媒体',
                        tags: ['公众参与', '信息扩散']
                    },
                    {
                        day: '1-2',
                        month: '6月',
                        title: '市民"散步"事件',
                        content: '厦门市民自发上街"散步"，表达对PX项目选址的意见。参与者以和平方式表达诉求，举牌"我要生存"、"还我蓝天碧水"等口号。据不完全统计，参与"散步"的市民人数达数万人，路线从市中心一直延伸到市政府所在地。这次集体行动持续了两天，期间秩序良好，未发生任何暴力冲突。',
                        source: '现场目击者',
                        tags: ['公众行动', '社会抗议']
                    },
                    {
                        day: '5-6',
                        month: '6月',
                        title: '政府回应',
                        content: '厦门市政府宣布暂停PX项目建设，并承诺进行进一步环评。市政府发言人表示："将认真听取市民意见，进行科学决策。"市政府还表示将委托权威机构对项目进行全面环境影响评估，并承诺在评估完成前暂停项目建设。',
                        source: '厦门市政府新闻办',
                        tags: ['官方回应', '政策调整']
                    },
                    {
                        day: '15',
                        month: '12月',
                        title: '环评公示与公众听证',
                        content: '厦门市举行PX项目环评公众听证会，邀请了来自各界的100多位代表参加。听证会分两天进行，共有107位代表发言，其中大多数代表表示反对项目在厦门建设。听证会上，环保专家详细介绍了项目可能带来的环境影响，包括大气污染、水污染以及潜在的安全风险等。',
                        source: '厦门市环保局',
                        tags: ['环境评估', '公众参与']
                    },
                    {
                        day: '8',
                        month: '1月',
                        title: '项目最终迁址',
                        content: '福建省发改委宣布，厦门PX项目将迁至漳州古雷半岛重建。官方通告称："根据科学评估和公众意见，决定将项目迁至更合适的区域建设。"通告还指出，古雷半岛位于福建省漳州市东南部，距离市区较远，周边人口密度低，更适合建设化工项目。',
                        source: '福建省发改委',
                        tags: ['最终决定', '妥善解决']
                    }
                ],
                relatedTopics: [
                    {
                        title: '公众参与环境决策的意义',
                        content: '厦门PX事件是中国公众成功参与环境决策的典型案例，推动了环境影响评价制度的完善和公众参与机制的建立，对中国环境治理和公民社会发展产生了深远影响。'
                    },
                    {
                        title: '工业项目选址与城市规划',
                        content: '本案例引发了对化工等高风险工业项目选址标准的重新思考，促进了"邻避效应"相关研究，推动政府在城市规划中更加重视环境风险因素和公众感受。'
                    },
                    {
                        title: '环境信息公开与社会沟通',
                        content: '事件后，中国环境信息公开取得显著进步，政府与社会的沟通机制也得到改善，为解决类似环境争议提供了新思路和新机制。'
                    }
                ]
            };
        } else if (query.includes('疫情') || query.includes('新冠') || query.includes('防控')) {
            // 新冠疫情防控相关时间线
            return {
                title: '中国新冠疫情防控政策演变',
                subtitle: '2020年至2023年中国疫情防控政策的关键节点',
                description: '新冠肺炎(COVID-19)疫情是21世纪全球重大公共卫生事件。本时间线梳理了中国疫情防控政策的演变过程，记录了从严格防控到逐步优化再到全面放开的政策变迁历程。',
                analysisDate: currentDate,
                heatValue: 92, // 热度
                sentiment: {
                    negative: 28,
                    neutral: 45,
                    positive: 27
                },
                timelineItems: [
                    {
                        day: '23',
                        month: '1月',
                        title: '武汉封城',
                        content: '湖北省武汉市启动离汉通道关闭措施，暂停城市公共交通，关闭机场、火车站离汉通道，防止疫情扩散。这是中国首次对一个拥有1100多万人口的特大城市采取封城措施。',
                        source: '湖北省防控指挥部',
                        tags: ['疫情初期', '严格防控']
                    },
                    {
                        day: '8',
                        month: '4月',
                        title: '武汉解封',
                        content: '经过76天的封城措施后，武汉市正式解除离汉通道管控，恢复对外交通，标志着中国疫情防控取得阶段性重要成果。',
                        source: '湖北省防控指挥部',
                        tags: ['阶段胜利', '恢复秩序']
                    },
                    {
                        day: '28',
                        month: '9月',
                        title: '"动态清零"策略确立',
                        content: '中国疾控中心专家在接受媒体采访时首次明确提出"动态清零"概念，即通过精准防控，快速发现并处置新发疫情，实现社会面清零的防控目标。这一策略随后成为中国防疫的基本方针。',
                        source: '中国疾控中心',
                        tags: ['政策方针', '精准防控']
                    },
                    {
                        day: '2',
                        month: '8月',
                        title: '德尔塔变异株应对',
                        content: '面对德尔塔变异株带来的挑战，国家卫健委召开专题会议，强调坚持"外防输入、内防反弹"总策略和"动态清零"总方针不动摇，并进一步完善了核酸检测、流调溯源、区域管控等防控措施。',
                        source: '国家卫健委',
                        tags: ['变异应对', '政策调整']
                    },
                    {
                        day: '5',
                        month: '12月',
                        title: '全面优化二十条',
                        content: '国务院联防联控机制发布《关于进一步优化新冠肺炎疫情防控措施 科学精准做好防控工作的通知》，推出二十条优化措施，包括缩短隔离时间、精简防控内容、优化核酸检测等，标志着防控政策开始调整。',
                        source: '国务院联防联控机制',
                        tags: ['政策优化', '科学精准']
                    },
                    {
                        day: '7',
                        month: '12月',
                        title: '新十条发布',
                        content: '国务院联防联控机制发布《关于进一步优化落实新冠肺炎疫情防控措施的通知》，推出十条优化措施，包括取消健康码、明确居家隔离、优化分类管理等，疫情防控进入新阶段。',
                        source: '国务院联防联控机制',
                        tags: ['重大转变', '逐步放开']
                    },
                    {
                        day: '8',
                        month: '1月',
                        title: '乙类乙管实施',
                        content: '新冠肺炎疫情防控转入乙类乙管，取消入境隔离和集中隔离，全面恢复正常出入境秩序，标志着中国疫情防控进入新阶段。',
                        source: '国家卫健委',
                        tags: ['政策转型', '全面放开']
                    },
                    {
                        day: '5',
                        month: '5月',
                        title: '取消所有防疫措施',
                        content: '各地全面取消新冠肺炎疫情相关防控措施，公共场所不再查验核酸检测结果，跨境旅行全面恢复正常，标志着中国疫情防控工作全面回归常态。',
                        source: '各地政府通告',
                        tags: ['常态化', '全面恢复']
                    }
                ],
                relatedTopics: [
                    {
                        title: '经济恢复与政策调整',
                        content: '疫情防控政策的调整与经济发展需求密切相关，从严格防控到逐步放开，体现了平衡疫情防控与经济发展的政策智慧。'
                    },
                    {
                        title: '全球防疫政策比较',
                        content: '中国疫情防控政策经历了从最严格到逐步放开的过程，与世界其他国家采取的防控策略有显著不同，各有利弊。'
                    },
                    {
                        title: '公共卫生体系建设',
                        content: '疫情防控推动了中国公共卫生体系的完善，包括疾病预防控制体系改革、突发公共卫生事件应急体系建设等方面取得重要进展。'
                    }
                ]
            };
        } else if (query.includes('中美') || query.includes('贸易') || query.includes('关税')) {
            // 中美贸易摩擦时间线
            return {
                title: '中美贸易摩擦发展历程',
                subtitle: '2018年至2023年中美经贸关系重要节点',
                description: '中美贸易摩擦是21世纪国际关系中的重要事件，涉及全球两大经济体之间的贸易政策调整、关税措施实施以及双边关系变化。本时间线记录了从摩擦爆发到阶段性缓和的关键事件。',
                analysisDate: currentDate,
                heatValue: 87,
                sentiment: {
                    negative: 40,
                    neutral: 45,
                    positive: 15
                },
                timelineItems: [
                    {
                        day: '22',
                        month: '3月',
                        title: '贸易摩擦爆发',
                        content: '美国总统特朗普签署备忘录，基于"301调查"结果，指令贸易代表对从中国进口的商品大规模征收关税，并限制中国企业对美投资并购。美方宣布对价值约500亿美元的中国输美商品加征25%的关税。',
                        source: '白宫官网',
                        tags: ['起始事件', '美方行动']
                    },
                    {
                        day: '2',
                        month: '4月',
                        title: '中方反制措施',
                        content: '中国国务院关税税则委员会决定对原产于美国的大豆、汽车、化工品等14类106项商品加征25%的关税，涉及23亿美元美国对华出口。',
                        source: '中国财政部',
                        tags: ['中方反制', '对等原则']
                    },
                    {
                        day: '15',
                        month: '6月',
                        title: '首批关税正式实施',
                        content: '美国贸易代表办公室发布声明，宣布对价值340亿美元的中国商品征收25%的关税，并于7月6日生效。中国商务部当日回应，对等采取反制措施。',
                        source: '美国贸易代表办公室',
                        tags: ['政策实施', '贸易受阻']
                    },
                    {
                        day: '23',
                        month: '8月',
                        title: '第二轮关税生效',
                        content: '美国对价值160亿美元的中国商品加征25%的关税，同日中国对同等规模的美国商品实施反制措施。至此，美国对500亿美元中国商品的加征关税计划全部落实。',
                        source: '美国贸易代表办公室',
                        tags: ['升级措施', '双方对抗']
                    },
                    {
                        day: '24',
                        month: '9月',
                        title: '关税战升级',
                        content: '美国对2000亿美元中国商品加征10%的关税，并计划2019年1月1日起提高到25%。中国对600亿美元美国商品加征5%-10%不等的关税作为反制。',
                        source: '美国贸易代表办公室',
                        tags: ['冲突升级', '影响扩大']
                    },
                    {
                        day: '1',
                        month: '12月',
                        title: '贸易战暂停升级',
                        content: '中美两国元首在阿根廷G20峰会期间举行会晤，达成共识，停止加征新的关税，双方工作团队将加紧磋商，朝着取消所有加征关税的方向努力。',
                        source: '中国外交部',
                        tags: ['暂时缓和', '重启对话']
                    },
                    {
                        day: '15',
                        month: '1月',
                        title: '第一阶段经贸协议签署',
                        content: '中美在华盛顿正式签署第一阶段经贸协议。根据协议，美方将履行分阶段取消对华产品加征关税的相关承诺，实现加征关税由升到降的转变。中方承诺扩大自美进口。',
                        source: '中国商务部',
                        tags: ['阶段协议', '部分缓和']
                    },
                    {
                        day: '17',
                        month: '11月',
                        title: '拜登政府对华贸易政策',
                        content: '美国总统拜登与中国国家主席习近平举行视频会晤，双方就经贸问题进行了沟通。美方表示不寻求改变中国体制，不强化意识形态对抗，不支持"台独"，无意与中国发生冲突。这被视为中美关系可能缓和的信号。',
                        source: '白宫官网',
                        tags: ['政策调整', '关系重建']
                    }
                ],
                relatedTopics: [
                    {
                        title: '全球供应链重构',
                        content: '贸易摩擦促使全球企业重新考虑供应链布局，部分产业开始从中国向东南亚等地区转移，影响了全球价值链结构。'
                    },
                    {
                        title: '科技竞争与合作',
                        content: '除贸易领域外，中美在科技领域的竞争日益加剧，特别是在5G、人工智能、半导体等高科技领域，双方既有激烈竞争也有不得不合作的领域。'
                    },
                    {
                        title: '经济全球化走向',
                        content: '中美贸易摩擦是经济全球化进程中的重要事件，反映了全球化面临的挑战和调整，对世界经济格局产生深远影响。'
                    }
                ]
            };
        } else {
            // 默认时间线数据
            return {
                title: query,
                subtitle: '舆情事件梳理分析结果',
                description: `这是关于"${query}"的舆情事件分析。本次分析基于最近30天内的社交媒体数据、新闻报道和官方声明，旨在客观呈现事件发展脉络和公众反应。`,
                analysisDate: currentDate,
                heatValue: Math.floor(60 + Math.random() * 35), // 60-95之间的随机热度
                sentiment: {
                    negative: Math.floor(20 + Math.random() * 30), // 20-50%
                    neutral: Math.floor(30 + Math.random() * 20), // 30-50%
                    positive: Math.floor(10 + Math.random() * 25) // 计算剩余部分
                },
                timelineItems: [
                    {
                        day: '15',
                        month: '6月',
                        title: '事件初始阶段',
                        content: `关于"${query}"的初始报道开始出现在主流媒体，引发了公众的初步关注和讨论。`,
                        source: '人民日报',
                        tags: ['官方声明', '高可信度']
                    },
                    {
                        day: '17',
                        month: '6月',
                        title: '事件发展',
                        content: `"${query}"相关话题在社交媒体上迅速传播，各方观点开始碰撞，讨论热度明显上升。`,
                        source: '新华社',
                        tags: ['官方通报']
                    },
                    {
                        day: '20',
                        month: '6月',
                        title: '舆论高峰期',
                        content: `"${query}"相关话题达到讨论高峰，微博热搜榜持续12小时，全网讨论量超过500万条。`,
                        source: '微博热搜',
                        tags: ['热点讨论', '社交媒体']
                    },
                    {
                        day: '22',
                        month: '6月',
                        title: '官方回应',
                        content: `针对"${query}"引发的公众关注，相关部门发布官方声明，澄清事实，平息争议。`,
                        source: '国务院新闻办公室',
                        tags: ['权威声明', '最高可信度']
                    }
                ],
                relatedTopics: [
                    {
                        title: '政策解读',
                        content: `与"${query}"相关的政策背景和影响分析，包括历史沿革和未来趋势预测。`
                    },
                    {
                        title: '公众反应',
                        content: `公众对"${query}"的主要反应和情感倾向分析，涵盖不同群体的观点差异。`
                    },
                    {
                        title: '专家观点',
                        content: `来自学界、业界和政府的专家对"${query}"事件的专业解读和评估。`
                    }
                ]
            };
        }
    } else if (mode === 'factcheck') {
        return {
            title: query,
            subtitle: '新闻事实核查分析结果',
            checkDate: currentDate,
            verdict: {
                type: 'partially-true',
                text: '部分属实'
            },
            claimContent: `近期网络流传关于"${query}"的消息称：${generateRandomClaim(query)}。该消息在社交媒体平台引发广泛传播和讨论。`,
            claimSource: `来源：某新闻网站 - ${getPastDate(5)}`,
            verdictContent: `基于我们的分析和查证，关于"${query}"的消息部分属实。某些关键信息确实准确，但也存在一些误导性表述或缺乏上下文的情况。`,
            evidenceItems: [
                {
                    title: '官方数据核实',
                    type: 'true',
                    typeText: '确认属实',
                    content: `通过查询相关官方数据库和记录，确认有关"${query}"的部分数据陈述是准确的，特别是关于${generateRandomFactDetail(query, true)}的部分。`,
                    source: `数据来源：国家统计局 - ${getPastDate(30)}数据报告`
                },
                {
                    title: '事件当事人回应',
                    type: 'false',
                    typeText: '证伪',
                    content: `涉事方已通过官方渠道发表声明，明确否认了"${query}"中关于${generateRandomFactDetail(query, false)}的说法。根据当事人提供的证据可以确认这部分内容不实。`,
                    source: `来源：当事人官方声明 - ${getPastDate(3)}`
                },
                {
                    title: '历史记录对比',
                    type: 'partially-true',
                    typeText: '部分属实',
                    content: `通过历史记录和档案资料比对，"${query}"相关事件确实发生过，但时间线存在错误，且某些细节被夸大或简化，导致整体叙述存在偏差。`,
                    source: '数据来源：国家档案馆相关历史记录'
                }
            ],
            conclusion: `通过对"${query}"相关多方面证据的综合分析，我们认为该消息部分属实。其中关于${generateRandomFactDetail(query, true)}的描述基本准确，关于${generateRandomFactDetail(query, false)}的描述则存在明显误导。公众在接收此类信息时应保持批判思维。`,
            suggestions: [
                '关注信息来源的可靠性和权威性',
                '留意报道中是否包含确切的时间、地点和数据',
                '对极端性、情绪化的表述保持警惕',
                '查找多个渠道的报道进行交叉验证'
            ]
        };
    }
}

// 生成随机声明内容
function generateRandomClaim(topic) {
    const claims = [
        `${topic}将在下个月实施全新政策，影响范围覆盖全国各省市`,
        `知情人士透露，${topic}背后存在重大利益关系，涉及多方势力`,
        `专家警告${topic}可能带来严重后果，相关部门已开始调查`,
        `最新研究显示，${topic}正在以前所未有的速度发展，引发担忧`,
        `有报道称${topic}事件中的关键人物已经承认之前的声明有误导性`
    ];
    return claims[Math.floor(Math.random() * claims.length)];
}

// 生成随机事实细节
function generateRandomFactDetail(topic, isTrue) {
    const trueDetails = [
        `相关数据趋势`,
        `基本事件经过`,
        `主要参与方`,
        `官方发布的基础信息`,
        `事件发生的时间范围`
    ];
    
    const falseDetails = [
        `具体影响范围`,
        `某些参与方的动机`,
        `事件的经济损失`,
        `后续发展预测`,
        `特定个人的言论`
    ];
    
    const details = isTrue ? trueDetails : falseDetails;
    return details[Math.floor(Math.random() * details.length)];
}

// 获取过去日期的格式化字符串
function getPastDate(daysAgo) {
    const past = new Date();
    past.setDate(past.getDate() - daysAgo);
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    return past.toLocaleDateString('zh-CN', options);
}

// 添加滚动动画效果
function addScrollAnimations() {
    const animateOnScroll = () => {
        const elements = document.querySelectorAll('.timeline-item, .evidence-item, .topic-card');
        
        elements.forEach(element => {
            const elementTop = element.getBoundingClientRect().top;
            const elementVisible = 150;
            
            if (elementTop < window.innerHeight - elementVisible) {
                element.classList.add('visible');
            } else {
                element.classList.remove('visible');
            }
        });
    };
    
    // 初始触发一次
    window.animateOnScroll = animateOnScroll;
    setTimeout(animateOnScroll, 200);
    
    // 监听滚动事件
    window.addEventListener('scroll', animateOnScroll);
}

// 切换模式按钮的增强功能
const modeButtons = document.querySelectorAll('.mode-btn');
if (modeButtons.length) {
    modeButtons.forEach(button => {
        button.addEventListener('click', function() {
            const active = document.querySelector('.mode-btn.active');
            if (active) active.classList.remove('active');
            
            this.classList.add('active');
            
            // 更新模式滑块位置
            const slider = document.querySelector('.mode-slider');
            if (slider) {
                const index = Array.from(modeButtons).indexOf(this);
                slider.style.transform = `translateX(${index * 100}%)`;
            }
            
            // 更新标题和描述显示
            const mode = this.getAttribute('data-mode');
            document.querySelectorAll('.mode-title, .mode-description').forEach(el => {
                el.style.display = 'none';
            });
            
            document.querySelectorAll(`.${mode}-title, .${mode}-description`).forEach(el => {
                el.style.display = 'block';
            });
            
            // 添加过渡动画
            const inputSection = document.querySelector('.input-section');
            if (inputSection) {
                inputSection.classList.add('mode-transition');
                setTimeout(() => {
                    inputSection.classList.remove('mode-transition');
                }, 500);
            }
        });
    });
}

// 清空输入按钮功能
const clearInputBtn = document.querySelector('.clear-input');
const eventInput = document.getElementById('event-input');

if (clearInputBtn && eventInput) {
    clearInputBtn.addEventListener('click', function() {
        eventInput.value = '';
        eventInput.focus();
        
        // 添加清空动画
        this.classList.add('rotate');
        setTimeout(() => {
            this.classList.remove('rotate');
        }, 300);
    });
    
    // 根据输入内容显示/隐藏清空按钮
    eventInput.addEventListener('input', function() {
        if (this.value.trim() !== '') {
            clearInputBtn.style.opacity = '1';
            clearInputBtn.style.visibility = 'visible';
        } else {
            clearInputBtn.style.opacity = '0';
            clearInputBtn.style.visibility = 'hidden';
        }
    });
    
    // 初始化时检查
    if (eventInput.value.trim() !== '') {
        clearInputBtn.style.opacity = '1';
        clearInputBtn.style.visibility = 'visible';
    } else {
        clearInputBtn.style.opacity = '0';
        clearInputBtn.style.visibility = 'hidden';
    }
} 