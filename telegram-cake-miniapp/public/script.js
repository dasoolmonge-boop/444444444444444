// Инициализация Telegram Mini App
const tg = window.Telegram.WebApp;

// Сообщаем Telegram, что приложение готово
tg.ready();

// Расширяем на весь экран
tg.expand();

// Настройка MainButton
tg.MainButton.setText('ЗАКАЗАТЬ');
tg.MainButton.setParams({
    color: '#50a8eb',
    text_color: '#ffffff'
});

// Глобальные переменные
let cakes = [];
let user = tg.initDataUnsafe.user || {};

// Загрузка данных тортов
async function loadCakes() {
    try {
        const response = await fetch('/api/cakes');
        const data = await response.json();
        cakes = data;
        renderCakes(cakes);
    } catch (error) {
        console.error('Ошибка загрузки тортов:', error);
        showToast('Ошибка загрузки меню', 'error');

        // Показываем заглушку
        const grid = document.getElementById('cakesGrid');
        grid.innerHTML = `
            <div class="empty-cart">
                <i class="fas fa-exclamation-circle" style="font-size: 48px; opacity: 0.3;"></i>
                <p style="margin-top: 16px;">Не удалось загрузить торты</p>
                <button class="category" onclick="loadCakes()" style="margin-top: 16px;">Повторить</button>
            </div>
        `;
    }
}

// Отрисовка тортов
function renderCakes(cakesArray) {
    const grid = document.getElementById('cakesGrid');
    grid.innerHTML = '';

    cakesArray.forEach(cake => {
        const card = document.createElement('div');
        card.className = 'cake-card';
        card.innerHTML = `
            <img src="${cake.photo}" alt="${cake.name}" class="cake-image"
                 onerror="this.src='https://via.placeholder.com/200?text=Торт'">
            <div class="cake-info">
                <div class="cake-name">${cake.name}</div>
                <div class="cake-weight">⚖️ ${cake.weight} кг</div>
                <div class="cake-description" style="font-size: 13px; color: var(--tg-hint); margin: 8px 0; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">
                    ${cake.description}
                </div>
                <div class="cake-price-row">
                    <span class="cake-price">${cake.price} ₽</span>
                    <button class="add-to-cart" data-id="${cake.id}">
                        <i class="fas fa-plus"></i>
                    </button>
                </div>
            </div>
        `;

        grid.appendChild(card);
    });

    // Добавляем обработчики для кнопок "Добавить в корзину"
    document.querySelectorAll('.add-to-cart').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const cakeId = parseInt(btn.dataset.id);
            const cake = cakes.find(c => c.id === cakeId);
            if (cake) {
                cart.addItem(cake);
                animateButton(btn);
            }
        });
    });
}

// Анимация кнопки при добавлении
function animateButton(btn) {
    btn.classList.add('added');
    btn.innerHTML = '<i class="fas fa-check"></i>';
    setTimeout(() => {
        btn.classList.remove('added');
        btn.innerHTML = '<i class="fas fa-plus"></i>';
    }, 1000);
}

// Показать уведомление
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <i class="fas ${type === 'success' ? 'fa-check-circle' :
                       type === 'error' ? 'fa-exclamation-circle' :
                       'fa-info-circle'}"></i>
        <span>${message}</span>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideUp 0.3s reverse';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Фильтрация тортов по категориям
function filterCakes(category) {
    if (category === 'all') {
        renderCakes(cakes);
    } else if (category === 'popular') {
        // Имитация популярных - первые 3
        const popular = cakes.slice(0, 3);
        renderCakes(popular);
    } else if (category === 'new') {
        // Имитация новинок - последние 2
        const newCakes = cakes.slice(-2);
        renderCakes(newCakes);
    }
}

// Инициализация при загрузке
document.addEventListener('DOMContentLoaded', () => {
    loadCakes();

    // Обработка открытия корзины
    document.getElementById('cartIcon').addEventListener('click', () => {
        document.getElementById('cartPanel').classList.add('open');
        cart.render();
    });

    // Закрытие корзины
    document.getElementById('closeCart').addEventListener('click', () => {
        document.getElementById('cartPanel').classList.remove('open');
    });

    // Обработка категорий
    document.querySelectorAll('.category').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.category').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            const category = btn.dataset.category;
            filterCakes(category);
        });
    });

    // Обработка кнопки оформления заказа
    document.getElementById('checkoutBtn').addEventListener('click', () => {
        if (cart.items.length === 0) {
            showToast('Корзина пуста', 'warning');
            return;
        }
        openCheckoutModal();
    });

    // Тактильная обратная связь
    if (tg.HapticFeedback) {
        document.querySelectorAll('button').forEach(btn => {
            btn.addEventListener('click', () => {
                tg.HapticFeedback.impactOccurred('light');
            });
        });
    }
});

// Функция открытия модального окна оформления заказа
function openCheckoutModal() {
    const modal = document.getElementById('checkoutModal');
    const summary = document.getElementById('orderSummary');

    let summaryHtml = '<div class="summary-items">';
    cart.items.forEach(item => {
        summaryHtml += `
            <div class="summary-item">
                <span>${item.name} × ${item.quantity}</span>
                <span>${item.price * item.quantity} ₽</span>
            </div>
        `;
    });
    summaryHtml += '</div>';
    summaryHtml += `
        <div class="summary-total">
            <span>Итого:</span>
            <span>${cart.getTotalPrice()} ₽</span>
        </div>
    `;

    summary.innerHTML = summaryHtml;

    if (user.first_name) {
        document.getElementById('name').value = user.first_name || '';
    }

    modal.classList.add('open');

    if (tg.HapticFeedback) {
        tg.HapticFeedback.impactOccurred('medium');
    }
}