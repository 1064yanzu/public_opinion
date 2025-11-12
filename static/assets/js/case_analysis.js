// 模拟数据（使用真实案例）
const mockCases = [
    {
        id: 1,
        title: "政府网络舆情应对失策——以“成都四十九中学生坠亡”事件为例",
        type: "政府舆情",
        result: "failure",
        date: "2021-05-09",
        summary: "2021年5月9日，成都四十九中一名学生在校内坠亡。事件发生后，家长在微博发文质疑学校和政府部门的处理方式，引发公众关注和讨论。由于相关部门的回应不及时且信息披露不足，导致网络负面舆情迅速扩散，对政府公信力造成严重影响。",
        metrics: {
            duration: "5天",
            influence: 95,
            sentiment: -0.8,
            engagement: 500000
        },
        timeline: [
            {
                phase: "酝酿扩散期",
                date: "2021-05-09 18:40",
                description: "学生坠亡消息在微博上曝光，起初公众认为是意外事故，未引起广泛关注。",
                influence: 0.2,
                sentiment: -0.2
            },
            {
                phase: "爆发蔓延期",
                date: "2021-05-10 12:32",
                description: "坠亡学生的母亲在微博发文质疑，引发公众关注和大量转发，舆情进入首次高潮。",
                influence: 0.8,
                sentiment: -0.7
            },
            {
                phase: "反复波动期",
                date: "2021-05-11",
                description: "官方发布通报，但信息披露不足，公众质疑不断，负面舆情持续发酵。",
                influence: 0.95,
                sentiment: -0.9
            },
            {
                phase: "衰减消退期",
                date: "2021-05-13",
                description: "官方媒体详细披露事件真相，澄清谣言，舆情逐渐平息，公众态度回归理性。",
                influence: 0.6,
                sentiment: -0.3
            }
        ],
        lessons: [
            {
                title: "及时回应公众关切",
                content: "在舆情初期，政府应主动、及时地披露信息，满足公众知情权，防止谣言滋生。",
                importance: "high"
            },
            {
                title: "信息透明与人文关怀",
                content: "信息发布应注重细节和温度，体现对当事人的关怀和对公众的尊重，增强公信力。",
                importance: "high"
            },
            {
                title: "优化舆情应对机制",
                content: "建立健全网络舆情监测和应对机制，提高政府部门的网络治理能力和水平。",
                importance: "medium"
            }
        ],
        trends: {
            dates: ["05-09", "05-10", "05-11", "05-12", "05-13"],
            influence: [0.2, 0.8, 0.95, 0.8, 0.6],
            sentiment: [-0.2, -0.7, -0.9, -0.5, -0.3]
        },
        wordCloudData: [
            { name: "坠亡", value: 1000 },
            { name: "家长质疑", value: 800 },
            { name: "信息公开", value: 600 },
            { name: "官方回应", value: 400 },
            { name: "舆情发酵", value: 300 },
            { name: "政府公信力", value: 200 },
            { name: "谣言", value: 100 }
            // 更多关键词...
        ]
    }
    // 可以添加更多案例...
];

// 工具函数（保持不变）
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
        this.initializeWordCloud(caseItem);
    }

    generateDetailModalContent(caseItem) {
        return `
            <div class="modal-content">
                <span class="modal-close">&times;</span>
                <h2>${caseItem.title}</h2>
                <p>${caseItem.summary}</p>
                <h3>事件趋势</h3>
                <div id="trendChart" style="width: 100%; height: 400px; margin-bottom: 20px;"></div>
                <h3>热词分析</h3>
                <div id="wordCloud" style="width: 100%; height: 400px; margin-bottom: 20px;"></div>
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
                text: '舆情发展趋势',
                left: 'center'
            },
            tooltip: {
                trigger: 'axis'
            },
            legend: {
                data: ['影响力', '情感指数'],
                top: 30
            },
            grid: {
                left: '3%',
                right: '4%',
                bottom: '10%',
                containLabel: true
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

    initializeWordCloud(caseItem) {
        const chartDom = document.getElementById('wordCloud');
        const myChart = echarts.init(chartDom);
        const option = {
            title: {
                text: '舆情热词分析',
                left: 'center'
            },
            tooltip: {},
            series: [{
                type: 'wordCloud',
                gridSize: 10,
                sizeRange: [12, 50],
                rotationRange: [-45, 45],
                shape: 'circle',
                width: '100%',
                height: '100%',
                textStyle: {
                    color: function() {
                        return 'rgb(' + [
                            Math.round(Math.random() * 160),
                            Math.round(Math.random() * 160),
                            Math.round(Math.random() * 160)
                        ].join(',') + ')';
                    }
                },
                data: caseItem.wordCloudData
            }]
        };
        myChart.setOption(option);
    }
}

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    new CaseAnalysis();
});