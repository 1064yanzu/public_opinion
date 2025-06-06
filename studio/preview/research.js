/**
 * ClarityStudio 舆情研究台交互脚本
 */

document.addEventListener('DOMContentLoaded', function() {
    // 初始化变量
    const body = document.body;
    const modeButtons = document.querySelectorAll('.mode-btn');
    const advancedOptions = document.querySelector('.advanced-options');
    const optionToggle = document.querySelector('.option-toggle');
    const clearInput = document.querySelector('.clear-input');
    const eventInput = document.getElementById('event-input');
    const analyzeBtn = document.getElementById('analyze-btn');
    const queryItems = document.querySelectorAll('.query-item');
    
    const timelineResult = document.querySelector('.timeline-result');
    const factcheckResult = document.querySelector('.factcheck-result');
    const emptyState = document.querySelector('.empty-state');
    
    // 设置当前模式
    let currentMode = 'timeline'; // 默认为舆情事件梳理模式
    body.setAttribute('data-mode', currentMode);
    
    // 模式切换
    modeButtons.forEach(button => {
        button.addEventListener('click', function() {
            // 移除所有按钮的活跃状态
            modeButtons.forEach(btn => btn.classList.remove('active'));
            
            // 添加当前按钮的活跃状态
            this.classList.add('active');
            
            // 更新当前模式
            currentMode = this.getAttribute('data-mode');
            body.setAttribute('data-mode', currentMode);
            
            // 更新输入框提示文本
            if (currentMode === 'timeline') {
                eventInput.placeholder = '请输入舆情事件...';
            } else {
                eventInput.placeholder = '请输入需要核查的新闻...';
            }
            
            // 重置结果区域
            resetResults();
        });
    });
    
    // 高级选项展开/收起
    optionToggle.addEventListener('click', function() {
        advancedOptions.classList.toggle('open');
    });
    
    // 清空输入框
    clearInput.addEventListener('click', function() {
        eventInput.value = '';
        eventInput.focus();
    });
    
    // 最近查询项点击
    queryItems.forEach(item => {
        item.addEventListener('click', function() {
            const queryText = this.getAttribute('data-query');
            eventInput.value = queryText;
            
            // 模拟分析点击
            simulateAnalysis();
        });
    });
    
    // 分析按钮点击
    analyzeBtn.addEventListener('click', function() {
        if (eventInput.value.trim() === '') {
            // 输入为空，显示提示
            eventInput.classList.add('error');
            setTimeout(() => {
                eventInput.classList.remove('error');
            }, 1000);
            return;
        }
        
        // 执行分析
        performAnalysis();
    });
    
    // 回车键提交
    eventInput.addEventListener('keyup', function(event) {
        if (event.key === 'Enter') {
            analyzeBtn.click();
        }
    });
    
    // 模拟分析过程
    function performAnalysis() {
        // 显示加载状态
        analyzeBtn.classList.add('loading');
        
        // 模拟加载延迟
        setTimeout(() => {
            // 移除加载状态
            analyzeBtn.classList.remove('loading');
            
            // 显示分析结果
            showResults();
            
        }, 1800); // 模拟1.8秒的加载时间
    }
    
    // 模拟最近查询的快速分析
    function simulateAnalysis() {
        // 显示加载状态
        analyzeBtn.classList.add('loading');
        
        // 较短的加载延迟
        setTimeout(() => {
            // 移除加载状态
            analyzeBtn.classList.remove('loading');
            
            // 显示分析结果
            showResults();
            
        }, 800); // 模拟0.8秒的加载时间
    }
    
    // 显示分析结果
    function showResults() {
        // 隐藏空状态
        emptyState.style.display = 'none';
        
        // 根据当前模式显示相应结果
        if (currentMode === 'timeline') {
            timelineResult.style.display = 'block';
            factcheckResult.style.display = 'none';
            
            // 填充时间线结果数据
            populateTimelineData();
        } else {
            timelineResult.style.display = 'none';
            factcheckResult.style.display = 'block';
            
            // 填充事实核查结果数据
            populateFactcheckData();
        }
        
        // 更新结果标题
        updateResultsTitle();
    }
    
    // 重置结果区域
    function resetResults() {
        timelineResult.style.display = 'none';
        factcheckResult.style.display = 'none';
        emptyState.style.display = 'flex';
        
        // 重置结果标题
        document.getElementById('results-title').textContent = '等待您的查询...';
        document.getElementById('results-subtitle').textContent = '在左侧输入您感兴趣的舆情事件或需要核查的新闻';
    }
    
    // 更新结果标题
    function updateResultsTitle() {
        const query = eventInput.value.trim();
        
        if (currentMode === 'timeline') {
            document.getElementById('results-title').textContent = `"${query}" 舆情分析`;
            document.getElementById('results-subtitle').textContent = '以下是该事件的舆情分析和时间线梳理';
            
            // 更新事件标题
            document.getElementById('event-title').textContent = query;
        } else {
            document.getElementById('results-title').textContent = `"${query}" 事实核查`;
            document.getElementById('results-subtitle').textContent = '以下是该新闻的事实核查结果';
            
            // 更新核查标题
            document.getElementById('claim-title').textContent = query;
        }
    }
    
    // 填充时间线数据
    function populateTimelineData() {
        // 这里可以通过API获取真实数据，现在使用模拟数据
        
        // 更新事件描述
        const eventDescriptions = [
            '这是一起引发广泛社会关注的舆情事件，涉及多方利益相关者。事件从微博平台发酵，迅速扩散至全网，引发了关于社会治理、公共政策和信息透明度的讨论。',
            '这是近期社交媒体热议的焦点事件，涉及多个方面的争议和讨论。事件经历了从曝光到发酵再到官方回应的完整过程，反映了当前社会治理中的若干挑战。',
            '该事件是近期公众关注的热点话题，在社交媒体平台引发大量讨论和争议。事件迅速发展，多方参与表态，反映出公众对相关议题的高度关注。'
        ];
        
        document.getElementById('event-description').textContent = eventDescriptions[Math.floor(Math.random() * eventDescriptions.length)];
        
        // 更新热度指数
        const heatValue = Math.floor(Math.random() * 30) + 70; // 70-99之间
        document.getElementById('heat-value').textContent = heatValue;
        document.querySelector('.heat-level').style.width = `${heatValue}%`;
        
        // 更新情感倾向
        const negative = Math.floor(Math.random() * 40) + 10; // 10-49
        const positive = Math.floor(Math.random() * 30) + 10; // 10-39
        const neutral = 100 - negative - positive;
        
        document.querySelector('.sentiment-bar.negative').style.width = `${negative}%`;
        document.querySelector('.sentiment-bar.negative').textContent = `${negative}%`;
        document.querySelector('.sentiment-bar.neutral').style.width = `${neutral}%`;
        document.querySelector('.sentiment-bar.neutral').textContent = `${neutral}%`;
        document.querySelector('.sentiment-bar.positive').style.width = `${positive}%`;
        document.querySelector('.sentiment-bar.positive').textContent = `${positive}%`;
        
        // 更新分析日期
        const today = new Date();
        const dateString = `${today.getFullYear()}年${today.getMonth() + 1}月${today.getDate()}日`;
        document.getElementById('analysis-date').textContent = dateString;
    }
    
    // 填充事实核查数据
    function populateFactcheckData() {
        // 这里可以通过API获取真实数据，现在使用模拟数据
        
        // 随机选择一个核查结果：真、假、部分真实
        const verdicts = ['true', 'false', 'partially-true'];
        const verdictTexts = {
            'true': '确认属实',
            'false': '确认不实',
            'partially-true': '部分属实'
        };
        
        const randomVerdict = verdicts[Math.floor(Math.random() * verdicts.length)];
        const factcheckBadge = document.querySelector('.factcheck-badge');
        
        // 更新徽章状态
        factcheckBadge.setAttribute('data-verdict', randomVerdict);
        factcheckBadge.querySelector('.verdict-text').textContent = verdictTexts[randomVerdict];
        
        // 更新核查内容
        document.getElementById('claim-content').textContent = eventInput.value.trim();
        
        // 根据不同的核查结果显示不同的结论
        const verdictContents = {
            'true': '经过多方查证和权威信息核实，该新闻报道内容属实。新闻中的关键信息、数据和事件描述均与事实相符，未发现明显虚假或误导性表述。',
            'false': '经过多方查证和权威信息核实，该新闻报道内容不实。新闻中的主要信息与实际情况不符，存在明显错误或捏造的内容，可能对公众造成误导。',
            'partially-true': '经过多方查证和权威信息核实，该新闻内容部分属实。新闻中有部分信息与事实相符，但也存在一些错误、夸大或缺乏上下文的描述，读者需要谨慎判断。'
        };
        
        document.getElementById('verdict-content').textContent = verdictContents[randomVerdict];
        
        // 更新核查日期
        const today = new Date();
        const dateString = `${today.getFullYear()}年${today.getMonth() + 1}月${today.getDate()}日`;
        document.getElementById('check-date').textContent = dateString;
    }
    
    // 添加结果行动按钮交互效果
    const actionButtons = document.querySelectorAll('.action-btn');
    actionButtons.forEach(button => {
        button.addEventListener('click', function() {
            // 添加按钮点击效果
            this.classList.add('pulse-effect');
            setTimeout(() => {
                this.classList.remove('pulse-effect');
            }, 500);
            
            // 根据按钮类型执行不同操作
            const action = this.getAttribute('title');
            
            if (action === '导出为PDF') {
                // 模拟导出功能
                alert('PDF导出功能即将上线，敬请期待！');
            } else if (action === '分享结果') {
                // 模拟分享功能
                alert('分享功能即将上线，敬请期待！');
            } else if (action === '刷新分析') {
                // 刷新分析
                performAnalysis();
            }
        });
    });
    
    // 深色模式检测
    const darkModeMedia = window.matchMedia('(prefers-color-scheme: dark)');
    function applyTheme(isDark) {
        if (isDark) {
            document.body.classList.add('dark-mode');
        } else {
            document.body.classList.remove('dark-mode');
        }
    }
    
    // 初始应用主题
    applyTheme(darkModeMedia.matches);
    
    // 监听系统主题变化
    darkModeMedia.addEventListener('change', e => {
        applyTheme(e.matches);
    });
    
    // 为导航链接添加平滑滚动效果
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                window.scrollTo({
                    top: targetElement.offsetTop - 80,
                    behavior: 'smooth'
                });
            }
        });
    });
}); 