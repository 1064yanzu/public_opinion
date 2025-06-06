// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 导航栏滚动效果
    const header = document.querySelector('header');
    let lastScrollY = window.scrollY;

    window.addEventListener('scroll', function() {
        if (window.scrollY > 100) {
            header.classList.add('scrolled');
        } else {
            header.classList.remove('scrolled');
        }

        lastScrollY = window.scrollY;
    });

    // 添加背景动态效果
    const body = document.body;
    
    // 监听鼠标移动，让浮动形状跟随鼠标轻微移动
    document.addEventListener('mousemove', function(e) {
        const mouseX = e.clientX / window.innerWidth;
        const mouseY = e.clientY / window.innerHeight;
        
        const shapes = document.querySelectorAll('.shape');
        shapes.forEach((shape, index) => {
            const offsetX = (mouseX - 0.5) * (index + 1) * 15;
            const offsetY = (mouseY - 0.5) * (index + 1) * 15;
            shape.style.transform = `translate(${offsetX}px, ${offsetY}px)`;
        });
    });
    
    // 随机添加微小的动态圆点
    function createParticles() {
        const particlesContainer = document.querySelector('.bg-floating-shapes');
        if (!particlesContainer) return;
        
        const particleCount = window.innerWidth > 768 ? 20 : 10;
        
        for (let i = 0; i < particleCount; i++) {
            const particle = document.createElement('div');
            particle.classList.add('particle');
            
            // 随机大小
            const size = Math.random() * 5 + 1;
            particle.style.width = `${size}px`;
            particle.style.height = `${size}px`;
            
            // 随机位置
            const posX = Math.random() * 100;
            const posY = Math.random() * 100;
            particle.style.left = `${posX}%`;
            particle.style.top = `${posY}%`;
            
            // 随机透明度
            const opacity = Math.random() * 0.1 + 0.05;
            particle.style.opacity = opacity;
            
            // 随机动画延迟
            const delay = Math.random() * 5;
            particle.style.animationDelay = `${delay}s`;
            
            // 添加到容器
            particlesContainer.appendChild(particle);
        }
    }
    
    createParticles();
    
    // 窗口大小变化时重新调整
    window.addEventListener('resize', function() {
        // 移除旧的粒子
        const oldParticles = document.querySelectorAll('.particle');
        oldParticles.forEach(particle => particle.remove());
        
        // 创建新的
        createParticles();
    });

    // 平滑滚动到锚点
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                window.scrollTo({
                    top: targetElement.offsetTop - 100,
                    behavior: 'smooth'
                });
            }
        });
    });

    // 预览项目交互效果
    const previewItems = document.querySelectorAll('.preview-item');
    previewItems.forEach(item => {
        item.addEventListener('mouseenter', function() {
            previewItems.forEach(i => i.classList.remove('active'));
            this.classList.add('active');
        });
    });

    // 添加页面动画
    const animateElements = document.querySelectorAll('.hero-content, .app-preview, .feature-card, .step, .pricing-card');
    
    // 使用 Intersection Observer 监听元素进入视口
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate');
                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.1
    });

    animateElements.forEach(el => {
        observer.observe(el);
    });

    // 价格卡片交互
    const pricingCards = document.querySelectorAll('.pricing-card');
    const selectionFeedback = document.querySelector('.selection-feedback');
    let selectedPlanText = document.querySelector('.selected-plan');
    
    // 初始不显示选中状态反馈
    if (selectionFeedback) {
        selectionFeedback.classList.remove('show');
    }

    // 点击选择方案
    pricingCards.forEach(card => {
        // 悬停效果
        card.addEventListener('mouseenter', function() {
            pricingCards.forEach(c => c.classList.remove('hovered'));
            this.classList.add('hovered');
        });
        
        card.addEventListener('mouseleave', function() {
            this.classList.remove('hovered');
        });
        
        // 点击选择效果
        card.addEventListener('click', function() {
            // 获取方案名称
            const planName = this.querySelector('h3').textContent;
            const planType = this.getAttribute('data-plan');
            
            // 移除其他卡片的选中状态
            pricingCards.forEach(c => c.classList.remove('selected'));
            
            // 添加当前卡片的选中状态
            this.classList.add('selected');
            
            // 创建或更新选中方案文本元素
            if (!selectedPlanText) {
                selectionFeedback.innerHTML = `您已选择<span class="selected-plan">${planName}</span>方案，限时免费使用！`;
                selectedPlanText = document.querySelector('.selected-plan');
            } else {
                selectedPlanText.textContent = planName;
            }
            
            // 显示反馈信息
            selectionFeedback.classList.remove('show');
            
            // 触发视觉反馈
            setTimeout(() => {
                selectionFeedback.classList.add('show');
            }, 10);
            
            // 如果是企业版，修改反馈信息
            if (planType === 'enterprise') {
                selectionFeedback.innerHTML = `您已选择<span class="selected-plan">${planName}</span>方案，我们的客户经理将很快与您联系！`;
            } else {
                selectionFeedback.innerHTML = `您已选择<span class="selected-plan">${planName}</span>方案，限时免费使用！`;
            }
            
            // 按钮点击效果
            this.classList.add('clicked');
            setTimeout(() => {
                this.classList.remove('clicked');
            }, 300);
        });
    });

    // 防止点击卡片上的按钮时触发卡片点击事件
    document.querySelectorAll('.pricing-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.stopPropagation();
        });
    });
    
    // ===== 新增功能 =====
    
    // 1. 视差滚动效果
    const parallaxElements = document.querySelectorAll('.hero, .features, .how-it-works, .pricing');
    
    window.addEventListener('scroll', function() {
        const scrolled = window.pageYOffset;
        
        parallaxElements.forEach(element => {
            const speed = 0.2;
            const yPos = -(scrolled * speed);
            const section = element;
            
            if (section.querySelector('.parallax-bg')) {
                section.querySelector('.parallax-bg').style.transform = `translateY(${yPos}px)`;
            }
        });
    });
    
    // 为需要视差效果的部分添加背景元素
    parallaxElements.forEach(section => {
        // 如果还没有视差背景，添加一个
        if (!section.querySelector('.parallax-bg')) {
            const parallaxBg = document.createElement('div');
            parallaxBg.classList.add('parallax-bg');
            section.prepend(parallaxBg);
        }
    });
    
    // 2. 图片加载动画
    const images = document.querySelectorAll('img');
    images.forEach(img => {
        // 添加加载动画类
        img.classList.add('img-loading');
        
        img.addEventListener('load', function() {
            this.classList.remove('img-loading');
            this.classList.add('img-loaded');
        });
    });
    
    // 3. 微交互动效 - 按钮和链接
    const interactiveElements = document.querySelectorAll('.primary-btn, .secondary-btn, .pricing-btn, .try-btn, .nav-links a');
    interactiveElements.forEach(element => {
        element.addEventListener('mouseenter', function() {
            this.classList.add('pulse-effect');
        });
        
        element.addEventListener('mouseleave', function() {
            this.classList.remove('pulse-effect');
        });
    });
    
    // 4. 打字机效果 (应用于网站一级标题)
    const heroTitle = document.querySelector('.hero h1');
    if (heroTitle) {
        const originalText = heroTitle.innerHTML;
        const textLines = originalText.split('<br>');
        
        // 保存"用"和"揭示真相"的分隔
        heroTitle.innerHTML = textLines[0] + '<br><span class="typing"></span><br>' + textLines[2];
        
        const typingElement = heroTitle.querySelector('.typing');
        const textToType = textLines[1]; // "ClarityStudio"
        let i = 0;
        
        // 启动打字效果
        function typeWriter() {
            if (i < textToType.length) {
                typingElement.innerHTML += textToType.charAt(i);
                i++;
                setTimeout(typeWriter, 100);
            } else {
                // 打字完成后添加光标闪烁效果
                typingElement.classList.add('typing-done');
            }
        }
        
        // 延迟一下再开始打字效果，让页面有时间加载
        setTimeout(typeWriter, 1000);
    }
    
    // 5. 创建回到顶部按钮
    const backToTopBtn = document.createElement('button');
    backToTopBtn.classList.add('back-to-top');
    backToTopBtn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="18 15 12 9 6 15"></polyline></svg>';
    document.body.appendChild(backToTopBtn);
    
    // 回到顶部功能
    backToTopBtn.addEventListener('click', function() {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
    
    // 显示/隐藏回到顶部按钮
    window.addEventListener('scroll', function() {
        if (window.scrollY > 300) {
            backToTopBtn.classList.add('show');
        } else {
            backToTopBtn.classList.remove('show');
        }
    });
    
    // 6. 创建暗色模式切换按钮
    const darkModeToggle = document.createElement('button');
    darkModeToggle.classList.add('dark-mode-toggle');
    darkModeToggle.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>';
    document.body.appendChild(darkModeToggle);
    
    // 检查是否已经有暗色模式偏好
    if (localStorage.getItem('darkMode') === 'enabled') {
        document.body.classList.add('dark-mode');
        darkModeToggle.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>';
    }
    
    // 点击切换暗色模式
    darkModeToggle.addEventListener('click', function() {
        if (document.body.classList.contains('dark-mode')) {
            document.body.classList.remove('dark-mode');
            localStorage.setItem('darkMode', 'disabled');
            this.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>';
        } else {
            document.body.classList.add('dark-mode');
            localStorage.setItem('darkMode', 'enabled');
            this.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>';
        }
    });
    
    // 7. 为内容块添加入场动画
    const contentBlocks = document.querySelectorAll('section > .container > *:not(.features-grid):not(.steps):not(.pricing-cards)');
    
    const contentObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in-up');
                contentObserver.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.2,
        rootMargin: '0px 0px -100px 0px'
    });
    
    contentBlocks.forEach(block => {
        contentObserver.observe(block);
    });
}); 