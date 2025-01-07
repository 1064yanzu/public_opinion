class CaseAnalysis {
    constructor() {
        this.bindEvents();
        this.loadCases();
    }

    bindEvents() {
        // 绑定筛选和搜索事件
        document.getElementById('typeFilter')?.addEventListener('change', () => this.loadCases());
        document.getElementById('resultFilter')?.addEventListener('change', () => this.loadCases());
        
        // 搜索框防抖
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            searchInput.addEventListener('input', this.debounce(() => this.loadCases(), 500));
        }

        // 案例卡片点击事件（使用事件委托）
        document.getElementById('caseList')?.addEventListener('click', (e) => {
            const card = e.target.closest('.case-card');
            if (card) {
                const caseId = card.dataset.caseId;
                if (caseId) {
                    this.showCaseDetail(caseId);
                }
            }
        });
    }

    async loadCases() {
        try {
            const type = document.getElementById('typeFilter')?.value || '';
            const result = document.getElementById('resultFilter')?.value || '';
            const keyword = document.getElementById('searchInput')?.value || '';

            const params = new URLSearchParams({
                type,
                result,
                keyword
            });

            const response = await fetch(`/new-api/cases?${params}`);
            const data = await response.json();

            if (data.code === 200) {
                this.renderCases(data.data);
            } else {
                this.showError(data.message || '获取案例列表失败');
            }
        } catch (error) {
            console.error('加载案例失败:', error);
            this.showError('网络错误，请稍后重试');
        }
    }

    async showCaseDetail(caseId) {
        try {
            const response = await fetch(`/new-api/cases/${caseId}`);
            const data = await response.json();

            if (data.code === 200) {
                this.renderCaseDetail(data.data);
            } else if (data.code === 404) {
                this.showError('未找到该案例');
            } else {
                this.showError(data.message || '获取案例详情失败');
            }
        } catch (error) {
            console.error('获取案例详情失败:', error);
            this.showError('网络错误，请稍后重试');
        }
    }

    renderCases(cases) {
        const container = document.getElementById('caseList');
        if (!container) return;

        if (!cases.length) {
            container.innerHTML = '<div class="no-data">暂无匹配的案例</div>';
            return;
        }

        container.innerHTML = cases.map(case_ => `
            <div class="case-card" data-case-id="${case_.id}">
                <h3>${case_.title}</h3>
                <div class="case-info">
                    <span class="case-type">${case_.type}</span>
                    <span class="case-result ${case_.result}">${case_.result === 'success' ? '处理成功' : '处理失败'}</span>
                </div>
                <p class="case-summary">${case_.summary}</p>
                <div class="case-meta">
                    <span>发生时间: ${case_.date}</span>
                    <span>持续: ${case_.duration}</span>
                    <span>阅读量: ${case_.readCount}</span>
                </div>
            </div>
        `).join('');
    }

    renderCaseDetail(case_) {
        const modal = document.getElementById('caseModal');
        if (!modal) return;

        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h2>${case_.title}</h2>
                    <span class="close" onclick="document.getElementById('caseModal').style.display='none'">&times;</span>
                </div>
                <div class="modal-body">
                    <div class="case-background">
                        <h3>事件背景</h3>
                        <p>${case_.background}</p>
                    </div>
                    <div class="case-timeline">
                        <h3>事件时间线</h3>
                        ${case_.timeline.map(item => `
                            <div class="timeline-item">
                                <div class="time">${item.time}</div>
                                <div class="phase">${item.phase}</div>
                                <div class="content">${item.content}</div>
                            </div>
                        `).join('')}
                    </div>
                    <div class="case-analysis">
                        <div class="problems">
                            <h3>存在问题</h3>
                            <ul>
                                ${case_.problems.map(problem => `<li>${problem}</li>`).join('')}
                            </ul>
                        </div>
                        <div class="solutions">
                            <h3>解决方案</h3>
                            <ul>
                                ${case_.solutions.map(solution => `<li>${solution}</li>`).join('')}
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        `;
        modal.style.display = 'block';
    }

    showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.textContent = message;
        document.body.appendChild(errorDiv);
        setTimeout(() => errorDiv.remove(), 3000);
    }

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
}

// 初始化
const caseAnalysis = new CaseAnalysis();
