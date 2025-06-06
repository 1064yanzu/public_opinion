// 滚动动画
    document.addEventListener('DOMContentLoaded', () => {
        const cards = document.querySelectorAll('.feature-card');
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }
            });
        }, {
            threshold: 0.1
        });

        cards.forEach(card => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            card.style.transition = 'all 0.6s ease';
            observer.observe(card);
        });
    });

    // 添加视频加载和错误处理脚本
    document.addEventListener('DOMContentLoaded', () => {
        const video = document.querySelector('.video-player');
        
        // 视频加载误处理
        video.addEventListener('error', (e) => {
            console.error('视频加载失败:', e);
            video.closest('.video-wrapper').innerHTML = `
                <div style="
                    padding: 40px; 
                    text-align: center; 
                    color: #666;
                    background: #f8f9fa;
                    border-radius: 20px;
                ">
                    <svg viewBox="0 0 24 24" style="width: 48px; height: 48px; margin-bottom: 20px;">
                        <path fill="#666" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
                    </svg>
                    <p>视频加载失败，请检查文件路径或刷新页面重试</p>
                </div>
            `;
        });
        
        // 视频加载进度提示
        video.addEventListener('loadstart', () => {
            video.setAttribute('poster', 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1"%3E%3C/svg%3E');
        });
        
        // 视频加载完成后移除占位图
        video.addEventListener('loadeddata', () => {
            video.removeAttribute('poster');
        });
    });

    // 添加滚动事件处理
    document.addEventListener('DOMContentLoaded', () => {
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function(e) {
                e.preventDefault();
                const targetId = this.getAttribute('href').substring(1);
                const targetElement = document.getElementById(targetId);
                
                if (targetElement) {
                    targetElement.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
    });

    // 团队成员数据
    const teamMembers = [
        {
            name: '文梓婧',
            role: '项目成员',
            desc: '我是文梓婧，05年生，苏州人，铁打的巨蟹座INFJ，一边躺平一边卷的45%拧巴法棍，港台文学重度依赖型人格，一枚浓浓的淡人，梦想是只做想做的事情。',
            avatar: '/static/assets/images/文梓婧.jpg'
        },
        {
            name: '彭静怡',
            role: '项目成员',
            desc: '我是彭静怡，04年生，是温柔细心的巨蟹座ISFP，上升双子思维跳跃、行动力强，全世界最伟大的饭搭子，在王者峡谷当过几年嫦娥，私下里是唱歌跳舞都来。',
            avatar: '/static/assets/images/彭静怡.jpg'
        },
        {
            name: '罗相吉',
            role: '项目成员',
            desc: '我是罗相吉，04年生，社牛症患者，六边形战士，先天自来熟，不靠谱点子王，是为人热情随和的ISFJ。喜欢读哲理诗，偶尔喜欢写写随笔，懒癌重度患者。',
            avatar: '/static/assets/images/罗相吉.jpg'
        },
        {
            name: '赵雯祺',
            role: '项目成员',
            desc: '我是赵雯祺，又名茄子，04年5月出生，山东泰安人，infp。喜欢春夏之交和漫无目的地闲聊。极度过敏体质但爱吃，最爱布蕾脆脆奶芙。座右铭是不管多急吃完这顿饭再急。',
            avatar: '/static/assets/images/赵雯祺.jpg'
        },
        {
            name: '陈旭豪',
            role: '项目主理人',
            desc: '我是陈旭豪，团队主理人、技术负责人。精通Python、java、html、css、javascript、Vue3等单词的拼写。数码发烧友，喜欢折腾各类数码产品。技术乐观主义者，AI降临派',
            avatar: '/static/assets/images/陈旭豪.jpg'
        },
        {
            name: '陈俊松',
            role: '项目成员',
            desc: '我是陈俊松，热爱生活，喜欢在运动场上挥洒汗水，也喜欢喜欢用心品尝佳肴之味美；喜欢用相机抓取美好瞬间，也喜欢在书海中学习历史大势。千里之行，始于足下，愿我们能够共同进步！',
            avatar: '/static/assets/images/陈俊松.jpg'
        }
    ];

// 初始化卡片
document.addEventListener('DOMContentLoaded', () => {
    const cards = document.querySelectorAll('.member-card');
    const usedMembers = new Set();

    // 初始化所有卡片
    cards.forEach(card => {
        card.addEventListener('click', function() {
            if (!this.dataset.initialized) {
                initializeCard(this, usedMembers);
                this.dataset.initialized = 'true';
            }
            
            if (!this.classList.contains('flipped')) {
                // 第一次点击：翻转卡片
                this.classList.add('flipped');
            } else {
                // 第二次点击：显示模态框
                showMemberModal(this);
            }
        });
    });
});

function initializeCard(card, usedMembers) {
    // 随机选择未使用的成员
    let availableMembers = teamMembers.filter(
        (_, index) => !usedMembers.has(index)
    );
    
    if (availableMembers.length === 0) {
        usedMembers.clear();
        availableMembers = teamMembers;
    }
    
    const randomIndex = Math.floor(Math.random() * availableMembers.length);
    const memberIndex = teamMembers.indexOf(availableMembers[randomIndex]);
    const member = teamMembers[memberIndex];
    
    usedMembers.add(memberIndex);
    
    // 更新卡片内容
    const backSide = card.querySelector('.card-back');
    backSide.querySelector('.member-avatar img').src = member.avatar;
    backSide.querySelector('.member-avatar img').dataset.memberId = memberIndex;
    backSide.querySelector('.member-name').textContent = member.name;
    backSide.querySelector('.member-role').textContent = member.role;
    backSide.querySelector('.member-desc').textContent = member.desc;
}

    // 模态框功能
    function showMemberModal(card) {
        const modal = document.querySelector('.member-modal');
        const modalBody = modal.querySelector('.modal-body');
        const memberId = card.querySelector('.member-avatar img').dataset.memberId;
        const member = teamMembers[memberId];
        
        const tags = extractTags(member);
        
        modalBody.innerHTML = `
            <div class="modal-bg"></div>
            <div class="modal-left-decor"></div>
            <div class="modal-right-decor"></div>
            
            <div class="modal-avatar">
                <img src="${member.avatar}" alt="${member.name}">
            </div>
            
            <h2 class="modal-name">${member.name}</h2>
            
            <div class="modal-tags">
                ${tags.map(tag => `<span class="modal-tag">${tag}</span>`).join('')}
            </div>
            
            <p class="modal-desc">${member.desc}</p>
        `;
        
        modal.classList.add('active');

        // 重新绑定关闭按钮事件
        const closeBtn = modal.querySelector('.close-modal');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                modal.classList.remove('active');
            });
        }
    }

    // 提取标签的辅助函数
    function extractTags(member) {
        const tags = [];
        
        // 从描述中提取关键信息作为标签
        if (member.name === '文梓婧') {
            tags.push('巨蟹座', 'INFJ', '苏州人', '05年生');
        } else if (member.name === '彭静怡') {
            tags.push('巨蟹座', 'ISFP', '04年生', '唱歌跳舞');
        } else if (member.name === '罗相吉') {
            tags.push('ISFJ', '04年生', '诗歌爱好者');
        } else if (member.name === '赵雯祺') {
            tags.push('INFP', '04年生', '山东人', '美食爱好者');
        } else if (member.name === '陈旭豪') {
            tags.push('AI降临派', '04年生', '数码发烧友', '技术乐观主义');
        } else if (member.name === '陈俊松') {
            tags.push('山东人', '摄影', '热爱生活', '志愿活动');
        }
        
        return tags;
    }

    // 关闭模态框
    document.querySelector('.close-modal').addEventListener('click', () => {
        document.querySelector('.member-modal').classList.remove('active');
    });

    // 点击模态框外部关闭
    document.querySelector('.member-modal').addEventListener('click', (e) => {
        if (e.target.classList.contains('member-modal')) {
            e.target.classList.remove('active');
        }
    });

    // 添加页面加载动画
    document.addEventListener('DOMContentLoaded', () => {
        const loading = document.createElement('div');
        loading.className = 'loading';
        document.body.appendChild(loading);

        window.addEventListener('load', () => {
            loading.style.opacity = '0';
            setTimeout(() => loading.remove(), 300);
        });
    });

    // 添加移动端菜单切换功能
    document.addEventListener('DOMContentLoaded', () => {
        const menuToggle = document.createElement('div');
        menuToggle.className = 'menu-toggle';
        menuToggle.innerHTML = `
            <span></span>
            <span></span>
            <span></span>
        `;
        
        const navContainer = document.querySelector('.nav-container');
        const navMenu = document.querySelector('.nav-menu');
        
        navContainer.insertBefore(menuToggle, navMenu);
        
        menuToggle.addEventListener('click', () => {
            navMenu.classList.toggle('active');
            menuToggle.classList.toggle('active');
        });

        // 点击菜单项后关闭菜单
        navMenu.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                navMenu.classList.remove('active');
                menuToggle.classList.remove('active');
            });
        });

        // 点击页面其他地方关闭菜单
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.nav-menu') && !e.target.closest('.menu-toggle')) {
                navMenu.classList.remove('active');
                menuToggle.classList.remove('active');
            }
        });
    });

    // 优化滚动性能
    let ticking = false;
    window.addEventListener('scroll', () => {
        if (!ticking) {
            window.requestAnimationFrame(() => {
                // 处理滚动相关的视觉效果
                const scrolled = window.scrollY;
                const navbar = document.querySelector('.navbar');
                
                if (scrolled > 50) {
                    navbar.style.background = 'rgba(255, 255, 255, 0.95)';
                    navbar.style.boxShadow = '0 10px 30px rgba(0, 0, 0, 0.1)';
                } else {
                    navbar.style.background = 'rgba(255, 255, 255, 0.85)';
                    navbar.style.boxShadow = 'none';
                }
                
                ticking = false;
            });
            ticking = true;
        }
    });
