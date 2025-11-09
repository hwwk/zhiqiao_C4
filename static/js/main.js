/**
 * AI News 前端交互脚本
 */

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    initCategoryFilter();
});

/**
 * 初始化分类筛选功能
 */
function initCategoryFilter() {
    const categoryButtons = document.querySelectorAll('.category-item');
    const cards = document.querySelectorAll('.card');
    const currentCount = document.getElementById('current-count');

    categoryButtons.forEach(button => {
        button.addEventListener('click', function() {
            const category = this.dataset.category;

            // 更新按钮激活状态
            categoryButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');

            // 筛选卡片
            let visibleCount = 0;

            cards.forEach(card => {
                const cardCategory = card.dataset.category;

                if (category === 'all' || cardCategory === category) {
                    card.classList.remove('hidden');
                    visibleCount++;
                } else {
                    card.classList.add('hidden');
                }
            });

            // 更新显示的数量
            if (currentCount) {
                currentCount.textContent = visibleCount;
            }

            // 添加过渡动画
            animateCards();
        });
    });
}

/**
 * 卡片动画效果
 */
function animateCards() {
    const visibleCards = document.querySelectorAll('.card:not(.hidden)');

    visibleCards.forEach((card, index) => {
        card.style.animation = 'none';
        // 强制重绘
        void card.offsetWidth;
        card.style.animation = `fadeIn 0.5s ease-out ${index * 0.05}s`;
    });
}

/**
 * 图片加载错误处理
 */
document.addEventListener('error', function(e) {
    if (e.target.tagName === 'IMG') {
        // 图片加载失败时的处理
        const card = e.target.closest('.card');
        if (card) {
            const imageWrapper = e.target.closest('.card-image-wrapper');
            if (imageWrapper) {
                // 移除图片包装器
                imageWrapper.remove();

                // 获取卡片信息
                const title = card.querySelector('.card-title')?.textContent || '';
                const category = card.dataset.category || 'Video';

                // 创建渐变背景替代
                const gradient = document.createElement('div');
                gradient.className = 'card-gradient';
                gradient.setAttribute('data-category', category);

                const centeredTitle = document.createElement('h3');
                centeredTitle.className = 'card-title-centered';
                centeredTitle.textContent = title;

                gradient.appendChild(centeredTitle);

                // 插入到卡片开头
                const cardLink = card.querySelector('.card-link');
                if (cardLink) {
                    cardLink.insertBefore(gradient, cardLink.firstChild);
                }

                // 移除原来的标题（如果存在）
                const originalTitle = card.querySelector('.card-title');
                if (originalTitle) {
                    originalTitle.remove();
                }
            }
        }
    }
}, true);

/**
 * 平滑滚动到顶部
 */
function scrollToTop() {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}

/**
 * 监听滚动，显示返回顶部按钮（可选功能）
 */
let scrollTimeout;
window.addEventListener('scroll', function() {
    clearTimeout(scrollTimeout);

    scrollTimeout = setTimeout(function() {
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;

        // 可以在这里添加返回顶部按钮的显示/隐藏逻辑
        // if (scrollTop > 300) {
        //     showBackToTopButton();
        // } else {
        //     hideBackToTopButton();
        // }
    }, 100);
});

/**
 * 键盘快捷键支持
 */
document.addEventListener('keydown', function(e) {
    // 按数字键 1-4 切换分类
    if (e.key >= '1' && e.key <= '4') {
        const index = parseInt(e.key) - 1;
        const buttons = document.querySelectorAll('.category-item');
        if (buttons[index]) {
            buttons[index].click();
        }
    }

    // ESC 键重置到全部分类
    if (e.key === 'Escape') {
        const allButton = document.querySelector('.category-item[data-category="all"]');
        if (allButton) {
            allButton.click();
        }
    }
});

/**
 * 打印调试信息
 */
console.log('AI News 页面加载完成');
console.log('功能：分类筛选、卡片动画、图片错误处理、键盘快捷键');
console.log('快捷键：数字 1-4 切换分类，ESC 返回全部');
