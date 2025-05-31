// 现代风格舆情监测网站 - JavaScript
document.addEventListener('DOMContentLoaded', () => {
  // 初始化导航栏滚动效果
  initNavbar();
  
  // 预加载团队成员图片
  preloadTeamImages();
  
  // 初始化团队成员数据
  initTeamMembers();
  
  // 初始化模态框
  initModal();
  
  // 初始化动画效果
  initAnimations();
  
  // 初始化打字机效果
  initTypewriter();
  
  // 初始化滚动动画效果
  initScrollAnimations();
  
  // 初始化进度条动画
  animateProgressBars();
});

// 导航栏滚动效果
function initNavbar() {
  const navbar = document.querySelector('.navbar');
  
  // 监听滚动事件
  window.addEventListener('scroll', function() {
    if (window.scrollY > 10) {
      navbar.classList.add('scrolled');
    } else {
      navbar.classList.remove('scrolled');
    }
  });
  
  // 移动端导航栏适配
  adjustNavbarHeight();
  window.addEventListener('resize', adjustNavbarHeight);
  
  // 平滑滚动到锚点
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
      if (this.getAttribute('href') === '#') return;
      
      e.preventDefault();
      const targetId = this.getAttribute('href');
      const targetElement = document.querySelector(targetId);
      
      if (targetElement) {
        const headerHeight = document.querySelector('.navbar').offsetHeight;
        const targetPosition = targetElement.getBoundingClientRect().top + window.pageYOffset - headerHeight;
        
        window.scrollTo({
          top: targetPosition,
          behavior: 'smooth'
        });
      }
    });
  });
}

// 根据屏幕宽度调整导航栏高度和主内容区域的padding
function adjustNavbarHeight() {
  const navbar = document.querySelector('.navbar');
  const hero = document.querySelector('.hero');
  
  if (window.innerWidth <= 768) {
    // 获取导航栏实际高度
    const navbarHeight = navbar.offsetHeight;
    
    // 更新hero区域的顶部padding，确保内容不被遮挡
    hero.style.paddingTop = `${navbarHeight + 20}px`;
    
    // 更新CSS变量
    document.documentElement.style.setProperty('--header-height', `${navbarHeight}px`);
  } else {
    // 重置为默认值
    hero.style.paddingTop = '';
    document.documentElement.style.setProperty('--header-height', '72px');
  }
}

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

// 预加载团队成员图片
function preloadTeamImages() {
  teamMembers.forEach(member => {
    const img = new Image();
    img.src = member.avatar;
    
    // 添加图片加载错误处理
    img.onerror = function() {
      console.warn(`预加载图片失败: ${member.avatar}`);
      
      // 尝试多个可能的备用路径
      const backupPaths = [
        `/tuandui/${member.name}.jpg`,
        `tuandui/${member.name}.jpg`,
        `./tuandui/${member.name}.jpg`,
        `../tuandui/${member.name}.jpg`,
        `../../tuandui/${member.name}.jpg`,
        `/static/tuandui/${member.name}.jpg`
      ];
      
      console.log(`尝试备用路径...`);
      
      // 递归尝试加载备用路径
      tryNextPath(backupPaths, 0, member);
    };
  });
}

// 递归尝试加载多个备用路径
function tryNextPath(paths, index, member) {
  if (index >= paths.length) {
    console.warn(`所有备用路径都失败，将使用占位图`);
    return;
  }
  
  const currentPath = paths[index];
  console.log(`尝试路径: ${currentPath}`);
  
  const backupImg = new Image();
  backupImg.src = currentPath;
  
  backupImg.onload = function() {
    console.log(`成功加载: ${currentPath}`);
    member.avatar = currentPath;
  };
  
  backupImg.onerror = function() {
    console.warn(`路径失败: ${currentPath}`);
    // 尝试下一个路径
    tryNextPath(paths, index + 1, member);
  };
}

// 初始化团队成员卡片
function initTeamMembers() {
  // 获取所有团队成员卡片
  const memberCards = document.querySelectorAll('.member-card');
  
  // 确保卡片数量与团队成员匹配
  if (memberCards.length !== teamMembers.length) {
    console.warn(`卡片数量(${memberCards.length})与团队成员数量(${teamMembers.length})不匹配`);
  }

  // 初始化所有卡片
  memberCards.forEach((card, index) => {
    // 直接使用对应索引的团队成员，不再随机
    if (index < teamMembers.length) {
      const member = teamMembers[index];
      initializeCardWithMember(card, member, index);
    }
  });
  
  // 模态框关闭功能
  const closeBtn = document.querySelector('.close-modal');
  const modalOverlay = document.querySelector('.modal-overlay');
  
  closeBtn.addEventListener('click', closeModal);
  modalOverlay.addEventListener('click', closeModal);
  
  // 初始化图片错误处理
  initImageErrorHandling();
}

function initializeCardWithMember(card, member, memberId) {
  // 更新卡片内容
  const backSide = card.querySelector('.card-back');
  
  // 使用tuandui文件夹中的真实照片
  const avatarUrl = member.avatar;
  
  backSide.innerHTML = `
     <div class="member-avatar">
       <img src="${avatarUrl}" alt="${member.name}" data-member-id="${memberId}">
     </div>
     <div class="member-info">
       <h3 class="member-name">${member.name}</h3>
       <div class="member-role">${member.role}</div>
     </div>
     <p class="member-desc">${member.desc}</p>
  `;
  
  // 添加卡片点击翻转效果
  card.addEventListener('click', function() {
    if (!this.classList.contains('flipped')) {
      // 第一次点击：翻转卡片
      this.classList.add('flipped');
    } else {
      // 第二次点击：显示模态框
      showMemberModal(this);
    }
  });
}

// 生成随机渐变色背景
function getRandomColor(id) {
  const colors = [
    'linear-gradient(135deg, #3B82F6, #2563EB)',
    'linear-gradient(135deg, #8B5CF6, #7C3AED)',
    'linear-gradient(135deg, #EC4899, #DB2777)',
    'linear-gradient(135deg, #10B981, #059669)',
    'linear-gradient(135deg, #F59E0B, #D97706)',
    'linear-gradient(135deg, #6366F1, #4F46E5)'
  ];
  
  return colors[id % colors.length];
}

// 初始化模态框
function initModal() {
  const modal = document.querySelector('.member-modal');
  const closeBtn = modal.querySelector('.close-modal');
  const overlay = modal.querySelector('.modal-overlay');
  
  // 关闭模态框
  closeBtn.addEventListener('click', () => closeModal());
  
  // 点击模态框外部关闭
  overlay.addEventListener('click', () => closeModal());
  
  // ESC 关闭模态框
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && modal.classList.contains('active')) {
      closeModal();
    }
  });
}

// 显示成员模态框
function showMemberModal(card) {
  const modal = document.querySelector('.member-modal');
  const modalBody = modal.querySelector('.modal-body');
  const memberId = card.querySelector('.member-avatar img').dataset.memberId;
  const member = teamMembers[memberId];
  
  // 使用tuandui文件夹中的真实照片
  const avatarUrl = member.avatar;
  
  const tags = extractTags(member);
  
  modalBody.innerHTML = `
    <div class="modal-bg"></div>
    <div class="modal-left-decor"></div>
    <div class="modal-right-decor"></div>
    
    <div class="modal-avatar">
      <img src="${avatarUrl}" alt="${member.name}">
    </div>
    
    <h2 class="modal-name">${member.name}</h2>
    
    <div class="modal-tags">
      ${tags.map(tag => `<span class="modal-tag">${tag}</span>`).join('')}
    </div>
    
    <p class="modal-desc">${member.desc}</p>
  `;
  
  modal.classList.add('active');
  
  // 添加标签动画效果
  setTimeout(() => {
    modal.querySelectorAll('.modal-tag').forEach((tag, index) => {
      setTimeout(() => {
        tag.classList.add('tag-animate');
      }, index * 100);
    });
  }, 300);
  
  // 阻止页面滚动
  document.body.style.overflow = 'hidden';
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
    tags.push('AI降临派', '技术负责人', '数码发烧友', '技术乐观主义');
  } else if (member.name === '陈俊松') {
    tags.push('热爱生活', '摄影', '运动爱好者', '志愿活动');
  }
  
  return tags;
}

// 关闭模态框
function closeModal() {
  const modal = document.querySelector('.member-modal');
  modal.classList.remove('active');
  
  // 恢复页面滚动
  document.body.style.overflow = '';
}

// 初始化动画效果
function initAnimations() {
  // 界面预览动画
  animateInterface();
  
  // 创建视差滚动效果
  createParallaxEffect();
  
  // 添加渐进式显示动画
  addScrollReveal();
}

// 界面预览元素动画
function animateInterface() {
  // 每2秒更新一次进度条动画
  setInterval(() => {
    document.querySelectorAll('.progress').forEach(progress => {
      const newWidth = Math.floor(Math.random() * 30) + 60; // 60-90%范围内随机
      progress.style.width = `${newWidth}%`;
    });
  }, 2000);
}

// 创建视差滚动效果
function createParallaxEffect() {
  window.addEventListener('scroll', () => {
    const scrollPosition = window.scrollY;
    
    // 背景特效
    const heroDot = document.querySelector('.hero-dot');
    if (heroDot) {
      heroDot.style.transform = `translate(${scrollPosition * 0.05}px, ${scrollPosition * 0.02}px)`;
    }
  });
}

// 添加渐进式显示动画
function addScrollReveal() {
  const elements = document.querySelectorAll('.feature-card, .innovation-card, .member-card');
  
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('revealed');
        observer.unobserve(entry.target);
      }
    });
  }, {
    threshold: 0.1
  });
  
  elements.forEach(element => {
    element.classList.add('reveal');
    observer.observe(element);
  });
  
  // 添加CSS
  const style = document.createElement('style');
  style.textContent = `
    .reveal {
      opacity: 0;
      transform: translateY(30px);
      transition: opacity 0.6s ease, transform 0.6s ease;
    }
    
    .revealed {
      opacity: 1;
      transform: translateY(0);
    }
  `;
  
  document.head.appendChild(style);
}

// 初始化打字机效果
function initTypewriter() {
  // 应用打字机效果到首页标题
  const heroTitle = document.querySelector('.hero h1');
  if (heroTitle) {
    const originalText = heroTitle.innerHTML;
    const highlight = heroTitle.querySelector('.highlight');
    const highlightText = highlight ? highlight.textContent : '';
    
    // 清空原内容
    heroTitle.innerHTML = '';
    
    // 分解文本
    // 将originalText中的<span class="highlight">舆情分析</span>进行特殊处理
    const plainText = originalText.replace(/<span class="highlight">.*?<\/span>/, 'HIGHLIGHT_PLACEHOLDER');
    const parts = plainText.split('HIGHLIGHT_PLACEHOLDER');
    
    // 第一部分（高亮前的文本）
    const part1 = parts[0];
    // 第二部分（高亮后的文本）
    const part2 = parts[1] || '';
    
    let textIndex = 0;
    const part1Chars = part1.split('');
    const part2Chars = part2.split('');
    
    function typeNextChar() {
      if (textIndex < part1Chars.length) {
        // 还在打第一部分
        heroTitle.innerHTML += part1Chars[textIndex];
        textIndex++;
        setTimeout(typeNextChar, 80);
      } else if (textIndex === part1Chars.length) {
        // 打高亮部分
        heroTitle.innerHTML += `<span class="highlight">${highlightText}</span>`;
        textIndex++;
        setTimeout(typeNextChar, 150); // 高亮部分稍微停顿长一些
      } else if (textIndex - part1Chars.length - 1 < part2Chars.length) {
        // 打第二部分
        const idx = textIndex - part1Chars.length - 1;
        heroTitle.innerHTML += part2Chars[idx];
        textIndex++;
        setTimeout(typeNextChar, 80);
      } else {
        // 全部打完了，添加光标闪烁
        const cursor = document.createElement('span');
        cursor.className = 'typing-cursor';
        cursor.textContent = '|';
        heroTitle.appendChild(cursor);
        
        // 2秒后移除光标
        setTimeout(() => {
          cursor.style.opacity = '0';
        }, 2000);
      }
    }
    
    // 开始打字效果
    typeNextChar();
    
    // 添加打字机光标样式
    const style = document.createElement('style');
    style.textContent = `
      .typing-cursor {
        color: var(--secondary);
        font-weight: 400;
        animation: blink 1s infinite;
      }
      
      @keyframes blink {
        0%, 100% { opacity: 1; }
        50% { opacity: 0; }
      }
    `;
    document.head.appendChild(style);
  }
  
  // 添加文本渐显效果到其他元素
  const fadeElements = document.querySelectorAll('.section-header h2');
  fadeElements.forEach(element => {
    element.style.opacity = '0';
    element.style.transform = 'translateY(10px)';
    element.style.transition = 'opacity 0.8s, transform 0.8s';
    
    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          setTimeout(() => {
            element.style.opacity = '1';
            element.style.transform = 'translateY(0)';
          }, 300);
          observer.unobserve(element);
        }
      });
    }, { threshold: 0.5 });
    
    observer.observe(element);
  });
}

// 初始化滚动动画
function initScrollAnimations() {
  // 将所有需要动画的元素添加reveal类
  const featureCards = document.querySelectorAll('.feature-card');
  const innovationCards = document.querySelectorAll('.innovation-card');
  const memberCards = document.querySelectorAll('.member-card');
  const sectionHeaders = document.querySelectorAll('.section-header');
  
  // 添加reveal类
  [...featureCards, ...innovationCards, ...memberCards, ...sectionHeaders].forEach(el => {
    el.classList.add('reveal');
  });
  
  // 初始化IntersectionObserver
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('revealed');
        // 一旦元素显示，停止观察
        observer.unobserve(entry.target);
      }
    });
  }, {
    threshold: 0.1, // 元素10%可见时触发
    rootMargin: '0px 0px -50px 0px' // 提前50px触发
  });
  
  // 开始观察所有reveal元素
  document.querySelectorAll('.reveal').forEach(el => {
    observer.observe(el);
  });
}

// 初始化进度条动画
function animateProgressBars() {
  const progressBars = document.querySelectorAll('.progress');
  
  // 随机化进度条进度
  progressBars.forEach(bar => {
    const randomProgress = Math.floor(Math.random() * 30) + 70; // 70%-100%
    setTimeout(() => {
      bar.style.width = `${randomProgress}%`;
    }, 1000);
  });
  
  // 周期性动画
  setInterval(() => {
    progressBars.forEach(bar => {
      const currentWidth = parseInt(bar.style.width, 10) || 75;
      const newWidth = currentWidth < 30 ? 
        currentWidth + Math.floor(Math.random() * 30) + 40 : 
        Math.max(currentWidth - Math.floor(Math.random() * 20), 60);
      
      bar.style.width = `${newWidth}%`;
    });
  }, 4000);
}

// 处理图片加载错误
function initImageErrorHandling() {
  // 为所有团队成员图片添加错误处理
  document.querySelectorAll('.member-avatar img').forEach(img => {
    img.addEventListener('error', function(e) {
      console.warn(`图片加载失败: ${this.src}`);
      
      // 替换为默认头像
      const name = this.alt || '用户';
      const firstChar = name.charAt(0);
      
      // 生成随机颜色作为背景
      const colors = ['#3B82F6', '#8B5CF6', '#EC4899', '#10B981', '#F59E0B', '#6366F1'];
      const randomColor = colors[Math.floor(Math.random() * colors.length)];
      
      // 创建SVG数据URL
      const svgContent = `
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
          <rect width="100" height="100" fill="${randomColor}"/>
          <text x="50" y="50" font-family="Arial" font-size="40" fill="white" text-anchor="middle" dominant-baseline="central">${firstChar}</text>
        </svg>
      `;
      
      const encodedSVG = encodeURIComponent(svgContent);
      this.src = `data:image/svg+xml;charset=utf-8,${encodedSVG}`;
    });
  });
  
  // 为模态框中的图片添加错误处理
  const modalObserver = new MutationObserver(mutations => {
    mutations.forEach(mutation => {
      if (mutation.type === 'childList') {
        const modalImg = document.querySelector('.modal-avatar img');
        if (modalImg && !modalImg.dataset.errorHandlerAttached) {
          modalImg.addEventListener('error', function(e) {
            console.warn(`模态框图片加载失败: ${this.src}`);
            
            // 替换为默认头像
            const name = this.alt || '用户';
            const firstChar = name.charAt(0);
            
            // 生成随机颜色作为背景
            const colors = ['#3B82F6', '#8B5CF6', '#EC4899', '#10B981', '#F59E0B', '#6366F1'];
            const randomColor = colors[Math.floor(Math.random() * colors.length)];
            
            // 创建SVG数据URL
            const svgContent = `
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
                <rect width="100" height="100" fill="${randomColor}"/>
                <text x="50" y="50" font-family="Arial" font-size="40" fill="white" text-anchor="middle" dominant-baseline="central">${firstChar}</text>
              </svg>
            `;
            
            const encodedSVG = encodeURIComponent(svgContent);
            this.src = `data:image/svg+xml;charset=utf-8,${encodedSVG}`;
          });
          
          modalImg.dataset.errorHandlerAttached = 'true';
        }
      }
    });
  });
  
  modalObserver.observe(document.querySelector('.member-modal'), { 
    childList: true, 
    subtree: true 
  });
} 