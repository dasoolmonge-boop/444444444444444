// Модуль корзины
const cart = {
    items: [],

    // Добавить товар
    addItem(cake) {
        const existingItem = this.items.find(item => item.id === cake.id);

        if (existingItem) {
            existingItem.quantity += 1;
        } else {
            this.items.push({
                ...cake,
                quantity: 1
            });
        }

        this.updateBadge();
        this.render();
        this.saveToStorage();

        showToast(`${cake.name} добавлен в корзину`, 'success');
    },

    // Удалить товар
    removeItem(cakeId) {
        const index = this.items.findIndex(item => item.id === cakeId);
        if (index !== -1) {
            const cake = this.items[index];
            this.items.splice(index, 1);
            showToast(`${cake.name} удален из корзины`, 'warning');
        }

        this.updateBadge();
        this.render();
        this.saveToStorage();
    },

    // Обновить количество
    updateQuantity(cakeId, quantity) {
        const item = this.items.find(item => item.id === cakeId);
        if (item) {
            if (quantity <= 0) {
                this.removeItem(cakeId);
            } else {
                item.quantity = quantity;
            }
        }

        this.updateBadge();
        this.render();
        this.saveToStorage();
    },

    // Получить общую сумму
    getTotalPrice() {
        return this.items.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    },

    // Обновить счетчик на иконке
    updateBadge() {
        const badge = document.getElementById('cartBadge');
        const count = this.items.reduce((sum, item) => sum + item.quantity, 0);
        badge.textContent = count;
        badge.style.display = count > 0 ? 'flex' : 'none';
    },

    // Отрисовать корзину
    render() {
        const cartItems = document.getElementById('cartItems');
        const totalPrice = this.getTotalPrice();

        if (this.items.length === 0) {
            cartItems.innerHTML = `
                <div class="empty-cart">
                    <i class="fas fa-shopping-cart" style="font-size: 48px; opacity: 0.3;"></i>
                    <p style="margin-top: 16px; color: var(--tg-hint);">Корзина пуста</p>
                    <p style="margin-top: 8px; font-size: 14px; color: var(--tg-hint);">Добавьте торты из каталога</p>
                </div>
            `;
        } else {
            cartItems.innerHTML = this.items.map(item => `
                <div class="cart-item" data-id="${item.id}">
                    <img src="${item.photo}" alt="${item.name}" class="cart-item-image"
                         onerror="this.src='https://via.placeholder.com/60?text=Торт'">
                    <div class="cart-item-info">
                        <div class="cart-item-name">${item.name}</div>
                        <div class="cart-item-price">${item.price} ₽ × ${item.quantity}</div>
                    </div>
                    <button class="remove-item" onclick="cart.removeItem(${item.id})">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            `).join('');
        }

        document.getElementById('cartTotalPrice').textContent = `${totalPrice} ₽`;

        // Обновляем MainButton Telegram
        if (this.items.length > 0) {
            tg.MainButton.setText(`ОФОРМИТЬ ЗАКАЗ (${totalPrice} ₽)`);
            tg.MainButton.show();
            tg.MainButton.onClick(() => openCheckoutModal());
        } else {
            tg.MainButton.hide();
        }
    },

    // Очистить корзину
    clear() {
        this.items = [];
        this.updateBadge();
        this.render();
        this.saveToStorage();
    },

    // Сохранить в localStorage
    saveToStorage() {
        localStorage.setItem('cart', JSON.stringify(this.items));
    },

    // Загрузить из localStorage
    loadFromStorage() {
        const saved = localStorage.getItem('cart');
        if (saved) {
            try {
                this.items = JSON.parse(saved);
                this.updateBadge();
                this.render();
            } catch (e) {
                console.error('Ошибка загрузки корзины:', e);
                this.items = [];
            }
        }
    }
};

// Инициализация корзины
cart.loadFromStorage();

// Обработка отправки формы заказа
document.getElementById('orderForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const name = document.getElementById('name').value.trim();
    const phone = document.getElementById('phone').value.trim();
    const address = document.getElementById('address').value.trim();
    const deliveryDate = document.getElementById('deliveryDate').value.trim();
    const deliveryTime = document.getElementById('deliveryTime').value.trim();
    const wish = document.getElementById('wish').value.trim();

    let isValid = true;

    if (name.length < 2) {
        showToast('Введите корректное имя', 'error');
        isValid = false;
    }

    if (!validatePhone(phone)) {
        showToast('Введите корректный номер телефона', 'error');
        isValid = false;
    }

    if (address.length < 5) {
        showToast('Введите корректный адрес', 'error');
        isValid = false;
    }

    if (!deliveryDate || !deliveryTime) {
        showToast('Заполните дату и время доставки', 'error');
        isValid = false;
    }

    if (!isValid) return;

    const submitBtn = e.target.querySelector('.submit-order');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Отправка...';

    const orderData = {
        name,
        phone,
        address,
        deliveryDate,
        deliveryTime,
        wish: wish || 'Без пожеланий',
        cart: cart.items,
        totalPrice: cart.getTotalPrice(),
        userId: user.id || 0,
        username: user.username || ''
    };

    try {
        const response = await fetch('/api/send-order', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(orderData)
        });

        const result = await response.json();

        if (result.success) {
            showToast('✅ Заказ успешно оформлен!', 'success');
            cart.clear();
            document.getElementById('checkoutModal').classList.remove('open');
            e.target.reset();

            if (tg.HapticFeedback) {
                tg.HapticFeedback.notificationOccurred('success');
            }

            tg.MainButton.setText('ЗАКРЫТЬ');
            tg.MainButton.onClick(() => tg.close());
            tg.MainButton.show();
        } else {
            throw new Error('Ошибка при отправке');
        }
    } catch (error) {
        console.error('Ошибка:', error);
        showToast('❌ Ошибка при оформлении заказа', 'error');

        if (tg.HapticFeedback) {
            tg.HapticFeedback.notificationOccurred('error');
        }
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Подтвердить заказ';
    }
});

// Валидация телефона
function validatePhone(phone) {
    const pattern = /^[\+]?[(]?[0-9]{1,3}[)]?[-\s\.]?[(]?[0-9]{1,4}[)]?[-\s\.]?[0-9]{1,4}[-\s\.]?[0-9]{1,9}$/;
    return pattern.test(phone);
}

// Закрытие модального окна
document.getElementById('closeModal').addEventListener('click', () => {
    document.getElementById('checkoutModal').classList.remove('open');
});

document.getElementById('checkoutModal').addEventListener('click', (e) => {
    if (e.target === document.getElementById('checkoutModal')) {
        e.target.classList.remove('open');
    }
});

// Автоматическое форматирование телефона
document.getElementById('phone').addEventListener('input', (e) => {
    let value = e.target.value.replace(/\D/g, '');
    if (value.length > 0) {
        if (value.startsWith('7')) {
            value = '+7 ' + value.substring(1, 4) + ' ' + value.substring(4, 7) + '-' + value.substring(7, 9) + '-' + value.substring(9, 11);
        } else if (value.startsWith('8')) {
            value = '8 ' + value.substring(1, 4) + ' ' + value.substring(4, 7) + '-' + value.substring(7, 9) + '-' + value.substring(9, 11);
        }
        e.target.value = value.trim();
    }
});