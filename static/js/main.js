// SkillLink FX - Main JavaScript File

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Market data refresh
    function refreshMarketData() {
        const marketCards = document.querySelectorAll('.market-card');
        marketCards.forEach(card => {
            const priceElement = card.querySelector('.card-title');
            if (priceElement) {
                const currentPrice = parseFloat(priceElement.textContent.replace('$', ''));
                const change = (Math.random() - 0.5) * 0.02;
                const newPrice = currentPrice * (1 + change);
                priceElement.textContent = '$' + newPrice.toFixed(2);
                
                const changeBadge = card.querySelector('.badge');
                if (changeBadge) {
                    const changePercent = (change * 100).toFixed(2);
                    changeBadge.textContent = changePercent + '%';
                    changeBadge.className = change >= 0 ? 'badge bg-success' : 'badge bg-danger';
                }
            }
        });
    }

    // Auto-refresh market data every 10 seconds
    setInterval(refreshMarketData, 10000);

    // Live clock
    function updateClock() {
        const now = new Date();
        const clockElement = document.getElementById('live-clock');
        if (clockElement) {
            clockElement.textContent = now.toLocaleTimeString('en-US', {
                hour12: true,
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
        }
    }

    setInterval(updateClock, 1000);
    updateClock();

    // Chart color scheme
    const chartColors = {
        primary: 'rgba(52, 152, 219, 1)',
        success: 'rgba(46, 204, 113, 1)',
        danger: 'rgba(231, 76, 60, 1)',
        warning: 'rgba(243, 156, 18, 1)',
        info: 'rgba(26, 188, 156, 1)',
        light: 'rgba(236, 240, 241, 1)',
        dark: 'rgba(44, 62, 80, 1)'
    };

    // Theme switcher
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            const htmlElement = document.documentElement;
            const currentTheme = htmlElement.getAttribute('data-bs-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            
            htmlElement.setAttribute('data-bs-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            
            const icon = this.querySelector('i');
            icon.className = newTheme === 'dark' ? 'fas fa-moon' : 'fas fa-sun';
        });

        const savedTheme = localStorage.getItem('theme') || 'dark';
        document.documentElement.setAttribute('data-bs-theme', savedTheme);
        const icon = themeToggle.querySelector('i');
        icon.className = savedTheme === 'dark' ? 'fas fa-moon' : 'fas fa-sun';
    }

    // Market search
    const marketSearch = document.getElementById('marketSearch');
    if (marketSearch) {
        marketSearch.addEventListener('input', function(e) {
            const searchTerm = e.target.value.toLowerCase();
            const marketCards = document.querySelectorAll('.market-card');
            
            marketCards.forEach(card => {
                const symbol = card.querySelector('.card-title').textContent.toLowerCase();
                const name = card.querySelector('.text-muted').textContent.toLowerCase();
                
                if (symbol.includes(searchTerm) || name.includes(searchTerm)) {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            });
        });
    }

    // Signal filter
    const signalFilters = document.querySelectorAll('.signal-filter');
    signalFilters.forEach(filter => {
        filter.addEventListener('change', function() {
            document.getElementById('signalFilterForm').submit();
        });
    });

    // AJAX form handling
    document.querySelectorAll('.ajax-form').forEach(form => {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const submitBtn = this.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerHTML;
            
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
            submitBtn.disabled = true;
            
            try {
                const response = await fetch(this.action, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });
                
                const data = await response.json();
                
                if (data.success) {
                    if (data.redirect) {
                        window.location.href = data.redirect;
                    } else if (data.message) {
                        showNotification(data.message, 'success');
                        if (data.reset_form) {
                            this.reset();
                        }
                    }
                } else {
                    showNotification(data.error || 'An error occurred', 'danger');
                }
            } catch (error) {
                showNotification('Network error: ' + error.message, 'danger');
            } finally {
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
            }
        });
    });

    // Notification system
    function showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        notification.style.cssText = `
            top: 20px;
            right: 20px;
            z-index: 9999;
            min-width: 300px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        `;
        
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
    }

    // Price alert system
    function setupPriceAlerts() {
        const alertButtons = document.querySelectorAll('.set-price-alert');
        alertButtons.forEach(button => {
            button.addEventListener('click', function() {
                const symbol = this.dataset.symbol;
                const currentPrice = parseFloat(this.dataset.price);
                
                const alertPrice = prompt(`Set price alert for ${symbol}\nCurrent price: $${currentPrice}\n\nEnter alert price:`);
                
                if (alertPrice && !isNaN(alertPrice)) {
                    const price = parseFloat(alertPrice);
                    const direction = price > currentPrice ? 'above' : 'below';
                    
                    const alerts = JSON.parse(localStorage.getItem('priceAlerts') || '[]');
                    alerts.push({
                        symbol: symbol,
                        targetPrice: price,
                        direction: direction,
                        currentPrice: currentPrice,
                        timestamp: new Date().toISOString()
                    });
                    
                    localStorage.setItem('priceAlerts', JSON.stringify(alerts));
                    
                    showNotification(`Price alert set for ${symbol} at $${price}`, 'success');
                }
            });
        });
    }

    setupPriceAlerts();

    // Risk calculator
    const riskCalculator = document.getElementById('riskCalculator');
    if (riskCalculator) {
        const inputs = riskCalculator.querySelectorAll('input');
        const resultElement = document.getElementById('riskResult');
        
        function calculateRisk() {
            const balance = parseFloat(document.getElementById('accountBalance').value) || 0;
            const riskPercent = parseFloat(document.getElementById('riskPercent').value) || 2;
            const stopLoss = parseFloat(document.getElementById('stopLoss').value) || 0;
            const entryPrice = parseFloat(document.getElementById('entryPrice').value) || 0;
            
            if (balance > 0 && stopLoss > 0 && entryPrice > 0) {
                const riskAmount = balance * (riskPercent / 100);
                const riskPerUnit = Math.abs(entryPrice - stopLoss);
                const positionSize = riskAmount / riskPerUnit;
                
                resultElement.innerHTML = `
                    <h5>Risk Calculation Results:</h5>
                    <p>Risk Amount: $${riskAmount.toFixed(2)}</p>
                    <p>Position Size: ${positionSize.toFixed(4)} units</p>
                    <p>Total Position Value: $${(positionSize * entryPrice).toFixed(2)}</p>
                `;
            }
        }
        
        inputs.forEach(input => {
            input.addEventListener('input', calculateRisk);
        });
        
        calculateRisk();
    }

    // Initialize TradingView widgets
    function initializeTradingView() {
        const tradingViewElements = document.querySelectorAll('.tradingview-widget-container');
        
        tradingViewElements.forEach(element => {
            const symbol = element.dataset.symbol || 'BTCUSD';
            const interval = element.dataset.interval || '60';
            
            if (typeof TradingView !== 'undefined') {
                new TradingView.widget({
                    "container_id": element.id,
                    "width": "100%",
                    "height": "400",
                    "symbol": symbol,
                    "interval": interval,
                    "timezone": "exchange",
                    "theme": "dark",
                    "style": "1",
                    "locale": "en",
                    "toolbar_bg": "#0f0f23",
                    "enable_publishing": false,
                    "hide_side_toolbar": false,
                    "allow_symbol_change": true,
                    "details": true,
                    "calendar": false,
                    "studies": ["Volume@tv-basicstudies"],
                    "show_popup_button": true,
                    "popup_width": "1000",
                    "popup_height": "650"
                });
            }
        });
    }

    if (typeof TradingView !== 'undefined') {
        initializeTradingView();
    }

    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href !== '#') {
                e.preventDefault();
                const target = document.querySelector(href);
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });
    });

    // Copy to clipboard
    document.querySelectorAll('.copy-to-clipboard').forEach(button => {
        button.addEventListener('click', function() {
            const text = this.dataset.copy;
            navigator.clipboard.writeText(text).then(() => {
                const originalHTML = this.innerHTML;
                this.innerHTML = '<i class="fas fa-check"></i> Copied!';
                setTimeout(() => {
                    this.innerHTML = originalHTML;
                }, 2000);
            });
        });
    });
});