        // 全局变量，用于存储图表实例
        let chinaHeatmap, sentimentPie, genderPie;

        function initAllCharts() {
            // 确保中国地图数据已加载
            if (typeof echarts.getMap('china') === 'undefined') {
                console.error('中国地图数据未加载');
                return;
            }

            // 初始化图表
            chinaHeatmap = echarts.init(document.getElementById('map'));
            sentimentPie = echarts.init(document.getElementById('sentiment-pie'));
            genderPie = echarts.init(document.getElementById('gender-pie'));

            // 设置初始选项
            chinaHeatmap.setOption(getChartOption('china'));
            sentimentPie.setOption(getChartOption('sentiment'));
            genderPie.setOption(getChartOption('gender'));

            // 首次更新图表数据
            updateCharts();

            // 添加窗口resize事件监听
            window.addEventListener('resize', function() {
                chinaHeatmap.resize();
                sentimentPie.resize();
                genderPie.resize();
            });

            console.log('所有图表初始化完成');
        }

        function getChartOption(type) {
            const isMobile = window.innerWidth <= 768;
            
            switch(type) {
                case 'china':
                    return {
                        tooltip: {
                            trigger: 'item'
                        },
                        visualMap: {
                            min: 0,
                            max: 1000,
                            left: isMobile ? 'center' : 'left',
                            bottom: isMobile ? 10 : 'bottom',
                            text: ['高', '低'],
                            calculable: true,
                            orient: isMobile ? 'horizontal' : 'vertical',
                            inRange: {
                                color: ['#e6f7ff', '#1890ff']
                            }
                        },
                        series: [
                            {
                                name: '热力值',
                                type: 'map',
                                map: 'china',
                                roam: true,
                                label: {
                                    show: !isMobile,
                                    fontSize: isMobile ? 8 : 12
                                },
                                emphasis: {
                                    label: {
                                        show: true,
                                        fontSize: isMobile ? 10 : 14
                                    }
                                },
                                data: []
                            }
                        ]
                    };
                case 'sentiment':
                    return {
                        tooltip: {
                            trigger: 'item',
                            formatter: '{a} <br/>{b}: {c} ({d}%)'
                        },
                        series: [
                            {
                                name: '情感分析',
                                type: 'pie',
                                radius: isMobile ? ['30%', '60%'] : ['40%', '70%'],
                                avoidLabelOverlap: true,
                                label: {
                                    show: true,
                                    position: isMobile ? 'inner' : 'outside',
                                    fontSize: isMobile ? 10 : 14
                                },
                                emphasis: {
                                    label: {
                                        show: true,
                                        fontSize: isMobile ? 12 : 18,
                                        fontWeight: 'bold'
                                    }
                                },
                                labelLine: {
                                    show: !isMobile
                                },
                                data: []
                            }
                        ]
                    };
                case 'gender':
                    return {
                        tooltip: {
                            trigger: 'item',
                            formatter: '{a} <br/>{b}: {c} ({d}%)'
                        },
                        series: [
                            {
                                name: '性别分布',
                                type: 'pie',
                                radius: isMobile ? '60%' : '70%',
                                label: {
                                    show: true,
                                    position: isMobile ? 'inner' : 'outside',
                                    fontSize: isMobile ? 10 : 14
                                },
                                data: [],
                                emphasis: {
                                    itemStyle: {
                                        shadowBlur: 10,
                                        shadowOffsetX: 0,
                                        shadowColor: 'rgba(0, 0, 0, 0.5)'
                                    },
                                    label: {
                                        show: true,
                                        fontSize: isMobile ? 12 : 16
                                    }
                                }
                            }
                        ]
                    };
            }
        }

        function updateCharts() {
            fetch('/page/api/chart-data')
                .then(response => {
                    if (!response.ok) {
                        throw new Error('网络响应不正常');
                    }
                    return response.json();
                })
                .then(data => {
                    // 更新热力图
                    chinaHeatmap.setOption({
                        series: [{
                            data: data.heatmapData
                        }]
                    });

                    // 更新情感分析图
                    const sentimentData = [
                        {name: '正面', value: data.sentimentData.正面, itemStyle: {color: '#52c41a'}},
                        {name: '负面', value: data.sentimentData.负面, itemStyle: {color: '#f5222d'}},
                        {name: '中性', value: data.sentimentData.中性, itemStyle: {color: '#faad14'}}
                    ];
                    sentimentPie.setOption({
                        series: [{
                            data: sentimentData
                        }]
                    });

                    // 更新性别分布图
                    const genderData = [
                        {name: '男', value: data.genderData.男, itemStyle: {color: '#1890ff'}},
                        {name: '女', value: data.genderData.女, itemStyle: {color: '#eb2f96'}}
                    ];
                    genderPie.setOption({
                        series: [{
                            data: genderData
                        }]
                    });

                    // 更新预警提示
                    const totalSentiment = data.sentimentData.正面 + data.sentimentData.负面 + data.sentimentData.中性;
                    const negativePercentage = (data.sentimentData.负面 / totalSentiment) * 100;
                    updateWarningBox(negativePercentage);
                })
                .catch(error => {
                    console.error('获取图表数据失败:', error);
                    // 这里可以添加用户友好的错误提示
                });
        }
        function updateRealtimeMonitoring() {
    fetch('/page/api/realtime-monitoring')
        .then(response => {
            if (!response.ok) {
                throw new Error('网络响应不正常');
            }
            return response.json();
        })
        .then(dataList => {
            const realtimeList = document.getElementById('realtime-list');

            dataList.forEach((data, index) => {
                const li = document.createElement('li');
                li.innerHTML = `
                    <span class="author"> <a href="${data.authorLink}" target="_blank">${data.author}</a></span>
                    <span class="content">${data.content}</span>
                `;
                li.style.opacity = '0';
                li.style.transform = 'translateY(-20px)';

                // 将新数据插入到列表的顶部
                realtimeList.insertBefore(li, realtimeList.firstChild);

                // 添加渐入动画
                setTimeout(() => {
                    li.style.opacity = '1';
                    li.style.transform = 'translateY(0)';
                }, index * 100);
            });

            // 保持列表在一个合理的长度，例如最多显示50条
            const maxItems = 50;
            while (realtimeList.children.length > maxItems) {
                const itemToRemove = realtimeList.lastChild;
                itemToRemove.style.opacity = '0';
                itemToRemove.style.transform = 'translateY(20px)';
                setTimeout(() => {
                    realtimeList.removeChild(itemToRemove);
                }, 500);
            }

            // 平滑滚动到顶部
            realtimeList.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        })
        .catch(error => {
            console.error('获取实时监测数据失败:', error);
        });
}

        function updateWarningBox(negativePercentage) {
            const warningBox = document.getElementById('warning-box');
            let message, className;

            if (negativePercentage <= 30) {
                message = '无异常';
                className = 'normal';
            } else if (negativePercentage <= 50) {
                message = '需要注意';
                className = 'warning';
            } else {
                message = '舆情危机提醒';
                className = 'danger';
            }

            warningBox.textContent = message;
            warningBox.className = 'warning-box ' + className;
        }

        function updateHotTopics() {
    fetch('/page/api/hot-topics')
        .then(response => {
            if (!response.ok) {
                throw new Error('网络响应不正常');
            }
            return response.json();
        })
        .then(data => {
            const hotTopicsGrid = document.getElementById('hot-topics-grid');
            hotTopicsGrid.innerHTML = ''; // 清空现有内容

            data.forEach((item, index) => {
                for (const [title, url] of Object.entries(item)) {
                    const topicItem = document.createElement('div');
                    topicItem.className = 'hot-topic-item';
                    const a = document.createElement('a');
                    a.href = url;
                    a.textContent = title;
                    a.target = '_blank'; // 在新标签页中打开链接
                    topicItem.appendChild(a);
                    hotTopicsGrid.appendChild(topicItem);

                    // 添加渐入动画
                    topicItem.style.opacity = '0';
                    topicItem.style.transform = 'translateY(20px)';
                    setTimeout(() => {
                        topicItem.style.opacity = '1';
                        topicItem.style.transform = 'translateY(0)';
                    }, index * 50);
                }
            });
        })
        .catch(error => {
            console.error('获取热点话题失败:', error);
            // 这里可以添加用户友好的错误提示
        });
}
        function updateClock() {
    const clock = document.getElementById('real-time-clock');
    const now = new Date();
    clock.textContent = now.toLocaleString();
}

// 在 DOMContentLoaded 事件监听器中添加：
setInterval(updateClock, 1000);

        // 添加移动端触摸事件支持
        function addTouchSupport() {
            const chartElements = [chinaHeatmap, sentimentPie, genderPie];
            
            chartElements.forEach(chart => {
                if (chart) {
                    const mc = new Hammer(chart.getDom());
                    
                    // 支持双指缩放
                    mc.get('pinch').set({ enable: true });
                    
                    // 支持拖动
                    mc.get('pan').set({ direction: Hammer.DIRECTION_ALL });
                    
                    // 处理缩放
                    mc.on('pinchstart', function() {
                        const option = chart.getOption();
                        if (option.series[0].type === 'map') {
                            chart._lastScale = option.series[0].zoom || 1;
                        }
                    });
                    
                    mc.on('pinch', function(e) {
                        const option = chart.getOption();
                        if (option.series[0].type === 'map') {
                            option.series[0].zoom = chart._lastScale * e.scale;
                            chart.setOption(option);
                        }
                    });
                    
                    // 处理拖动
                    mc.on('panmove', function(e) {
                        const option = chart.getOption();
                        if (option.series[0].type === 'map') {
                            chart.setOption({
                                series: [{
                                    center: [
                                        e.center.x,
                                        e.center.y
                                    ]
                                }]
                            });
                        }
                    });
                }
            });
        }

        document.addEventListener('DOMContentLoaded', function() {
    initAllCharts();
    updateHotTopics(); // 立即执行一次
    updateRealtimeMonitoring(); // 立即执行一次

    // 添加移动端触摸支持
    if ('ontouchstart' in window) {
        addTouchSupport();
    }
    
    // 定期更新数据
    setInterval(updateCharts, 5000);
    setInterval(updateHotTopics, 1800000); // 每1分钟更新一次热点话题
    setInterval(updateRealtimeMonitoring, 30000); // 每30秒更新一次
    setInterval(updateClock, 1000); // 每秒更新时钟

    // 监听屏幕旋转事件
    window.addEventListener('orientationchange', function() {
        setTimeout(function() {
            chinaHeatmap && chinaHeatmap.resize();
            sentimentPie && sentimentPie.resize();
            genderPie && genderPie.resize();
        }, 300);
    });
});
