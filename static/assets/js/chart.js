document.addEventListener('DOMContentLoaded', function () {
    var pieChartContainer = document.getElementById('pie-chart');

    // 确保 pie_data 被正确替换
    var pieData = { pie_data|tojson };
    console.log("Received data:", pieData); // 查看控制台输出，确认数据传递正确

    // 初始化 ECharts 实例
    var pieChart = echarts.init(pieChartContainer);
    if (!pieChart) {
        console.error("Failed to initialize ECharts instance.");
        return;
    }

    // 饼图配置项
    var option = {
        tooltip: {
            trigger: 'item'
        },
        series: [
            {
                type: 'pie',
                radius: '75%',
                data: Object.entries(pieData).map(([name, value]) => ({ name, value })),
                emphasis: {
                    itemStyle: {
                        shadowBlur: 10,
                        shadowOffsetX: 0,
                        shadowColor: 'rgba(0, 0, 0, 0.5)'
                    }
                }
            }
        ]
    };

    try {
            // 使用配置项和数据显示图表
            pieChart.setOption(option);
        } catch (error) {
            console.error("Error setting the chart option:", error);
        }
    });