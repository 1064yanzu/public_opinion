$(document).ready(function() {
    // 延迟加载非关键组件
    const loadDeferredStyles = () => {
        const additionalStyles = document.createElement('link');
        additionalStyles.rel = 'stylesheet';
        additionalStyles.href = 'https://lf3-cdn-tos.bytecdntp.com/cdn/expire-1-M/animate.css/4.1.1/animate.min.css';
        document.head.appendChild(additionalStyles);
    };
    window.addEventListener('load', loadDeferredStyles);

    // 日期选择器配置
    $('.input-daterange').datepicker({
        format: 'yyyy-mm-dd',
        language: 'zh-CN',
        autoclose: true,
        todayHighlight: true,
        clearBtn: true,
        orientation: "bottom auto"
    });

    // Select2配置
    $('.select2-multiple').select2({
        language: 'zh-CN',
        placeholder: '请选择要爬取的平台...',
        allowClear: true,
        closeOnSelect: false,
        templateResult: formatPlatform,
        templateSelection: formatPlatformSelection,
        dropdownParent: $('body')
    });

    // 平台选项格式化
    function formatPlatform(platform) {
        if (!platform.id) return platform.text;
        const platformData = {
            weibo: {
                icon: 'iconfont icon-weibo',
                name: '新浪微博',
                desc: '中国最大的社交媒体平台',
                color: '#E6162D'
            },
            douyin: {
                icon: 'iconfont icon-douyin',
                name: '抖音短视频',
                desc: '领先的短视频平台',
                color: '#000000'
            }
        };
        
        const data = platformData[platform.id];
        if (!data) return platform.text;

        return $(`
            <div class="d-flex align-items-center p-2 platform-option">
                <div class="platform-icon mr-3" style="color: ${data.color}">
                    <i class="${data.icon}"></i>
                </div>
                <div>
                    <div class="platform-name">${data.name}</div>
                    <small class="text-muted">${data.desc}</small>
                </div>
            </div>
        `);
    }

    // 选中项格式化
    function formatPlatformSelection(platform) {
        if (!platform.id) return platform.text;
        const icons = {
            weibo: 'iconfont icon-weibo',
            douyin: 'iconfont icon-douyin'
        };
        return $(`
            <span class="selected-platform">
                <i class="${icons[platform.id] || 'iconfont icon-platform'} mr-1"></i>
                ${platform.text}
            </span>
        `);
    }

    // 表单提交处理
    $('#crawl-form').on('submit', function(event) {
        event.preventDefault();
        
        var selectedPlatforms = $('.select2-multiple').val();
        if (!selectedPlatforms || selectedPlatforms.length === 0) {
            Swal.fire({
                title: '提示',
                text: '请选择至少一个平台',
                icon: 'warning',
                confirmButtonText: '确定'
            });
            return;
        }

        // 添加提交按钮加载动画
        const $submitBtn = $(this).find('button[type="submit"]');
        $submitBtn.prop('disabled', true)
            .html('<i class="fas fa-spinner fa-spin mr-2"></i>处理中...');

        // 显示加载遮罩
        showLoadingOverlay('正在初始化爬虫系统...', '请稍候，系统正在准备数据采集');

        // 使用AJAX提交表单
        $.ajax({
            url: $(this).attr('action'),
            method: 'POST',
            data: new FormData(this),
            processData: false,
            contentType: false,
            success: function(response) {
                if (response.status === 'success') {
                    // 更新数据展示
                    updateDataDisplay(response.data);
                    // 更新表格数据
                    updateDataTable(response.data.infos2);
                    hideLoadingOverlay();
                    updateStatus('数据采集完成', 'success');
                } else {
                    hideLoadingOverlay();
                    Swal.fire({
                        title: '错误',
                        text: response.message || '爬取失败，请重试',
                        icon: 'error',
                        confirmButtonText: '确定'
                    });
                }
                
                // 恢复提交按钮状态
                $submitBtn.prop('disabled', false)
                    .html('<i class="fas fa-spider mr-2"></i>开始爬取');
            },
            error: function(xhr, status, error) {
                hideLoadingOverlay();
                Swal.fire({
                    title: '错误',
                    text: '请求失败: ' + error,
                    icon: 'error',
                    confirmButtonText: '确定'
                });
                $submitBtn.prop('disabled', false)
                    .html('<i class="fas fa-spider mr-2"></i>开始爬取');
            }
        });
    });

    // 显示加载遮罩
    function showLoadingOverlay(title, subtitle) {
        const $overlay = $('#loadingOverlay');
        const $content = $overlay.find('.overlay-content');
        
        // 更新遮罩内容
        $content.html(`
            <div class="loading-pulse">
                <div></div>
                <div></div>
            </div>
            <h4 class="overlay-text">${title}</h4>
            <p class="overlay-subtext">${subtitle}</p>
            <div class="progress">
                <div class="progress-bar progress-bar-striped progress-bar-animated" role="progressbar" style="width: 100%"></div>
            </div>
        `);
        
        $overlay.css('display', 'flex').hide().fadeIn(300);
    }

    // 更新加载状态
    function updateLoadingStatus(title, subtitle) {
        const $content = $('#loadingOverlay .overlay-content');
        $content.find('.overlay-text').text(title);
        $content.find('.overlay-subtext').text(subtitle);
    }

    // 隐藏加载遮罩
    function hideLoadingOverlay() {
        $('#loadingOverlay').fadeOut('fast', function() {
            // 显示提示信息
            Swal.fire({
                title: '爬取完成',
                text: '请点击确定刷新页面查看最新数据',
                icon: 'success',
                confirmButtonText: '确定'
            }).then((result) => {
                if (result.isConfirmed) {
                    location.reload(); // 刷新页面
                }
            });
        });
    }

    // 更新数据显示
    function updateDataDisplay(data) {
        // 更新统计数据
        updateStatCard('share-count', data.share_num, '总转发数');
        updateStatCard('comment-count', data.comment_num, '总评论数');
        updateStatCard('like-count', data.like_num, '总点赞数');
        
        // 更新情感分析数据
        updateSentimentData(data.positive_count, data.negative_count, data.neutral_count);
        
        // 更新数据表格
        updateDataTable(data.infos2);
    }

    // 更新统计卡片
    function updateStatCard(elementId, value, label) {
        const $card = $(`#${elementId}`);
        if ($card.length) {
            $card.find('.data-value').text(value.toLocaleString());
            $card.find('.data-label').text(label);
        }
    }

    // 更新情感分析数据
    function updateSentimentData(positive, negative, neutral) {
        // 更新饼图数据
        if (window.sentimentChart) {
            window.sentimentChart.data.datasets[0].data = [positive, negative, neutral];
            window.sentimentChart.update();
        }
    }

    // 更新数据表格
    function updateDataTable(data) {
        const $table = $('#dataTable');
        if (!$table.length) return;

        // 过滤无效数据
        const filteredData = (data || []).filter(item => {
            return item.用户名 !== "未知作者" && 
                   item.内容 !== "无内容" &&
                   item.用户名 && item.内容;  // 确保不为空
        });
        
        // 销毁已存在的DataTable实例
        if ($.fn.DataTable.isDataTable('#dataTable')) {
            $table.DataTable().destroy();
            $table.empty();
        }

        // 初始化DataTable
        $table.DataTable({
            data: filteredData,
            columns: [
                { data: '用户名' },
                { data: '内容' },
                { 
                    data: 'sentiment_result',
                    render: function(data) {
                        let badgeClass = 'badge-warning';
                        if (data === '正面') badgeClass = 'badge-success';
                        if (data === '负面') badgeClass = 'badge-danger';
                        return `<span class="badge ${badgeClass}">${data}</span>`;
                    }
                },
                { data: '发布时间' },
                { data: '分享数' },
                { data: '评论数' },
                { data: '点赞数' }
            ],
            language: {
                "sProcessing": "处理中...",
                "sLengthMenu": "显示 _MENU_ 条结果",
                "sZeroRecords": "没有匹配结果",
                "sInfo": "显示第 _START_ 至 _END_ 项结果，共 _TOTAL_ 项",
                "sInfoEmpty": "显示第 0 至 0 项结果，共 0 项",
                "sInfoFiltered": "(由 _MAX_ 项结果过滤)",
                "sInfoPostFix": "",
                "sSearch": "搜索:",
                "sUrl": "",
                "sEmptyTable": "暂无数据",
                "sLoadingRecords": "载入中...",
                "sInfoThousands": ",",
                "oPaginate": {
                    "sFirst": "首页",
                    "sPrevious": "上页",
                    "sNext": "下页",
                    "sLast": "末页"
                },
                "oAria": {
                    "sSortAscending": ": 以升序排列此列",
                    "sSortDescending": ": 以降序排列此列"
                }
            },
            pageLength: 10,
            order: [[3, 'desc']], // 按发布时间降序排序
            responsive: true,
            dom: '<"d-flex justify-content-between align-items-center mb-3"lf>rt<"d-flex justify-content-between align-items-center mt-3"ip>',
            initComplete: function() {
                $('#dataTable').closest('.card').addClass('animate__animated animate__fadeIn');
            }
        });
    }

    // 获取最新数据并更新表格
    function fetchAndUpdateData() {
        $.ajax({
            url: '/page/api/get_latest_data',  // 新增一个API端点来获取最新数据
            method: 'GET',
            success: function(response) {
                if (response.status === 'success') {
                    updateDataTable(response.data);
                }
            },
            error: function(xhr, status, error) {
                console.error('获取数据失败:', error);
            }
        });
    }

    // 定时检查任务状态
    function checkTaskStatus() {
        $.get('/page/api/status', function(response) {
            if (response.status === 'working') {
                updateStatus(response.message, 'working');
            } else if (response.status === 'idle') {
                updateStatus(response.message, 'idle');
            } else if (response.status === 'error') {
                updateStatus(response.message, 'error');
            }
        });
    }

    // 每5秒检查一次任务状态
    setInterval(checkTaskStatus, 5000);

    // 停止爬虫按钮事件
    $('#stop-spider').on('click', function() {
        $.post('/page/stop_spider_task', function(response) {
            if (response.status === 'success') {
                updateStatus('爬虫任务已停止', 'idle');
            } else {
                updateStatus('停止任务失败: ' + response.message, 'error');
            }
        });
    });

    // 添加卡片入场动画
    $('.card').each(function(index) {
        $(this).css({
            'animation-delay': (index * 0.1) + 's',
            'animation-name': 'slideInUp'
        });
    });

    // 返回按钮事件处理
    $('.back-button').on('click', function() {
        window.location.href = '/page/home';
    }).on('mouseenter', function() {
        $(this).find('i').addClass('animate__animated animate__fadeInLeft');
    }).on('mouseleave', function() {
        $(this).find('i').removeClass('animate__animated animate__fadeInLeft');
    });

    // Select2选择事件动画
    $('.select2-multiple').on('select2:select', function(e) {
        const $choice = $(this).next().find('.select2-selection__choice:last');
        $choice.hide().slideDown(200).css({
            transform: 'scale(0.5)',
            opacity: 0
        }).animate({
            transform: 'scale(1)',
            opacity: 1
        }, 200);
    });

    // 移动端侧边栏处理
    const $sidebar = $('#sidebar');
    const $main = $('#main');
    const $overlay = $('<div class="sidebar-overlay"></div>').appendTo('body');
    
    // 侧边栏切换
    $('#sidebarToggle').on('click', function() {
        $sidebar.toggleClass('collapsed');
        $overlay.toggleClass('active');
        if (window.innerWidth <= 768) {
            $('body').toggleClass('sidebar-open');
        }
    });

    // 点击遮罩层关闭侧边栏
    $overlay.on('click', function() {
        $sidebar.removeClass('collapsed');
        $overlay.removeClass('active');
        $('body').removeClass('sidebar-open');
    });

    // 移动端手势支持
    let touchStartX = 0;
    let touchEndX = 0;
    
    document.addEventListener('touchstart', function(e) {
        touchStartX = e.changedTouches[0].screenX;
    }, false);
    
    document.addEventListener('touchend', function(e) {
        touchEndX = e.changedTouches[0].screenX;
        handleSwipe();
    }, false);
    
    function handleSwipe() {
        const swipeThreshold = 50;
        const diff = touchEndX - touchStartX;
        
        if (Math.abs(diff) < swipeThreshold) return;
        
        if (diff > 0) { // 右滑
            if (window.innerWidth <= 768 && !$sidebar.hasClass('collapsed')) {
                $sidebar.addClass('collapsed');
                $overlay.addClass('active');
                $('body').addClass('sidebar-open');
            }
        } else { // 左滑
            if (window.innerWidth <= 768 && $sidebar.hasClass('collapsed')) {
                $sidebar.removeClass('collapsed');
                $overlay.removeClass('active');
                $('body').removeClass('sidebar-open');
            }
        }
    }

    // 移动端表格滚动优化
    $('.table-responsive').on('scroll', function() {
        if (this.scrollLeft > 0) {
            $(this).addClass('table-shadow');
        } else {
            $(this).removeClass('table-shadow');
        }
    });

    // 移动端 Select2 优化
    $('.select2-multiple').on('select2:open', function() {
        if (window.innerWidth <= 768) {
            $('.select2-dropdown').css({
                'width': '100vw',
                'left': '0',
                'position': 'fixed',
                'top': 'auto',
                'bottom': '0',
                'border-radius': '1rem 1rem 0 0',
                'border': 'none',
                'box-shadow': '0 -4px 20px rgba(0,0,0,0.1)'
            });
            
            // 添加关闭按钮
            if (!$('.select2-close-btn').length) {
                $('<button>')
                    .addClass('select2-close-btn')
                    .html('<i class="fas fa-times"></i>')
                    .prependTo('.select2-dropdown')
                    .on('click', function() {
                        $('.select2-multiple').select2('close');
                    });
            }
        }
    });

    // 窗口大小变化处理
    let resizeTimer;
    $(window).on('resize', function() {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(function() {
            if (window.innerWidth > 768) {
                $overlay.removeClass('active');
                $('body').removeClass('sidebar-open');
            }
        }, 250);
    });

    // 移动端长按处理
    let longPressTimer;
    $('.menu-item a').on('touchstart', function() {
        const $this = $(this);
        longPressTimer = setTimeout(function() {
            $this.addClass('long-press');
        }, 500);
    }).on('touchend touchcancel', function() {
        clearTimeout(longPressTimer);
        $(this).removeClass('long-press');
    });

    // 表格滚动阴影效果
    $('.table-responsive').on('scroll', function() {
        const $this = $(this);
        const scrollLeft = $this.scrollLeft();
        const maxScroll = $this[0].scrollWidth - $this[0].clientWidth;
        
        $this.toggleClass('shadow-left', scrollLeft > 0);
        $this.toggleClass('shadow-right', scrollLeft < maxScroll);
    });

    // 表格行动画
    function initTableRowAnimations() {
        $('.table tbody tr').each(function(index) {
            $(this).css({
                'animation': 'fadeInUp 0.3s ease forwards',
                'animation-delay': (index * 0.05) + 's',
                'opacity': '0'
            });
        });
    }

    // 表格初始化配置
    if ($('#dataTable').length) {
        const table = $('#dataTable').DataTable({
            language: {
                url: '//cdn.datatables.net/plug-ins/1.10.21/i18n/Chinese.json'
            },
            pageLength: 10,
            dom: '<"table-top"lf>rt<"table-bottom"ip>',
            ordering: true,
            responsive: true,
            autoWidth: false,
            drawCallback: function() {
                initTableRowAnimations();
            },
            initComplete: function() {
                // 自定义搜索框
                $('.dataTables_filter input').attr('placeholder', '搜索...');
                
                // 添加表格工具栏
                const $toolbar = $('<div class="table-toolbar"></div>').insertBefore(this);
                
                // 添加刷新按钮
                $('<button>')
                    .addClass('action-btn refresh-btn')
                    .html('<i class="fas fa-sync-alt"></i>')
                    .appendTo($toolbar)
                    .on('click', function() {
                        const $btn = $(this);
                        $btn.addClass('rotating');
                        table.ajax.reload(null, false);
                        setTimeout(() => $btn.removeClass('rotating'), 1000);
                    });
                
                // 添加列显示切换
                $('<button>')
                    .addClass('action-btn columns-btn')
                    .html('<i class="fas fa-columns"></i>')
                    .appendTo($toolbar)
                    .on('click', function() {
                        const $btn = $(this);
                        const $columnsDropdown = $('.columns-dropdown');
                        
                        if (!$columnsDropdown.length) {
                            const $dropdown = $('<div class="columns-dropdown"></div>');
                            table.columns().every(function() {
                                const column = this;
                                const $checkbox = $(`
                                    <label class="column-toggle">
                                        <input type="checkbox" ${column.visible() ? 'checked' : ''}>
                                        <span>${$(column.header()).text()}</span>
                                    </label>
                                `);
                                
                                $checkbox.find('input').on('change', function() {
                                    column.visible(this.checked);
                                });
                                
                                $dropdown.append($checkbox);
                            });
                            
                            $btn.after($dropdown);
                        } else {
                            $columnsDropdown.toggle();
                        }
                    });
            }
        });

        // 表格行选中效果
        $('#dataTable tbody').on('click', 'tr', function() {
            $(this).toggleClass('selected');
        });

        // 表格状态标签初始化
        function initStatusBadges() {
            $('.table .status').each(function() {
                const status = $(this).data('status');
                const icon = {
                    'success': 'fas fa-check',
                    'warning': 'fas fa-exclamation',
                    'error': 'fas fa-times'
                }[status];
                
                $(this).addClass(`status-badge ${status}`).prepend(`<i class="${icon}"></i>`);
            });
        }

        // 初始化状态标签
        initStatusBadges();
    }

    // 定期检查状态
    function checkStatus() {
        $.ajax({
            url: '/page/api/status',
            method: 'GET',
            success: function(response) {
                const $statusIcon = $('#status-icon');
                const $statusMessage = $('#status-message');
                
                $statusIcon.removeClass('idle working error success scheduled')
                    .addClass(response.status);
                $statusMessage.text(response.message);

                // 如果状态是scheduled，添加高亮动画
                if (response.status === 'scheduled') {
                    $statusMessage.addClass('highlight-animation');
                    setTimeout(() => $statusMessage.removeClass('highlight-animation'), 1000);
                }

                // 如果定时任务执行完成，获取并更新数据
                if (response.status === 'success' && response.task_completed) {
                    fetchAndUpdateData();
                }
            },
            error: function(xhr, status, error) {
                console.error('状态检查失败:', error);
            }
        });
    }

    // 页面加载完成后初始化
    $(document).ready(function() {
        // 获取初始数据
        fetchAndUpdateData();

        // 开始定期检查状态（每5秒）
        setInterval(checkStatus, 5000);

        // 立即执行一次状态检查
        checkStatus();
    });
});

// 优化状态更新动画
function updateStatus(message, status = 'idle') {
    const $message = $('#status-message');
    const $icon = $('#status-icon');
    
    $message.fadeOut(200, function() {
        $(this).text(message)
            .addClass('animate__animated animate__fadeIn')
            .fadeIn(200);
    });
    
    $icon.fadeOut(200, function() {
        $(this).removeClass('idle working error')
            .addClass(status)
            .addClass('animate__animated animate__bounceIn')
            .fadeIn(200);
    });

    // 添加状态栏动效
    $('.status-bar').addClass('highlight-animation');
    setTimeout(() => $('.status-bar').removeClass('highlight-animation'), 1000);
}