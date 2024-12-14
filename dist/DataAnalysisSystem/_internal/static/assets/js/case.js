// 模拟数据
const mockCases = [
    {
        id: 1,
        title: "某高校食品安全事件舆情分析",
        type: "教育舆情",
        result: "success",
        date: "2023-05-15",
        summary: "某高校食堂发生食品安全问题，引发学生群体关注和讨论...",
        metrics: {
            duration: "72小时",
            influence: 85,
            sentiment: -0.6,
            engagement: 12500
        },
        timeline: [
            {
                phase: "事件爆发",
                date: "2023-05-15 08:30",
                description: "学生在社交媒体发布食堂食品安全问题...",
                influence: 0.3,
                sentiment: -0.8
            },
            {
                phase: "快速响应",
                date: "2023-05-15 10:00",
                description: "校方发布初步调查声明...",
                influence: 0.6,
                sentiment: -0.4
            },
            {
                phase: "危机处理",
                date: "2023-05-16 14:00",
                description: "召开新闻发布会...",
                influence: 0.8,
                sentiment: 0.2
            },
            {
                phase: "事件总结",
                date: "2023-05-18 09:00",
                description: "发布整改报告...",
                influence: 0.4,
                sentiment: 0.6
            }
        ],
        lessons: [
            {
                title: "及时回应至关重要",
                content: "在舆情初期及时发声...",
                importance: "high"
            },
            {
                title: "保持信息透明",
                content: "全程保持信息公开透明...",
                importance: "high"
            },
            {
                title: "建立长效机制",
                content: "建立食品安全长效监管机制...",
                importance: "medium"
            }
        ],
        trends: {
            dates: ["05-15", "05-16", "05-17", "05-18"],
            influence: [0.3, 0.8, 0.6, 0.4],
            sentiment: [-0.8, -0.4, 0.2, 0.6]
        }
    }
    // 可以添加更多案例...
];

// 工具函数
const debounce = (func, wait) => {
    let timeout;
    return function executedFunction(...args) {
        const context = this;
        const later = () => {
            clearTimeout(timeout);
            func.apply(context, args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
};

// 主要功能类
class CaseAnalysis {
    constructor() {
        this.cases = mockCases;
        this.initializeElements();
        this.bindEvents();
        this.filterCases();
    }

    initializeElements() {
        this.searchInput = document.getElementById('searchInput');
        this.caseTypeSelect = document.getElementById('caseType');
        this.resultRadios = document.getElementsByName('result');
        this.startDateInput = document.getElementById('startDate');
        this.endDateInput = document.getElementById('endDate');
        this.applyFilterBtn = document.getElementById('applyFilter');
        this.casesContainer = document.getElementById('casesContainer');
    }

    bindEvents() {
        this.searchInput.addEventListener('input', debounce(() => {
            this.filterCases();
        }, 300));

        this.caseTypeSelect.addEventListener('change', () => {
            this.filterCases();
        });

        this.resultRadios.forEach(radio => {
            radio.addEventListener('change', () => {
                this.filterCases();
            });
        });

        this.startDateInput.addEventListener('change', () => {
            this.filterCases();
        });

        this.endDateInput.addEventListener('change', () => {
            this.filterCases();
        });

        this.applyFilterBtn.addEventListener('click', () => {
            this.filterCases();
        });
    }

    filterCases() {
        const searchTerm = this.searchInput.value.trim().toLowerCase();
        const selectedType = this.caseTypeSelect.value;
        const selectedResult = Array.from(this.resultRadios).find(radio => radio.checked).value;
        const startDate = this.startDateInput.value;
        const endDate = this.endDateInput.value;

        const filteredCases = this.cases.filter(caseItem => {
            const matchesSearch = caseItem.title.toLowerCase().includes(searchTerm) || caseItem.summary.toLowerCase().includes(searchTerm);
            const matchesType = selectedType ? caseItem.type === selectedType : true;
            const matchesResult = selectedResult !== "all" ? caseItem.result === selectedResult : true;
            const caseDate = new Date(caseItem.date);
            const matchesStartDate = startDate ? caseDate >= new Date(startDate) : true;
            const matchesEndDate = endDate ? caseDate <= new Date(endDate) : true;
            return matchesSearch && matchesType && matchesResult && matchesStartDate && matchesEndDate;
        });

        this.renderCases(filteredCases);
    }

    renderCases(cases = []) {
        this.casesContainer.innerHTML = "";

        if (cases.length === 0) {
            this.casesContainer.innerHTML = "<p>未找到符合条件的案例。</p>";
            return;
        }

        cases.forEach(caseItem => {
            const card = this.generateCaseCard(caseItem);
            this.casesContainer.appendChild(card);
        });
    }

    generateCaseCard(caseItem) {
        const card = document.createElement("div");
        card.classList.add("case-card");
        card.innerHTML = `
            <h3 class="case-title">${caseItem.title}</h3>
            <p class="case-summary">${caseItem.summary}</p>
            <div class="case-tags">
                <span class="case-tag">${caseItem.type}</span>
                <span class="case-tag">${caseItem.date}</span>
            </div>
            <button class="details-button" data-id="${caseItem.id}">查看详情</button>
        `;

        const detailsButton = card.querySelector(".details-button");
        detailsButton.addEventListener("click", () => {
            this.showDetails(caseItem.id);
        });

        return card;
    }

    showDetails(caseId) {
        const caseItem = this.cases.find(item => item.id === caseId);
        if (!caseItem) return;

        const modalContent = this.generateDetailModalContent(caseItem);

        // 创建模态框
        const modal = document.createElement("div");
        modal.classList.add("modal");
        modal.innerHTML = modalContent;

        // 关闭按钮功能
        const closeButton = modal.querySelector(".modal-close");
        closeButton.addEventListener("click", () => {
            document.body.removeChild(modal);
        });

        // 点击遮罩层关闭
        modal.addEventListener("click", (e) => {
            if (e.target === modal) {
                document.body.removeChild(modal);
            }
        });

        document.body.appendChild(modal);

        // 初始化图表
        this.initializeCharts(caseItem);
    }

    generateDetailModalContent(caseItem) {
        return `
            <div class="modal-content">
                <span class="modal-close">&times;</span>
                <h2>${caseItem.title}</h2>
                <p>${caseItem.summary}</p>
                <h3>事件趋势</h3>
                <div id="trendChart" style="width: 100%; height: 400px;"></div>
                <h3>时间线</h3>
                ${this.generateTimeline(caseItem.timeline)}
                <h3>经验教训</h3>
                ${this.generateLessons(caseItem.lessons)}
            </div>
        `;
    }

    generateTimeline(timeline) {
        let timelineHtml = '<ul class="timeline">';
        timeline.forEach(event => {
            timelineHtml += `
                <li>
                    <h4>${event.phase} - ${event.date}</h4>
                    <p>${event.description}</p>
                </li>
            `;
        });
        timelineHtml += '</ul>';
        return timelineHtml;
    }

    generateLessons(lessons) {
        let lessonsHtml = '<ul class="lessons">';
        lessons.forEach(lesson => {
            lessonsHtml += `
                <li>
                    <h4>${lesson.title}</h4>
                    <p>${lesson.content}</p>
                </li>
            `;
        });
        lessonsHtml += '</ul>';
        return lessonsHtml;
    }

    initializeCharts(caseItem) {
        const chartDom = document.getElementById('trendChart');
        const myChart = echarts.init(chartDom);
        const option = {
            title: {
                text: '舆情发展趋势'
            },
            tooltip: {
                trigger: 'axis'
            },
            legend: {
                data: ['影响力', '情感指数']
            },
            xAxis: {
                type: 'category',
                data: caseItem.trends.dates
            },
            yAxis: [
                {
                    type: 'value',
                    name: '影响力',
                    position: 'left'
                },
                {
                    type: 'value',
                    name: '情感指数',
                    position: 'right'
                }
            ],
            series: [
                {
                    name: '影响力',
                    type: 'line',
                    data: caseItem.trends.influence
                },
                {
                    name: '情感指数',
                    type: 'line',
                    yAxisIndex: 1,
                    data: caseItem.trends.sentiment
                }
            ]
        };
        myChart.setOption(option);
    }
}

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    new CaseAnalysis();
});