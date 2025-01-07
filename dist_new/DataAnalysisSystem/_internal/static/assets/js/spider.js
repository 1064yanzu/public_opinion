$(document).ready(function() {
    $('.select2-multiple').select2({
        placeholder: "选择一个或多个平台",
        allowClear: true
    });

    $('.input-daterange').datepicker({
        format: 'yyyy-mm-dd',
        autoclose: true
    });

    $('#crawl-form').on('submit', function(event) {
        var selectedPlatforms = $('.select2-multiple').val();
        if (!selectedPlatforms || selectedPlatforms.length === 0) {
            Swal.fire({
                title: '请选择平台',
                text: '至少需要选择一个爬取平台',
                icon: 'warning',
                confirmButtonText: '确定'
            });
            event.preventDefault();
            return false;
        }
        
        // 检查其他必填字段
        var keyword = $('input[name="keyword"]').val();
        if (!keyword) {
            Swal.fire({
                title: '请输入关键词',
                text: '爬取关键词不能为空',
                icon: 'warning',
                confirmButtonText: '确定'
            });
            event.preventDefault();
            return false;
        }
        
        showOverlay('开始数据爬取', '正在初始化爬虫系统...');
        updateStatus('正在爬取数据...', 'working');
    });

    // 检查DataTable是否已经初始化
    if ($.fn.DataTable.isDataTable('#example')) {
        // 如果已经初始化,先销毁它
        $('#example').DataTable().destroy();
    }

    // 重新初始化DataTable
    $('#example').DataTable({
        "pageLength": 10,
        "language": {
            "url": "//cdn.datatables.net/plug-ins/1.10.21/i18n/Chinese.json"
        }
    });
});

function updateStatus(message, status = 'idle') {
    $('#status-message').text(message);
    $('#status-icon').removeClass('idle working error').addClass(status);
}

function fetchStatus() {
    $.ajax({
        url: '/page/api/status',
        method: 'GET',
        success: function(response) {
            updateStatus(response.message, response.status);
            if (response.status === 'error') {
                hideOverlay();
                Swal.fire({
                    title: '错误',
                    text: '数据爬取过程中出现错误',
                    icon: 'error'
                });
            }
        },
        error: function() {
            hideOverlay();
            Swal.fire({
                title: '连接错误',
                text: '无法获取爬虫状态',
                icon: 'error'
            });
        }
    });
}

// 每5秒更新一次状态
setInterval(fetchStatus, 5000);

// 监听页面刷新事件
window.addEventListener('beforeunload', function() {
    hideOverlay();
});

// 改进的遮罩控制函数
function showOverlay(message = '开始数据爬取', subMessage = '正在初始化爬虫...') {
    $('.overlay-text').text(message);
    $('.overlay-subtext').text(subMessage);
    $('#loadingOverlay').css('display', 'flex').fadeIn(400);
    
    // 动态消息更新
    let messages = [
        '正在连接数据源...',
        '正在分析数据结构...',
        '正在提取关键信息...',
        '正在处理数据...',
        '即将完成...'
    ];
    let currentMessage = 0;
    
    window.messageInterval = setInterval(() => {
        $('.overlay-subtext').fadeOut(200, function() {
            $(this).text(messages[currentMessage]).fadeIn(200);
        });
        currentMessage = (currentMessage + 1) % messages.length;
    }, 2500);
}

function hideOverlay() {
    $('#loadingOverlay').fadeOut(400);
    clearInterval(window.messageInterval);
}

// 修改停止按钮处理
$('#stop-spider').click(function() {
    showOverlay();
    $.ajax({
        url: '/page/stop_spider_task',
        type: 'POST',
        success: function(response) {
            $('#status-message').text(response.message);
            if (response.status === 'success') {
                $('#status-icon').removeClass().addClass('status-icon success');
            } else {
                $('#status-icon').removeClass().addClass('status-icon error');
            }
            hideOverlay();
        },
        error: function() {
            $('#status-message').text('停止监测请求失败');
            $('#status-icon').removeClass().addClass('status-icon error');
            hideOverlay();
        }
    });
});

window.addEventListener('load', function() {
    $('#loading-message').hide();
    updateStatus('页面加载完成');
});