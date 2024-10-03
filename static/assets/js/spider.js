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
        $('#loading-message').show();
        
        // 检查是否选择了至少一个平台
        var selectedPlatforms = $('.select2-multiple').val();
        if (!selectedPlatforms || selectedPlatforms.length === 0) {
            alert('请选择至少一个平台！');
            event.preventDefault(); // 阻止表单提交
        } else {
            updateStatus('正在爬取数据...', 'working');
        }
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
        url: '/page/api/status',  // 假设这是获取状态的API端点
        method: 'GET',
        success: function(response) {
            updateStatus(response.message, response.status);
        },
        error: function() {
            updateStatus('无法获取状态', 'error');
        }
    });
}

// 每5秒更新一次状态
setInterval(fetchStatus, 5000);

$('#stop-spider').click(function() {
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
        },
        error: function() {
            $('#status-message').text('停止监测请求失败');
            $('#status-icon').removeClass().addClass('status-icon error');
        }
    });
});

window.addEventListener('load', function() {
    $('#loading-message').hide();
    updateStatus('页面加载完成');
});